"""
pykrx 기반 데이터 제공자
기존 pykrx_stock_data.py의 기능을 StockDataProvider 인터페이스로 래핑
"""
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
import logging

from .base_stock_data_provider import StockDataProvider
from .pykrx_stock_data import PykrxStockDataFetcher
from pykrx import stock

logger = logging.getLogger(__name__)


class PykrxDataProvider(StockDataProvider):
    """pykrx 기반 데이터 제공자 구현"""
    
    def __init__(self):
        self.pykrx_data = PykrxStockDataFetcher()
        self._name = "pykrx"
        self._supported_markets = ["KR"]
        
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def supported_markets(self) -> List[str]:
        return self._supported_markets
    
    def get_stock_list(self, market: str = "KR", date: Optional[str] = None) -> List[Dict[str, Any]]:
        """주식 목록 조회"""
        if market.upper() not in self.supported_markets:
            logger.warning(f"Market {market} not supported by {self.name}")
            return []
            
        try:
            # 기존 메서드 활용
            date_str = date.replace("-", "") if date else datetime.now().strftime("%Y%m%d")
            return self.pykrx_data.get_market_ticker_list(date_str, market)
        except Exception as e:
            logger.error(f"Failed to get stock list: {e}")
            return []
    
    def get_stock_price(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """주식 가격 데이터 조회"""
        try:
            # YYYY-MM-DD를 YYYYMMDD로 변환
            start = start_date.replace("-", "")
            end = end_date.replace("-", "")
            
            # pykrx 호출
            df = stock.get_market_ohlcv_by_date(start, end, symbol)
            
            if df.empty:
                return pd.DataFrame()
            
            # 컬럼명 영문 변환
            df = df.rename(columns={
                '시가': 'open',
                '고가': 'high',
                '저가': 'low',
                '종가': 'close',
                '거래량': 'volume'
            })
            
            # 필요한 컬럼만 선택
            columns = ['open', 'high', 'low', 'close', 'volume']
            df = df[[col for col in columns if col in df.columns]]
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to get stock price for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_stock_price_realtime(self, symbol: str) -> Dict[str, Any]:
        """실시간 주식 가격 조회"""
        try:
            # 오늘 날짜로 조회
            today = datetime.now().strftime("%Y%m%d")
            df = self.pykrx_data.get_market_ohlcv_today(today, "KR")
            
            if df.empty:
                return {}
            
            # 특정 종목 찾기
            stock_data = df[df['ticker'] == symbol]
            if stock_data.empty:
                return {}
            
            row = stock_data.iloc[0]
            return {
                'symbol': symbol,
                'price': float(row.get('종가', 0)),
                'change': float(row.get('등락률', 0)),
                'change_percent': float(row.get('등락률', 0)),
                'volume': int(row.get('거래량', 0)),
                'date': today
            }
            
        except Exception as e:
            logger.error(f"Failed to get realtime price for {symbol}: {e}")
            return {}
    
    def get_stock_fundamental(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """재무 데이터 조회"""
        try:
            start = start_date.replace("-", "")
            end = end_date.replace("-", "")
            
            df = stock.get_market_fundamental_by_date(start, end, symbol)
            
            if df.empty:
                return pd.DataFrame()
            
            # 컬럼명 소문자로 변환
            df.columns = [col.lower() for col in df.columns]
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to get fundamental data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_market_cap(self, symbol: str, date: Optional[str] = None) -> Dict[str, Any]:
        """시가총액 조회"""
        try:
            date_str = date.replace("-", "") if date else datetime.now().strftime("%Y%m%d")
            
            df = stock.get_market_cap_by_date(date_str, date_str, symbol)
            
            if df.empty:
                return {}
            
            row = df.iloc[0]
            return {
                'market_cap': int(row.get('시가총액', 0)),
                'shares': int(row.get('상장주식수', 0))
            }
            
        except Exception as e:
            logger.error(f"Failed to get market cap for {symbol}: {e}")
            return {}
    
    def get_index_data(self, index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """지수 데이터 조회"""
        try:
            start = start_date.replace("-", "")
            end = end_date.replace("-", "")
            
            df = stock.get_index_ohlcv_by_date(start, end, index_code)
            
            if df.empty:
                return pd.DataFrame()
            
            # 컬럼명 영문 변환
            df = df.rename(columns={
                '시가': 'open',
                '고가': 'high',
                '저가': 'low',
                '종가': 'close',
                '거래량': 'volume'
            })
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to get index data for {index_code}: {e}")
            return pd.DataFrame()
    
    def get_market_overview(self, market: str = "KR", date: Optional[str] = None) -> pd.DataFrame:
        """시장 전체 데이터 조회"""
        try:
            date_str = date.replace("-", "") if date else datetime.now().strftime("%Y%m%d")
            
            return self.pykrx_data.get_market_ohlcv_today(date_str, market)
            
        except Exception as e:
            logger.error(f"Failed to get market overview: {e}")
            return pd.DataFrame()