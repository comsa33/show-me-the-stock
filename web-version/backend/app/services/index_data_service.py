"""
주요 지수 데이터 수집 서비스
한국 (pykrx) 및 미국 (yfinance) 주요 지수 실시간 데이터 제공
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yfinance as yf
from pykrx import stock

logger = logging.getLogger(__name__)


class IndexDataService:
    """주요 지수 데이터 서비스"""
    
    def __init__(self):
        self._cache = {}
        self._cache_duration = 300  # 5분 캐시
        
        # 지수 매핑
        self.kr_indices = {
            'KOSPI': '1001',
            'KOSDAQ': '2001',
            'KOSPI200': '1002',
            'KRX100': '1003'
        }
        
        self.us_indices = {
            'S&P500': '^GSPC',
            'NASDAQ': '^IXIC',
            'DowJones': '^DJI',
            'Russell2000': '^RUT',
            'VIX': '^VIX'
        }
    
    def _is_cache_valid(self, key: str) -> bool:
        """캐시 유효성 확인"""
        if key not in self._cache:
            return False
        cache_time = self._cache[key].get('timestamp', 0)
        return (datetime.now().timestamp() - cache_time) < self._cache_duration
    
    def get_korean_indices(self) -> List[Dict]:
        """한국 주요 지수 데이터 수집"""
        
        cache_key = 'kr_indices'
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]['data']
        
        try:
            indices_data = []
            today = datetime.now().strftime('%Y%m%d')
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
            
            for name, code in self.kr_indices.items():
                try:
                    # 1주일 데이터 가져오기 (최신 데이터 확보)
                    data = stock.get_index_ohlcv_by_date(week_ago, today, code)
                    
                    if not data.empty:
                        # 최신 데이터
                        current_value = float(data['종가'].iloc[-1])
                        current_open = float(data['시가'].iloc[-1])
                        
                        # 전일 대비 계산
                        if len(data) > 1:
                            prev_close = float(data['종가'].iloc[-2])
                        else:
                            prev_close = current_open
                        
                        change = current_value - prev_close
                        change_percent = (change / prev_close * 100) if prev_close > 0 else 0
                        
                        # 거래량 정보
                        volume = int(data['거래량'].iloc[-1]) if '거래량' in data.columns else 0
                        
                        index_info = {
                            'name': name,
                            'code': code,
                            'value': round(current_value, 2),
                            'change': round(change, 2),
                            'change_percent': round(change_percent, 2),
                            'volume': volume,
                            'market': 'KR',
                            'currency': 'KRW',
                            'timestamp': datetime.now().isoformat(),
                            'data_source': 'pykrx'
                        }
                        
                        indices_data.append(index_info)
                        logger.info(f"한국 지수 {name} 데이터 수집 성공: {current_value:,.2f}")
                        
                    else:
                        logger.warning(f"한국 지수 {name} ({code}) 데이터 없음")
                        
                except Exception as e:
                    logger.error(f"한국 지수 {name} ({code}) 수집 실패: {e}")
                    continue
            
            # 캐시 저장
            self._cache[cache_key] = {
                'data': indices_data,
                'timestamp': datetime.now().timestamp()
            }
            
            logger.info(f"한국 지수 {len(indices_data)}개 수집 완료")
            return indices_data
            
        except Exception as e:
            logger.error(f"한국 지수 데이터 수집 전체 실패: {e}")
            return self._generate_mock_kr_indices()
    
    def get_us_indices(self) -> List[Dict]:
        """미국 주요 지수 데이터 수집"""
        
        cache_key = 'us_indices'
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]['data']
        
        try:
            indices_data = []
            
            for name, symbol in self.us_indices.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='2d')  # 2일 데이터로 전일 대비 계산
                    
                    if not hist.empty:
                        current_value = float(hist['Close'].iloc[-1])
                        
                        # 전일 대비 계산
                        if len(hist) > 1:
                            prev_close = float(hist['Close'].iloc[-2])
                        else:
                            prev_close = float(hist['Open'].iloc[-1])
                        
                        change = current_value - prev_close
                        change_percent = (change / prev_close * 100) if prev_close > 0 else 0
                        
                        # 거래량
                        volume = int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0
                        
                        index_info = {
                            'name': name,
                            'code': symbol,
                            'value': round(current_value, 2),
                            'change': round(change, 2),
                            'change_percent': round(change_percent, 2),
                            'volume': volume,
                            'market': 'US',
                            'currency': 'USD',
                            'timestamp': datetime.now().isoformat(),
                            'data_source': 'yfinance'
                        }
                        
                        indices_data.append(index_info)
                        logger.info(f"미국 지수 {name} 데이터 수집 성공: {current_value:,.2f}")
                        
                    else:
                        logger.warning(f"미국 지수 {name} ({symbol}) 데이터 없음")
                        
                except Exception as e:
                    logger.error(f"미국 지수 {name} ({symbol}) 수집 실패: {e}")
                    continue
            
            # 캐시 저장
            self._cache[cache_key] = {
                'data': indices_data,
                'timestamp': datetime.now().timestamp()
            }
            
            logger.info(f"미국 지수 {len(indices_data)}개 수집 완료")
            return indices_data
            
        except Exception as e:
            logger.error(f"미국 지수 데이터 수집 전체 실패: {e}")
            return self._generate_mock_us_indices()
    
    def get_all_indices(self) -> Dict[str, List[Dict]]:
        """전체 지수 데이터 수집"""
        
        try:
            kr_indices = self.get_korean_indices()
            us_indices = self.get_us_indices()
            
            return {
                'korean_indices': kr_indices,
                'us_indices': us_indices,
                'total_count': len(kr_indices) + len(us_indices),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"전체 지수 데이터 수집 실패: {e}")
            return {
                'korean_indices': self._generate_mock_kr_indices(),
                'us_indices': self._generate_mock_us_indices(),
                'total_count': 4,
                'last_updated': datetime.now().isoformat()
            }
    
    def get_index_data(self, symbol: str, market: str = 'auto') -> Optional[Dict]:
        """개별 지수 데이터 조회"""
        
        try:
            if market.upper() == 'KR' or symbol in self.kr_indices.values():
                indices = self.get_korean_indices()
                for index in indices:
                    if index['code'] == symbol or index['name'] == symbol:
                        return index
            else:
                indices = self.get_us_indices()
                for index in indices:
                    if index['code'] == symbol or index['name'] == symbol:
                        return index
            
            return None
            
        except Exception as e:
            logger.error(f"지수 {symbol} 데이터 조회 실패: {e}")
            return None
    
    def _generate_mock_kr_indices(self) -> List[Dict]:
        """Mock 한국 지수 데이터"""
        
        mock_data = [
            {
                'name': 'KOSPI',
                'code': '1001',
                'value': 3089.65,
                'change': 15.32,
                'change_percent': 0.50,
                'volume': 750000000,
                'market': 'KR',
                'currency': 'KRW',
                'timestamp': datetime.now().isoformat(),
                'data_source': 'mock'
            },
            {
                'name': 'KOSDAQ',
                'code': '2001', 
                'value': 783.67,
                'change': -5.12,
                'change_percent': -0.65,
                'volume': 980000000,
                'market': 'KR',
                'currency': 'KRW',
                'timestamp': datetime.now().isoformat(),
                'data_source': 'mock'
            }
        ]
        
        return mock_data
    
    def _generate_mock_us_indices(self) -> List[Dict]:
        """Mock 미국 지수 데이터"""
        
        mock_data = [
            {
                'name': 'S&P500',
                'code': '^GSPC',
                'value': 6198.01,
                'change': 10.45,
                'change_percent': 0.17,
                'volume': 3200000000,
                'market': 'US',
                'currency': 'USD',
                'timestamp': datetime.now().isoformat(),
                'data_source': 'mock'
            },
            {
                'name': 'NASDAQ',
                'code': '^IXIC',
                'value': 20202.89,
                'change': -87.52,
                'change_percent': -0.43,
                'volume': 4100000000,
                'market': 'US',
                'currency': 'USD',
                'timestamp': datetime.now().isoformat(),
                'data_source': 'mock'
            }
        ]
        
        return mock_data


# 전역 서비스 인스턴스
index_service = IndexDataService()