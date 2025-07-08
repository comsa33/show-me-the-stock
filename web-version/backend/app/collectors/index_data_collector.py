"""
Market Index Data Collector
주요 시장 지수 데이터 수집기
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
import yfinance as yf
from pykrx import stock
from ..database.mongodb_client import get_mongodb_client

logger = logging.getLogger(__name__)


class IndexDataCollector:
    """시장 지수 데이터 수집기"""
    
    def __init__(self):
        self.db = get_mongodb_client()
        
        # 한국 지수 매핑
        self.kr_indices = {
            'KOSPI': '1001',
            'KOSDAQ': '2001',
            'KOSPI200': '1028',
            'KRX100': '1035'
        }
        
        # 미국 지수 매핑
        self.us_indices = {
            'S&P500': '^GSPC',
            'NASDAQ': '^IXIC',
            'DowJones': '^DJI',
            'Russell2000': '^RUT',
            'VIX': '^VIX'
        }
    
    def collect_korean_indices(self, start_date: str = None, end_date: str = None):
        """한국 지수 데이터 수집"""
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            # 기본값: 1년 전
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        
        collected_count = 0
        error_count = 0
        
        logger.info(f"한국 지수 수집 시작: {start_date} ~ {end_date}")
        
        # 주말/공휴일 문제 회피를 위해 평일로 날짜 조정
        current_date = datetime.now()
        if current_date.weekday() >= 5:  # 토요일(5) 또는 일요일(6)
            # 직전 금요일로 조정
            days_back = current_date.weekday() - 4
            adjusted_date = current_date - timedelta(days=days_back)
            end_date = adjusted_date.strftime('%Y%m%d')
            logger.info(f"주말 감지, 종료일을 {end_date}로 조정")
        
        for name, code in self.kr_indices.items():
            try:
                # pykrx로 지수 데이터 가져오기
                data = None
                
                # 여러 방법 시도
                try:
                    # 방법 1: 표준 API
                    logger.info(f"{name} ({code}) 수집 시도 - 기간: {start_date} ~ {end_date}")
                    data = stock.get_index_ohlcv_by_date(start_date, end_date, code)
                    logger.info(f"{name} 표준 API 성공, 데이터 크기: {len(data) if data is not None else 0}")
                except Exception as e1:
                    logger.error(f"{name} 표준 API 실패: {type(e1).__name__}: {e1}")
                    logger.error(f"상세 에러 내용: {str(e1)}")
                    
                    try:
                        # 방법 2: 날짜 범위를 좁혀서 시도
                        temp_start = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
                        logger.info(f"{name} 날짜 조정 시도: {temp_start} ~ {end_date}")
                        data = stock.get_index_ohlcv_by_date(temp_start, end_date, code)
                        logger.info(f"{name} 날짜 조정 성공")
                    except Exception as e2:
                        logger.error(f"{name} 날짜 조정 실패: {type(e2).__name__}: {e2}")
                        
                        try:
                            # 방법 3: 단일 날짜로 시도
                            single_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
                            logger.info(f"{name} 단일 날짜 시도: {single_date}")
                            data = stock.get_index_ohlcv_by_date(single_date, single_date, code)
                            logger.info(f"{name} 단일 날짜 성공")
                        except Exception as e3:
                            logger.error(f"{name} 모든 방법 실패: {type(e3).__name__}: {e3}")
                            
                            # 추가 디버깅: 지수 목록 확인
                            try:
                                logger.info("지수 목록 확인 시도...")
                                index_list = stock.get_index_ticker_list()
                                logger.info(f"사용 가능한 지수 개수: {len(index_list) if index_list else 0}")
                                if index_list and code in index_list:
                                    logger.info(f"{code}는 지수 목록에 있음")
                                else:
                                    logger.error(f"{code}는 지수 목록에 없음")
                            except Exception as e4:
                                logger.error(f"지수 목록 조회 실패: {e4}")
                            
                            continue
                
                if data is None or data.empty:
                    logger.warning(f"{name} ({code}) 데이터 없음")
                    continue
                
                # 컬럼명 확인 및 매핑
                columns = data.columns.tolist()
                logger.debug(f"{name} 데이터 컬럼: {columns}")
                
                # 컬럼명 매핑 (pykrx 버전에 따라 다를 수 있음)
                col_mapping = {
                    '시가': ['시가', 'Open', '시가지수'],
                    '고가': ['고가', 'High', '고가지수'],
                    '저가': ['저가', 'Low', '저가지수'],
                    '종가': ['종가', 'Close', '종가지수', '지수'],
                    '거래량': ['거래량', 'Volume', '거래대금']
                }
                
                # 실제 컬럼명 찾기
                actual_cols = {}
                for target, candidates in col_mapping.items():
                    for candidate in candidates:
                        if candidate in columns:
                            actual_cols[target] = candidate
                            break
                
                if '종가' not in actual_cols:
                    logger.error(f"{name} 데이터에 종가 컬럼이 없음. 컬럼: {columns}")
                    continue
                
                # MongoDB에 저장
                for date_idx, row in data.iterrows():
                    date_str = date_idx.strftime('%Y-%m-%d')
                    
                    # 필수 값 가져오기
                    close_val = float(row[actual_cols['종가']])
                    
                    # 전일 대비 계산
                    if date_idx > data.index[0]:
                        prev_idx = data.index[data.index.get_loc(date_idx) - 1]
                        prev_close = float(data.loc[prev_idx, actual_cols['종가']])
                        change = close_val - prev_close
                        change_percent = (change / prev_close * 100) if prev_close > 0 else 0
                    else:
                        change = 0
                        change_percent = 0
                    
                    doc = {
                        '_id': f'{name}_{date_str}',
                        'code': code,
                        'name': name,
                        'market': 'KR',
                        'date': date_str,
                        'open': float(row[actual_cols.get('시가', actual_cols['종가'])]),
                        'high': float(row[actual_cols.get('고가', actual_cols['종가'])]),
                        'low': float(row[actual_cols.get('저가', actual_cols['종가'])]),
                        'close': close_val,
                        'volume': int(row[actual_cols['거래량']]) if '거래량' in actual_cols else 0,
                        'change': round(change, 2),
                        'change_percent': round(change_percent, 2),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    # Upsert (있으면 업데이트, 없으면 삽입)
                    self.db.db.market_indices.replace_one(
                        {'_id': doc['_id']},
                        doc,
                        upsert=True
                    )
                    collected_count += 1
                
                logger.info(f"{name} 지수 수집 완료: {len(data)}개 레코드")
                
            except Exception as e:
                logger.error(f"{name} ({code}) 수집 실패: {e}")
                error_count += 1
        
        return {
            'market': 'KR',
            'collected': collected_count,
            'errors': error_count,
            'indices': list(self.kr_indices.keys())
        }
    
    def collect_us_indices(self, start_date: str = None, end_date: str = None):
        """미국 지수 데이터 수집"""
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            # 기본값: 1년 전
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        collected_count = 0
        error_count = 0
        
        logger.info(f"미국 지수 수집 시작: {start_date} ~ {end_date}")
        
        for name, symbol in self.us_indices.items():
            try:
                # yfinance로 지수 데이터 가져오기
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date)
                
                if data.empty:
                    logger.warning(f"{name} ({symbol}) 데이터 없음")
                    continue
                
                # MongoDB에 저장
                for date_idx, row in data.iterrows():
                    date_str = date_idx.strftime('%Y-%m-%d')
                    
                    # 전일 대비 계산
                    if date_idx > data.index[0]:
                        prev_idx = data.index[data.index.get_loc(date_idx) - 1]
                        prev_close = float(data.loc[prev_idx, 'Close'])
                        change = float(row['Close']) - prev_close
                        change_percent = (change / prev_close * 100) if prev_close > 0 else 0
                    else:
                        change = 0
                        change_percent = 0
                    
                    doc = {
                        '_id': f'{symbol}_{date_str}',
                        'code': symbol,
                        'name': name,
                        'market': 'US',
                        'date': date_str,
                        'open': float(row['Open']),
                        'high': float(row['High']),
                        'low': float(row['Low']),
                        'close': float(row['Close']),
                        'volume': int(row['Volume']) if 'Volume' in row and not pd.isna(row['Volume']) else 0,
                        'change': round(change, 2),
                        'change_percent': round(change_percent, 2),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    # Upsert (있으면 업데이트, 없으면 삽입)
                    self.db.db.market_indices.replace_one(
                        {'_id': doc['_id']},
                        doc,
                        upsert=True
                    )
                    collected_count += 1
                
                logger.info(f"{name} 지수 수집 완료: {len(data)}개 레코드")
                
            except Exception as e:
                logger.error(f"{name} ({symbol}) 수집 실패: {e}")
                error_count += 1
        
        return {
            'market': 'US',
            'collected': collected_count,
            'errors': error_count,
            'indices': list(self.us_indices.keys())
        }
    
    def collect_all_indices(self, start_date: str = None, end_date: str = None):
        """모든 지수 데이터 수집"""
        results = {
            'korean': self.collect_korean_indices(start_date, end_date),
            'us': self.collect_us_indices(start_date, end_date),
            'total_collected': 0,
            'total_errors': 0
        }
        
        results['total_collected'] = results['korean']['collected'] + results['us']['collected']
        results['total_errors'] = results['korean']['errors'] + results['us']['errors']
        
        return results
    
    def collect_daily_indices(self):
        """오늘 지수 데이터만 수집 (스케줄러용)"""
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # 한국 지수는 YYYYMMDD 형식
        kr_today = datetime.now().strftime('%Y%m%d')
        kr_yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        
        results = {
            'korean': self.collect_korean_indices(kr_yesterday, kr_today),
            'us': self.collect_us_indices(yesterday, today)
        }
        
        return results


# 싱글톤 인스턴스
_collector = None

def get_index_collector():
    """IndexDataCollector 싱글톤 인스턴스 반환"""
    global _collector
    if _collector is None:
        _collector = IndexDataCollector()
    return _collector