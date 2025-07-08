"""
주식 데이터 제공자 추상 인터페이스
모든 데이터 소스(pykrx, FinanceDataReader, yfinance 등)는 이 인터페이스를 구현해야 함
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from datetime import datetime


class StockDataProvider(ABC):
    """주식 데이터 제공자 추상 클래스"""
    
    @abstractmethod
    def get_stock_list(self, market: str = "ALL", date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        주식 목록 조회
        
        Args:
            market: 시장 구분 (KR, US, ALL)
            date: 조회 기준일 (YYYY-MM-DD)
            
        Returns:
            List[Dict]: 주식 목록
            - symbol: 종목 코드
            - name: 종목명
            - market: 시장 구분
            - display: 표시용 텍스트
        """
        pass
    
    @abstractmethod
    def get_stock_price(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        주식 가격 데이터 조회
        
        Args:
            symbol: 종목 코드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            
        Returns:
            DataFrame with columns: open, high, low, close, volume
            Index: date
        """
        pass
    
    @abstractmethod
    def get_stock_price_realtime(self, symbol: str) -> Dict[str, Any]:
        """
        실시간(최신) 주식 가격 조회
        
        Args:
            symbol: 종목 코드
            
        Returns:
            Dict: 현재가 정보
            - symbol: 종목 코드
            - price: 현재가
            - change: 전일 대비
            - change_percent: 전일 대비율
            - volume: 거래량
            - date: 데이터 일자
        """
        pass
    
    @abstractmethod
    def get_stock_fundamental(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        재무 데이터 조회
        
        Args:
            symbol: 종목 코드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            
        Returns:
            DataFrame with columns: per, pbr, eps, bps, div
            Index: date
        """
        pass
    
    @abstractmethod
    def get_market_cap(self, symbol: str, date: Optional[str] = None) -> Dict[str, Any]:
        """
        시가총액 및 발행주식수 조회
        
        Args:
            symbol: 종목 코드
            date: 조회 기준일
            
        Returns:
            Dict: 시가총액 정보
            - market_cap: 시가총액
            - shares: 발행주식수
        """
        pass
    
    @abstractmethod
    def get_index_data(self, index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        지수 데이터 조회
        
        Args:
            index_code: 지수 코드
            start_date: 시작일 (YYYY-MM-DD)
            end_date: 종료일 (YYYY-MM-DD)
            
        Returns:
            DataFrame with columns: open, high, low, close, volume
            Index: date
        """
        pass
    
    @abstractmethod
    def get_market_overview(self, market: str, date: Optional[str] = None) -> pd.DataFrame:
        """
        시장 전체 데이터 조회
        
        Args:
            market: 시장 구분 (KR, US)
            date: 조회 기준일
            
        Returns:
            DataFrame: 전체 종목의 가격 정보
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """데이터 제공자 이름"""
        pass
    
    @property
    @abstractmethod
    def supported_markets(self) -> List[str]:
        """지원하는 시장 목록"""
        pass
    
    def validate_symbol(self, symbol: str) -> Tuple[bool, str]:
        """
        종목 코드 유효성 검증
        
        Args:
            symbol: 종목 코드
            
        Returns:
            Tuple[bool, str]: (유효 여부, 메시지)
        """
        # 기본 검증 로직 (하위 클래스에서 오버라이드 가능)
        if not symbol:
            return False, "종목 코드가 비어있습니다"
        return True, "OK"
    
    def validate_date_range(self, start_date: str, end_date: str) -> Tuple[bool, str]:
        """
        날짜 범위 유효성 검증
        
        Args:
            start_date: 시작일
            end_date: 종료일
            
        Returns:
            Tuple[bool, str]: (유효 여부, 메시지)
        """
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            
            if start > end:
                return False, "시작일이 종료일보다 늦습니다"
            
            if end > datetime.now():
                return False, "종료일이 미래입니다"
                
            return True, "OK"
        except ValueError:
            return False, "날짜 형식이 올바르지 않습니다 (YYYY-MM-DD)"