"""
Stock Data Collector V2 - Provider 기반 구현
pykrx 의존성을 제거하고 StockDataProvider 인터페이스 사용
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from ..database.mongodb_client import get_mongodb_client
from ..data.stock_data_provider_factory import StockDataProviderFactory
from ..services.real_financial_data import RealFinancialDataService

logger = logging.getLogger(__name__)


class StockDataCollectorV2:
    """Provider 기반 주식 데이터 수집기"""
    
    def __init__(self):
        self.db = get_mongodb_client()
        # 환경변수나 설정에 따라 provider 선택
        self.kr_provider = StockDataProviderFactory.get_provider()
        self.financial_service = RealFinancialDataService()
        logger.info(f"Initialized with provider: {self.kr_provider.name}")
        
    def collect_kr_stock_list(self) -> Dict[str, Any]:
        """한국 주식 목록 수집"""
        logger.info("한국 주식 목록 수집 시작")
        
        try:
            # Provider를 통해 주식 목록 가져오기
            stocks = self.kr_provider.get_stock_list("KR")
            
            if not stocks:
                logger.warning("주식 목록이 비어있음")
                return {'status': 'failed', 'message': '주식 목록을 가져올 수 없습니다'}
            
            # MongoDB에 저장
            saved_count = 0
            for stock in stocks:
                try:
                    # 기존 형식 유지
                    doc = {
                        '_id': stock['symbol'],
                        'symbol': stock['symbol'],
                        'name': stock['name'],
                        'market': 'KR',
                        'listing_date': None,  # Provider에서 제공하지 않음
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    self.db.db.stock_list.replace_one(
                        {'_id': doc['_id']},
                        doc,
                        upsert=True
                    )
                    saved_count += 1
                    
                except Exception as e:
                    logger.error(f"종목 {stock['symbol']} 저장 실패: {e}")
            
            logger.info(f"한국 주식 {saved_count}개 저장 완료")
            return {
                'status': 'success',
                'total': len(stocks),
                'saved': saved_count
            }
            
        except Exception as e:
            logger.error(f"한국 주식 목록 수집 실패: {e}")
            return {'status': 'failed', 'message': str(e)}
    
    def collect_kr_daily_prices(self, date: Optional[str] = None) -> Dict[str, Any]:
        """한국 주식 일일 가격 수집"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"한국 주식 일일 가격 수집 시작: {date}")
        
        try:
            # MongoDB에서 한국 주식 목록 가져오기
            kr_stocks = list(self.db.db.stock_list.find({'market': 'KR'}))
            
            if not kr_stocks:
                logger.warning("수집할 한국 주식이 없음")
                return {'status': 'failed', 'message': '주식 목록이 비어있습니다'}
            
            success_count = 0
            error_count = 0
            
            # 배치 처리
            batch_size = 100
            for i in range(0, len(kr_stocks), batch_size):
                batch = kr_stocks[i:i + batch_size]
                
                for stock in batch:
                    try:
                        symbol = stock['symbol']
                        
                        # Provider를 통해 실시간 가격 가져오기
                        price_data = self.kr_provider.get_stock_price_realtime(symbol)
                        
                        if not price_data:
                            # 실시간 실패시 일일 데이터 시도
                            df = self.kr_provider.get_stock_price(
                                symbol, date, date
                            )
                            if df.empty:
                                continue
                            
                            # DataFrame에서 데이터 추출
                            row = df.iloc[0]
                            price_data = {
                                'symbol': symbol,
                                'price': float(row.get('close', 0)),
                                'change': 0,  # 계산 필요
                                'change_percent': 0,
                                'volume': int(row.get('volume', 0)),
                                'date': date
                            }
                        
                        # MongoDB 저장
                        self._save_price_data(symbol, price_data, date)
                        success_count += 1
                        
                    except Exception as e:
                        logger.error(f"종목 {symbol} 가격 수집 실패: {e}")
                        error_count += 1
                
                # API 부하 방지
                time.sleep(0.1)
            
            logger.info(f"한국 주식 가격 수집 완료: 성공 {success_count}, 실패 {error_count}")
            return {
                'status': 'success',
                'date': date,
                'success': success_count,
                'errors': error_count
            }
            
        except Exception as e:
            logger.error(f"한국 주식 가격 수집 실패: {e}")
            return {'status': 'failed', 'message': str(e)}
    
    def collect_historical_data(self, symbol: str, market: str, 
                              start_date: str, end_date: str) -> bool:
        """과거 데이터 수집 (가격 + 재무)"""
        try:
            logger.info(f"{symbol} 과거 데이터 수집: {start_date} ~ {end_date}")
            
            if market == "KR":
                # 한국 주식: Provider 사용
                # 가격 데이터
                price_df = self.kr_provider.get_stock_price(symbol, start_date, end_date)
                
                if not price_df.empty:
                    # 각 날짜별로 저장
                    for date_idx in price_df.index:
                        date_str = date_idx.strftime('%Y-%m-%d')
                        
                        # 가격 데이터 저장
                        price_doc = {
                            '_id': f'{symbol}_{date_str}',
                            'symbol': symbol,
                            'date': date_str,
                            'open': float(price_df.loc[date_idx, 'open']),
                            'high': float(price_df.loc[date_idx, 'high']),
                            'low': float(price_df.loc[date_idx, 'low']),
                            'close': float(price_df.loc[date_idx, 'close']),
                            'volume': int(price_df.loc[date_idx, 'volume']),
                            'market': market,
                            'updated_at': datetime.now().isoformat()
                        }
                        
                        # 전일 대비 계산
                        if date_idx > price_df.index[0]:
                            prev_idx = price_df.index[price_df.index.get_loc(date_idx) - 1]
                            prev_close = float(price_df.loc[prev_idx, 'close'])
                            price_doc['change'] = price_doc['close'] - prev_close
                            price_doc['change_percent'] = (
                                (price_doc['change'] / prev_close * 100) 
                                if prev_close > 0 else 0
                            )
                        else:
                            price_doc['change'] = 0
                            price_doc['change_percent'] = 0
                        
                        self.db.db.stock_price_daily.replace_one(
                            {'_id': price_doc['_id']},
                            price_doc,
                            upsert=True
                        )
                
                # 재무 데이터 (Provider가 지원하는 경우)
                try:
                    fund_df = self.kr_provider.get_stock_fundamental(symbol, start_date, end_date)
                    if not fund_df.empty:
                        self._save_fundamental_data(symbol, fund_df, market)
                except Exception as e:
                    logger.warning(f"{symbol} 재무 데이터 수집 실패: {e}")
                
            else:
                # 미국 주식: yfinance 사용
                self._collect_us_historical_data(symbol, start_date, end_date)
            
            return True
            
        except Exception as e:
            logger.error(f"{symbol} 과거 데이터 수집 실패: {e}")
            return False
    
    def collect_indices_data(self, date: Optional[str] = None) -> Dict[str, Any]:
        """지수 데이터 수집"""
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"지수 데이터 수집 시작: {date}")
        
        kr_indices = {
            'KOSPI': '1001',
            'KOSDAQ': '2001', 
            'KOSPI200': '1028'
        }
        
        us_indices = {
            'S&P500': '^GSPC',
            'NASDAQ': '^IXIC',
            'DowJones': '^DJI'
        }
        
        success_count = 0
        error_count = 0
        
        # 한국 지수
        for name, code in kr_indices.items():
            try:
                df = self.kr_provider.get_index_data(code, date, date)
                
                if not df.empty:
                    self._save_index_data(name, code, df.iloc[0], date, 'KR')
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"{name} 지수 수집 실패: {e}")
                error_count += 1
        
        # 미국 지수 (yfinance)
        for name, symbol in us_indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=date, end=date)
                
                if not hist.empty:
                    row = hist.iloc[0]
                    self._save_index_data_yf(name, symbol, row, date, 'US')
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"{name} 지수 수집 실패: {e}")
                error_count += 1
        
        return {
            'status': 'success',
            'date': date,
            'success': success_count,
            'errors': error_count
        }
    
    def _save_price_data(self, symbol: str, data: Dict, date: str):
        """가격 데이터 저장"""
        doc = {
            '_id': f'{symbol}_{date}',
            'symbol': symbol,
            'date': date,
            'open': data.get('open', data.get('price', 0)),
            'high': data.get('high', data.get('price', 0)),
            'low': data.get('low', data.get('price', 0)),
            'close': data.get('price', 0),
            'volume': data.get('volume', 0),
            'change': data.get('change', 0),
            'change_percent': data.get('change_percent', 0),
            'market': 'KR',
            'updated_at': datetime.now().isoformat()
        }
        
        # 일일 가격 저장
        self.db.db.stock_price_daily.replace_one(
            {'_id': doc['_id']},
            doc,
            upsert=True
        )
        
        # 실시간 스냅샷 업데이트
        realtime_doc = doc.copy()
        realtime_doc['_id'] = symbol
        self.db.db.stock_realtime.replace_one(
            {'_id': symbol},
            realtime_doc,
            upsert=True
        )
    
    def _save_fundamental_data(self, symbol: str, df: pd.DataFrame, market: str):
        """재무 데이터 저장"""
        for date_idx in df.index:
            date_str = date_idx.strftime('%Y-%m-%d')
            
            doc = {
                '_id': f'{symbol}_{date_str}',
                'symbol': symbol,
                'date': date_str,
                'per': float(df.loc[date_idx, 'per']) if 'per' in df.columns else None,
                'pbr': float(df.loc[date_idx, 'pbr']) if 'pbr' in df.columns else None,
                'eps': float(df.loc[date_idx, 'eps']) if 'eps' in df.columns else None,
                'bps': float(df.loc[date_idx, 'bps']) if 'bps' in df.columns else None,
                'div': float(df.loc[date_idx, 'div']) if 'div' in df.columns else None,
                'market': market,
                'updated_at': datetime.now().isoformat()
            }
            
            self.db.db.stock_financial.replace_one(
                {'_id': doc['_id']},
                doc,
                upsert=True
            )
    
    def _save_index_data(self, name: str, code: str, data: pd.Series, 
                        date: str, market: str):
        """지수 데이터 저장"""
        doc = {
            '_id': f'{name}_{date}',
            'code': code,
            'name': name,
            'market': market,
            'date': date,
            'open': float(data.get('open', 0)),
            'high': float(data.get('high', 0)),
            'low': float(data.get('low', 0)),
            'close': float(data.get('close', 0)),
            'volume': int(data.get('volume', 0)),
            'updated_at': datetime.now().isoformat()
        }
        
        self.db.db.market_indices.replace_one(
            {'_id': doc['_id']},
            doc,
            upsert=True
        )
    
    def _save_index_data_yf(self, name: str, symbol: str, data: pd.Series, 
                           date: str, market: str):
        """yfinance 지수 데이터 저장"""
        doc = {
            '_id': f'{symbol}_{date}',
            'code': symbol,
            'name': name,
            'market': market,
            'date': date,
            'open': float(data['Open']),
            'high': float(data['High']),
            'low': float(data['Low']),
            'close': float(data['Close']),
            'volume': int(data['Volume']) if 'Volume' in data else 0,
            'updated_at': datetime.now().isoformat()
        }
        
        self.db.db.market_indices.replace_one(
            {'_id': doc['_id']},
            doc,
            upsert=True
        )
    
    def _collect_us_historical_data(self, symbol: str, start_date: str, end_date: str):
        """미국 주식 과거 데이터 수집 (yfinance)"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                return
            
            # 가격 데이터 저장
            for date_idx in hist.index:
                date_str = date_idx.strftime('%Y-%m-%d')
                
                doc = {
                    '_id': f'{symbol}_{date_str}',
                    'symbol': symbol,
                    'date': date_str,
                    'open': float(hist.loc[date_idx, 'Open']),
                    'high': float(hist.loc[date_idx, 'High']),
                    'low': float(hist.loc[date_idx, 'Low']),
                    'close': float(hist.loc[date_idx, 'Close']),
                    'volume': int(hist.loc[date_idx, 'Volume']),
                    'market': 'US',
                    'updated_at': datetime.now().isoformat()
                }
                
                # 전일 대비 계산
                if date_idx > hist.index[0]:
                    prev_idx = hist.index[hist.index.get_loc(date_idx) - 1]
                    prev_close = float(hist.loc[prev_idx, 'Close'])
                    doc['change'] = doc['close'] - prev_close
                    doc['change_percent'] = (
                        (doc['change'] / prev_close * 100) 
                        if prev_close > 0 else 0
                    )
                else:
                    doc['change'] = 0
                    doc['change_percent'] = 0
                
                self.db.db.stock_price_daily.replace_one(
                    {'_id': doc['_id']},
                    doc,
                    upsert=True
                )
            
            # 재무 데이터
            info = ticker.info
            if info:
                self._save_us_financial_data(symbol, info, end_date)
                
        except Exception as e:
            logger.error(f"{symbol} 미국 주식 데이터 수집 실패: {e}")
    
    def _save_us_financial_data(self, symbol: str, info: Dict, date: str):
        """미국 주식 재무 데이터 저장"""
        try:
            doc = {
                '_id': f'{symbol}_{date}',
                'symbol': symbol,
                'date': date,
                'per': info.get('trailingPE'),
                'pbr': info.get('priceToBook'),
                'eps': info.get('trailingEps'),
                'bps': info.get('bookValue'),
                'div': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else None,
                'market_cap': info.get('marketCap'),
                'shares': info.get('sharesOutstanding'),
                'market': 'US',
                'updated_at': datetime.now().isoformat()
            }
            
            self.db.db.stock_financial.replace_one(
                {'_id': doc['_id']},
                doc,
                upsert=True
            )
            
        except Exception as e:
            logger.error(f"{symbol} 미국 재무 데이터 저장 실패: {e}")
    
    # 기존 메서드들 유지 (US 주식 관련)
    def collect_us_stock_list(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """미국 주식 목록 수집 (기존 코드 유지)"""
        # ... 기존 구현 유지 ...
        pass