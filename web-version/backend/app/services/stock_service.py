"""
주식 데이터 서비스
외부 API 연동 및 데이터 처리 로직
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
import yfinance as yf
import FinanceDataReader as fdr
from app.models.stock import (
    StockInfo, PriceData, TechnicalIndicators, EnrichedPriceData,
    StockDataResponse, MultiStockDataResponse, MarketType, PeriodType
)
from app.core.cache import cached, CacheKeys
from app.core.config import get_settings


class StockDataService:
    """주식 데이터 서비스"""
    
    def __init__(self):
        self.settings = get_settings()
        self._kospi_symbols = None
        self._nasdaq_symbols = None
    
    async def get_kospi_symbols(self) -> Dict[str, str]:
        """KOSPI/KOSDAQ 심볼 목록 반환"""
        if self._kospi_symbols is None:
            self._kospi_symbols = await self._load_korean_stocks()
        return self._kospi_symbols
    
    async def get_nasdaq_symbols(self) -> Dict[str, str]:
        """NASDAQ 심볼 목록 반환"""
        if self._nasdaq_symbols is None:
            self._nasdaq_symbols = await self._load_us_stocks()
        return self._nasdaq_symbols
    
    @cached(ttl=3600, key_prefix="korean_stocks")
    async def _load_korean_stocks(self) -> Dict[str, str]:
        """한국 주식 목록 로드"""
        try:
            # 안정적인 기본 주식 목록 사용
            default_stocks = {
                "삼성전자": "005930",
                "SK하이닉스": "000660",
                "NAVER": "035420",
                "LG화학": "051910",
                "KB금융": "105560",
                "LG에너지솔루션": "373220",
                "Celltrion": "068270",
                "삼성SDI": "006400",
                "SK아이이기술": "361610",
                "HMM": "011200",
                "현대차": "005380",
                "POSCO홀딩스": "005490",
                "기아": "000270",
                "LG전자": "066570",
                "삼성바이오로직스": "207940",
                "SK텔레콤": "017670",
                "CJ제일제당": "097950",
                "대한항공": "003490",
                "카카오": "035720",
                "대우조선해양": "042660",
                "에코프로비엠": "086520",
                "신한지주회사": "055550",
                "하나금융지주": "086790",
                "KB국민은행": "105560"
            }
            return default_stocks
            
        except Exception as e:
            print(f"Korean stocks loading failed: {e}")
            return {
                "삼성전자": "005930",
                "SK하이닉스": "000660",
                "NAVER": "035420"
            }
    
    @cached(ttl=3600, key_prefix="us_stocks")
    async def _load_us_stocks(self) -> Dict[str, str]:
        """미국 주식 목록 로드"""
        return {
            # Tech Giants
            "Apple": "AAPL",
            "Microsoft": "MSFT",
            "Amazon": "AMZN",
            "Google (Alphabet)": "GOOGL",
            "Tesla": "TSLA",
            "Meta (Facebook)": "META",
            "Netflix": "NFLX",
            "NVIDIA": "NVDA",
            "AMD": "AMD",
            "Intel": "INTC",
            
            # Financial
            "Berkshire Hathaway": "BRK-B",
            "JPMorgan Chase": "JPM",
            "Visa": "V",
            "Mastercard": "MA",
            "Bank of America": "BAC",
            
            # Healthcare
            "Johnson & Johnson": "JNJ",
            "UnitedHealth": "UNH",
            "Pfizer": "PFE",
            "Moderna": "MRNA",
            
            # Consumer
            "Procter & Gamble": "PG",
            "Coca-Cola": "KO",
            "PepsiCo": "PEP",
            "Walmart": "WMT",
            "Home Depot": "HD",
            "McDonald's": "MCD",
            "Nike": "NKE",
            
            # Others
            "Disney": "DIS",
            "PayPal": "PYPL",
            "Uber": "UBER",
            "Zoom": "ZM",
            "Spotify": "SPOT"
        }
    
    async def search_stocks(self, query: str, market: MarketType, limit: int = 20) -> List[Dict]:
        """주식 검색"""
        if market == MarketType.KR:
            symbols_dict = await self.get_kospi_symbols()
        else:
            symbols_dict = await self.get_nasdaq_symbols()
        
        results = []
        query_lower = query.lower().strip()
        
        if not query_lower:
            return results
        
        # 검색 로직
        for name, symbol in symbols_dict.items():
            name_lower = name.lower()
            symbol_upper = symbol.upper()
            query_upper = query.upper()
            
            score = 0
            
            # 정확한 매칭
            if symbol_upper == query_upper:
                score = 100
            elif symbol_upper.startswith(query_upper):
                score = 90
            elif name_lower == query_lower:
                score = 85
            elif name_lower.startswith(query_lower):
                score = 80
            elif query_upper in symbol_upper:
                score = 70
            elif query_lower in name_lower:
                score = 60
            elif any(word.startswith(query_lower) for word in name_lower.split()):
                score = 50
            
            if score > 0:
                results.append({
                    "name": name,
                    "symbol": symbol,
                    "score": score,
                    "display": f"{name} ({symbol})",
                    "market": market
                })
        
        # 점수순 정렬
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    @cached(ttl=60, key_prefix="stock_data")
    async def get_stock_data(
        self, 
        symbol: str, 
        period: PeriodType, 
        market: MarketType,
        include_indicators: bool = True
    ) -> Optional[StockDataResponse]:
        """개별 주식 데이터 조회"""
        try:
            if market == MarketType.KR:
                data = await self._get_korean_stock_data(symbol, period)
                currency = "KRW"
                exchange = "KRX"
            else:
                data = await self._get_us_stock_data(symbol, period)
                currency = "USD"
                exchange = "NASDAQ"
            
            if data is None or data.empty:
                return None
            
            # 기술적 지표 계산
            if include_indicators:
                data = self._calculate_technical_indicators(data)
            
            # 데이터 변환
            price_data_list = []
            for idx, row in data.iterrows():
                indicators = None
                if include_indicators:
                    indicators = TechnicalIndicators(
                        ma5=row.get('MA5'),
                        ma20=row.get('MA20'),
                        ma60=row.get('MA60'),
                        rsi=row.get('RSI'),
                        macd=row.get('MACD'),
                        signal=row.get('Signal'),
                        bb_upper=row.get('BB_Upper'),
                        bb_middle=row.get('BB_Middle'),
                        bb_lower=row.get('BB_Lower')
                    )
                
                price_data = EnrichedPriceData(
                    timestamp=idx if isinstance(idx, datetime) else pd.to_datetime(idx),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']),
                    indicators=indicators
                )
                price_data_list.append(price_data)
            
            # 주식 정보 조회
            stock_name = await self._get_stock_name(symbol, market)
            
            stock_info = StockInfo(
                symbol=symbol,
                name=stock_name,
                market=market,
                currency=currency,
                exchange=exchange
            )
            
            return StockDataResponse(
                info=stock_info,
                data=price_data_list,
                period=period,
                total_points=len(price_data_list)
            )
            
        except Exception as e:
            print(f"Error getting stock data for {symbol}: {e}")
            return None
    
    async def get_multiple_stocks(
        self, 
        symbols: List[str], 
        period: PeriodType, 
        market: MarketType,
        include_indicators: bool = True
    ) -> MultiStockDataResponse:
        """다중 주식 데이터 조회"""
        tasks = [
            self.get_stock_data(symbol, period, market, include_indicators)
            for symbol in symbols
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        stocks = {}
        successful_symbols = []
        failed_symbols = []
        
        for symbol, result in zip(symbols, results):
            if isinstance(result, Exception) or result is None:
                failed_symbols.append(symbol)
            else:
                stocks[symbol] = result
                successful_symbols.append(symbol)
        
        return MultiStockDataResponse(
            stocks=stocks,
            requested_symbols=symbols,
            successful_symbols=successful_symbols,
            failed_symbols=failed_symbols
        )
    
    async def _get_korean_stock_data(self, symbol: str, period: PeriodType) -> Optional[pd.DataFrame]:
        """한국 주식 데이터 조회"""
        try:
            # 기간 변환
            end_date = datetime.now()
            if period == PeriodType.ONE_DAY:
                start_date = end_date - timedelta(days=1)
            elif period == PeriodType.FIVE_DAYS:
                start_date = end_date - timedelta(days=5)
            elif period == PeriodType.ONE_MONTH:
                start_date = end_date - timedelta(days=30)
            elif period == PeriodType.THREE_MONTHS:
                start_date = end_date - timedelta(days=90)
            elif period == PeriodType.SIX_MONTHS:
                start_date = end_date - timedelta(days=180)
            elif period == PeriodType.ONE_YEAR:
                start_date = end_date - timedelta(days=365)
            elif period == PeriodType.TWO_YEARS:
                start_date = end_date - timedelta(days=730)
            elif period == PeriodType.FIVE_YEARS:
                start_date = end_date - timedelta(days=1825)
            else:
                start_date = end_date - timedelta(days=365)
            
            data = fdr.DataReader(symbol, start=start_date, end=end_date)
            
            if data.empty:
                return None
                
            data.reset_index(inplace=True)
            return data
            
        except Exception as e:
            print(f"Error fetching Korean stock data for {symbol}: {e}")
            return None
    
    async def _get_us_stock_data(self, symbol: str, period: PeriodType) -> Optional[pd.DataFrame]:
        """미국 주식 데이터 조회"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period.value)
            
            if data.empty:
                return None
                
            data.reset_index(inplace=True)
            return data
            
        except Exception as e:
            print(f"Error fetching US stock data for {symbol}: {e}")
            return None
    
    def _calculate_technical_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """기술적 지표 계산"""
        df = data.copy()
        
        # 이동평균선
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        avg_gain = gain.rolling(window=14).mean()
        avg_loss = loss.rolling(window=14).mean()
        rs = avg_gain / avg_loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # MACD
        exp1 = df['Close'].ewm(span=12).mean()
        exp2 = df['Close'].ewm(span=26).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9).mean()
        
        # 볼린저 밴드
        df['BB_Middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
        df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
        
        return df
    
    async def _get_stock_name(self, symbol: str, market: MarketType) -> str:
        """주식명 조회"""
        if market == MarketType.KR:
            symbols_dict = await self.get_kospi_symbols()
            for name, sym in symbols_dict.items():
                if sym == symbol:
                    return name
        else:
            symbols_dict = await self.get_nasdaq_symbols()
            for name, sym in symbols_dict.items():
                if sym == symbol:
                    return name
        
        return symbol  # 이름을 찾지 못하면 심볼 반환


# 서비스 인스턴스
stock_service = StockDataService()