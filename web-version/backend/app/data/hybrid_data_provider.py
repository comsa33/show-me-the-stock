"""
하이브리드 데이터 제공자
FDR + Yahoo Finance를 조합하여 최적의 데이터 제공
"""
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
import logging

from .base_stock_data_provider import StockDataProvider
from .fdr_data_provider import FDRDataProvider
from .yahoo_data_provider import YahooDataProvider

logger = logging.getLogger(__name__)


class HybridDataProvider(StockDataProvider):
    """하이브리드 데이터 제공자 - FDR과 Yahoo Finance 조합"""
    
    def __init__(self):
        self._name = "Hybrid (FDR + Yahoo)"
        self._supported_markets = ["KR", "US"]
        
        # 내부 provider들
        self.fdr = FDRDataProvider()
        self.yahoo = YahooDataProvider()
        
        logger.info("Initialized Hybrid Data Provider")
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def supported_markets(self) -> List[str]:
        return self._supported_markets
    
    def get_stock_list(self, market: str = "ALL", date: Optional[str] = None) -> List[Dict[str, Any]]:
        """주식 목록 조회 - FDR 우선"""
        try:
            # FDR 시도
            result = self.fdr.get_stock_list(market, date)
            if result:
                return result
        except Exception as e:
            logger.warning(f"FDR stock list failed: {e}")
        
        # Yahoo 백업
        return self.yahoo.get_stock_list(market, date)
    
    def get_stock_price(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """주식 가격 데이터 조회 - FDR 우선"""
        try:
            # FDR 시도
            df = self.fdr.get_stock_price(symbol, start_date, end_date)
            if not df.empty:
                return df
        except Exception as e:
            logger.warning(f"FDR price data failed for {symbol}: {e}")
        
        # Yahoo 백업
        try:
            return self.yahoo.get_stock_price(symbol, start_date, end_date)
        except Exception as e:
            logger.error(f"Both providers failed for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_stock_price_realtime(self, symbol: str) -> Dict[str, Any]:
        """실시간 주식 가격 조회 - FDR 우선"""
        try:
            # FDR 시도
            data = self.fdr.get_stock_price_realtime(symbol)
            if data:
                return data
        except Exception as e:
            logger.warning(f"FDR realtime failed for {symbol}: {e}")
        
        # Yahoo 백업
        return self.yahoo.get_stock_price_realtime(symbol)
    
    def get_stock_fundamental(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """재무 데이터 조회 - Yahoo 사용 (FDR 미지원)"""
        return self.yahoo.get_stock_fundamental(symbol, start_date, end_date)
    
    def get_market_cap(self, symbol: str, date: Optional[str] = None) -> Dict[str, Any]:
        """시가총액 조회 - Yahoo 사용"""
        return self.yahoo.get_market_cap(symbol, date)
    
    def get_index_data(self, index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """지수 데이터 조회 - Yahoo 우선 (KRX 문제 회피)"""
        try:
            # Yahoo 먼저 시도 (한국 지수 지원)
            df = self.yahoo.get_index_data(index_code, start_date, end_date)
            if not df.empty:
                return df
        except Exception as e:
            logger.warning(f"Yahoo index data failed for {index_code}: {e}")
        
        # FDR 백업 시도
        try:
            return self.fdr.get_index_data(index_code, start_date, end_date)
        except Exception as e:
            logger.error(f"Both providers failed for index {index_code}: {e}")
            return pd.DataFrame()
    
    def get_market_overview(self, market: str = "KR", date: Optional[str] = None) -> pd.DataFrame:
        """시장 전체 데이터 조회 - FDR 우선"""
        try:
            df = self.fdr.get_market_overview(market, date)
            if not df.empty:
                return df
        except Exception as e:
            logger.warning(f"FDR market overview failed: {e}")
        
        return self.yahoo.get_market_overview(market, date)