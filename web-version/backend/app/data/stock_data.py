from datetime import datetime, timedelta
from typing import Dict, List, Optional

import FinanceDataReader as fdr
import pandas as pd
import yfinance as yf
from pykrx import stock


class StockDataFetcher:
    def __init__(self):
        self._kospi_cache = None
        self._kosdaq_cache = None
        self._us_cache = None
        self._cache_time = None
        self.cache_duration = 300  # 5분 캐시

    def _is_cache_valid(self) -> bool:
        """캐시가 유효한지 확인"""
        if self._cache_time is None:
            return False
        return (datetime.now() - self._cache_time).seconds < self.cache_duration

    def get_all_kospi_stocks(self) -> List[Dict[str, str]]:
        """전체 KOSPI 종목 가져오기"""
        if self._kospi_cache is None or not self._is_cache_valid():
            try:
                # pykrx를 사용하여 전체 KOSPI 종목 가져오기
                today = datetime.now().strftime('%Y%m%d')
                kospi_list = stock.get_market_ticker_list(today, market="KOSPI")
                
                stocks = []
                for ticker in kospi_list:
                    try:
                        name = stock.get_market_ticker_name(ticker)
                        if name and len(name.strip()) > 0:
                            stocks.append({
                                "name": name,
                                "symbol": ticker,
                                "display": f"{name} ({ticker})",
                                "market": "KR"
                            })
                    except:
                        continue
                
                self._kospi_cache = stocks
                self._cache_time = datetime.now()
            except Exception as e:
                print(f"KOSPI 데이터 로딩 실패: {e}")
                # 실패시 기본 종목들 반환
                self._kospi_cache = self._get_default_kr_stocks()
        
        return self._kospi_cache

    def get_all_kosdaq_stocks(self) -> List[Dict[str, str]]:
        """전체 KOSDAQ 종목 가져오기"""
        if self._kosdaq_cache is None or not self._is_cache_valid():
            try:
                today = datetime.now().strftime('%Y%m%d')
                kosdaq_list = stock.get_market_ticker_list(today, market="KOSDAQ")
                
                stocks = []
                for ticker in kosdaq_list:
                    try:
                        name = stock.get_market_ticker_name(ticker)
                        if name and len(name.strip()) > 0:
                            stocks.append({
                                "name": name,
                                "symbol": ticker,
                                "display": f"{name} ({ticker})",
                                "market": "KR"
                            })
                    except:
                        continue
                
                self._kosdaq_cache = stocks
                self._cache_time = datetime.now()
            except Exception as e:
                print(f"KOSDAQ 데이터 로딩 실패: {e}")
                self._kosdaq_cache = []
        
        return self._kosdaq_cache

    def get_all_us_stocks(self) -> List[Dict[str, str]]:
        """미국 주요 종목 가져오기"""
        if self._us_cache is None or not self._is_cache_valid():
            # S&P 500과 NASDAQ 100 주요 종목들
            us_symbols = {
                # Mega Cap Tech
                "Apple Inc": "AAPL",
                "Microsoft Corporation": "MSFT", 
                "Alphabet Inc Class A": "GOOGL",
                "Amazon.com Inc": "AMZN",
                "Meta Platforms Inc": "META",
                "Tesla Inc": "TSLA",
                "NVIDIA Corporation": "NVDA",
                "Netflix Inc": "NFLX",
                "Adobe Inc": "ADBE",
                "Salesforce Inc": "CRM",
                
                # Major Banks
                "JPMorgan Chase & Co": "JPM",
                "Bank of America Corp": "BAC",
                "Wells Fargo & Company": "WFC",
                "Goldman Sachs Group Inc": "GS",
                "Morgan Stanley": "MS",
                
                # Healthcare & Pharma
                "Johnson & Johnson": "JNJ",
                "Pfizer Inc": "PFE",
                "UnitedHealth Group Inc": "UNH",
                "Merck & Co Inc": "MRK",
                "Abbott Laboratories": "ABT",
                
                # Consumer & Retail
                "Walmart Inc": "WMT",
                "The Coca-Cola Company": "KO",
                "PepsiCo Inc": "PEP",
                "Procter & Gamble Co": "PG",
                "Nike Inc": "NKE",
                "McDonald's Corporation": "MCD",
                "Starbucks Corporation": "SBUX",
                
                # Industrial & Energy
                "ExxonMobil Corporation": "XOM",
                "Chevron Corporation": "CVX",
                "Caterpillar Inc": "CAT",
                "Boeing Company": "BA",
                "General Electric Company": "GE",
                
                # Semiconductor
                "Intel Corporation": "INTC",
                "Advanced Micro Devices": "AMD",
                "Qualcomm Incorporated": "QCOM",
                "Broadcom Inc": "AVGO",
                "Taiwan Semiconductor": "TSM",
                
                # Communication & Media
                "Verizon Communications": "VZ",
                "AT&T Inc": "T",
                "Comcast Corporation": "CMCSA",
                "Walt Disney Company": "DIS",
                
                # Electric Vehicles & Clean Energy
                "Ford Motor Company": "F",
                "General Motors Company": "GM",
                "Rivian Automotive Inc": "RIVN",
                "Lucid Group Inc": "LCID",
                
                # Emerging Tech
                "Palantir Technologies": "PLTR",
                "Zoom Video Communications": "ZM",
                "Spotify Technology SA": "SPOT",
                "Snowflake Inc": "SNOW",
                "CrowdStrike Holdings": "CRWD",
                
                # Biotech
                "Moderna Inc": "MRNA",
                "Gilead Sciences Inc": "GILD",
                "Regeneron Pharmaceuticals": "REGN",
                "Biogen Inc": "BIIB",
                
                # Financial Services
                "Visa Inc": "V",
                "Mastercard Incorporated": "MA",
                "PayPal Holdings Inc": "PYPL",
                "Square Inc": "SQ",
                "American Express Company": "AXP",
                
                # Real Estate & REITs
                "American Tower Corporation": "AMT",
                "Prologis Inc": "PLD",
                "Crown Castle International": "CCI",
                
                # Utilities
                "NextEra Energy Inc": "NEE",
                "Duke Energy Corporation": "DUK",
                "Southern Company": "SO",
                
                # Materials
                "Linde plc": "LIN",
                "Air Products and Chemicals": "APD",
                "Dow Inc": "DOW",
                
                # Aerospace & Defense
                "Lockheed Martin Corporation": "LMT",
                "Raytheon Technologies": "RTX",
                "Northrop Grumman Corporation": "NOC"
            }
            
            stocks = []
            for name, symbol in us_symbols.items():
                stocks.append({
                    "name": name,
                    "symbol": symbol,
                    "display": f"{name} ({symbol})",
                    "market": "US"
                })
            
            self._us_cache = stocks
            self._cache_time = datetime.now()
        
        return self._us_cache

    def _get_default_kr_stocks(self) -> List[Dict[str, str]]:
        """기본 한국 종목 (fallback)"""
        default_stocks = {
            "삼성전자": "005930",
            "SK하이닉스": "000660", 
            "NAVER": "035420",
            "LG화학": "051910",
            "LG에너지솔루션": "373220",
            "셀트리온": "068270",
            "삼성SDI": "006400",
            "현대차": "005380",
            "POSCO홀딩스": "005490",
            "기아": "000270",
            "LG전자": "066570",
            "삼성바이오로직스": "207940",
            "SK텔레콤": "017670",
            "카카오": "035720",
            "신한지주": "055550",
            "하나금융지주": "086790",
            "KB금융": "105560",
            "현대모비스": "012330",
            "LG생활건강": "051900",
            "한국전력": "015760"
        }
        
        stocks = []
        for name, symbol in default_stocks.items():
            stocks.append({
                "name": name,
                "symbol": symbol,
                "display": f"{name} ({symbol})",
                "market": "KR"
            })
        
        return stocks

    def get_all_kr_stocks(self) -> List[Dict[str, str]]:
        """한국 전체 종목 (KOSPI + KOSDAQ) 가져오기"""
        kospi_stocks = self.get_all_kospi_stocks()
        kosdaq_stocks = self.get_all_kosdaq_stocks()
        return kospi_stocks + kosdaq_stocks

    def get_paginated_stocks(self, market: str, page: int = 1, limit: int = 20) -> Dict:
        """페이지네이션된 주식 데이터 반환"""
        if market.upper() == "KR" or market.upper() == "KOSPI":
            all_stocks = self.get_all_kr_stocks()
        elif market.upper() == "US":
            all_stocks = self.get_all_us_stocks()
        else:
            all_stocks = []
        
        total_count = len(all_stocks)
        total_pages = (total_count + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        paginated_stocks = all_stocks[start_idx:end_idx]
        
        return {
            "stocks": paginated_stocks,
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "limit": limit
        }

    def get_stock_data(self, symbol: str, period: str = "1y", market: str = "auto") -> Optional[pd.DataFrame]:
        """개별 종목 데이터 가져오기"""
        try:
            if market.upper() == "KR":
                # 한국 주식은 FinanceDataReader 사용
                data = fdr.DataReader(symbol, start=self._get_start_date(period))
            else:
                # 미국 주식은 yfinance 사용
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period)
            
            if data.empty:
                return None
            
            # 컬럼명 통일
            if 'Adj Close' in data.columns:
                data = data.drop('Adj Close', axis=1)
            
            return data
        except Exception as e:
            print(f"주식 데이터 로딩 실패 {symbol}: {e}")
            return None

    def _get_start_date(self, period: str) -> str:
        """기간을 시작 날짜로 변환"""
        today = datetime.now()
        
        if period == "1d":
            start_date = today - timedelta(days=7)  # 1일 데이터를 위해 1주일 전부터
        elif period == "5d":
            start_date = today - timedelta(days=14)
        elif period == "1mo":
            start_date = today - timedelta(days=35)
        elif period == "3mo":
            start_date = today - timedelta(days=100)
        elif period == "6mo":
            start_date = today - timedelta(days=200)
        elif period == "1y":
            start_date = today - timedelta(days=400)
        elif period == "2y":
            start_date = today - timedelta(days=800)
        elif period == "5y":
            start_date = today - timedelta(days=2000)
        else:
            start_date = today - timedelta(days=400)  # 기본값 1년
        
        return start_date.strftime('%Y-%m-%d')

    def get_real_time_price(self, symbol: str, market: str = "auto") -> Dict:
        """실시간 주가 정보 가져오기 (Mock 데이터)"""
        # 실제 구현에서는 실시간 API를 사용해야 함
        import random
        
        if market.upper() == "KR":
            base_price = random.randint(10000, 100000)
        else:
            base_price = random.randint(50, 500)
        
        change = random.uniform(-5, 5)
        change_percent = change / base_price * 100
        
        return {
            "symbol": symbol,
            "price": base_price,
            "change": change,
            "change_percent": change_percent,
            "volume": random.randint(100000, 10000000),
            "timestamp": datetime.now().isoformat()
        }