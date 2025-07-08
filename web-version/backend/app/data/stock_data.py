from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

import FinanceDataReader as fdr
import pandas as pd
import yfinance as yf
from ..database.mongodb_client import get_mongodb_client

logger = logging.getLogger(__name__)


class StockDataFetcher:
    def __init__(self):
        self._kospi_cache = None
        self._kosdaq_cache = None
        self._us_cache = None
        self._all_kr_cache = None
        self._cache_time = None
        self.cache_duration = 300  # 5분 캐시
        # MongoDB 클라이언트 초기화
        try:
            self.db = get_mongodb_client()
            logger.info("MongoDB client initialized for StockDataFetcher")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB client: {e}")
            self.db = None

    def _is_cache_valid(self) -> bool:
        """캐시가 유효한지 확인"""
        if self._cache_time is None:
            return False
        return (datetime.now() - self._cache_time).seconds < self.cache_duration

    def get_all_kospi_stocks(self) -> List[Dict[str, str]]:
        """전체 KOSPI 종목 가져오기"""
        # 전체 한국 주식을 가져온 후 KOSPI만 필터링
        all_kr_stocks = self.get_all_kr_stocks()
        # 실제로는 시장 구분이 없으므로 전체 반환 (향후 개선 필요)
        return all_kr_stocks

    def get_all_kosdaq_stocks(self) -> List[Dict[str, str]]:
        """전체 KOSDAQ 종목 가져오기"""
        # 전체 한국 주식을 가져온 후 KOSDAQ만 필터링
        all_kr_stocks = self.get_all_kr_stocks()
        # 실제로는 시장 구분이 없으므로 전체 반환 (향후 개선 필요)
        return all_kr_stocks

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
        if self._all_kr_cache is None or not self._is_cache_valid():
            try:
                if self.db:
                    # MongoDB에서 전체 한국 주식 목록 가져오기
                    all_stocks = self.db.get_stock_list(market="KR")
                    
                    # 필요한 형식으로 변환
                    formatted_stocks = []
                    for stock in all_stocks:
                        formatted_stocks.append({
                            "name": stock.get("name", ""),
                            "symbol": stock.get("symbol", ""),
                            "display": f"{stock.get('name', '')} ({stock.get('symbol', '')})",
                            "market": "KR"
                        })
                    
                    self._all_kr_cache = formatted_stocks
                    self._cache_time = datetime.now()
                    logger.info(f"Loaded {len(formatted_stocks)} Korean stocks from MongoDB")
                else:
                    # MongoDB 연결 실패시 기본 종목들 반환
                    logger.warning("MongoDB not available, using default stocks")
                    self._all_kr_cache = self._get_default_kr_stocks()
                    
            except Exception as e:
                logger.error(f"Failed to get Korean stocks: {e}")
                # 실패시 기본 종목들 반환
                self._all_kr_cache = self._get_default_kr_stocks()
        
        return self._all_kr_cache

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
        elif period == "ytd":
            # YTD: 올해 1월 1일부터
            start_date = today.replace(month=1, day=1)
            logger.info(f"YTD period selected: start_date={start_date.strftime('%Y-%m-%d')}, end_date={today.strftime('%Y-%m-%d')}")
        elif period == "1y":
            start_date = today - timedelta(days=400)
        elif period == "2y":
            start_date = today - timedelta(days=800)
        elif period == "5y":
            start_date = today - timedelta(days=2000)
        elif period == "max":
            # MAX: 최대한 많은 데이터 (10년)
            start_date = today - timedelta(days=3650)
        else:
            start_date = today - timedelta(days=400)  # 기본값 1년
        
        return start_date.strftime('%Y-%m-%d')

    def get_real_time_price(self, symbol: str, market: str = "auto") -> Dict:
        """실시간 주가 정보 가져오기 (MongoDB 우선, fallback으로 pykrx/yfinance)"""
        try:
            # 먼저 MongoDB에서 최신 가격 데이터 조회
            from app.database.mongodb_client import get_mongodb_client
            from datetime import datetime, timedelta
            
            try:
                db = get_mongodb_client()
                latest_price = db.get_latest_price(symbol)
                
                if latest_price:
                    # MongoDB에서 데이터를 찾았을 때
                    return {
                        "symbol": symbol,
                        "price": latest_price.get("close", 0),
                        "change": latest_price.get("change", 0),
                        "change_percent": latest_price.get("change_percent", 0),
                        "volume": latest_price.get("volume", 0),
                        "timestamp": latest_price.get("date", datetime.now().isoformat()),
                        "data_source": "mongodb"
                    }
            except Exception as e:
                logger.info(f"MongoDB fetch failed for {symbol}: {e}")
            
            # MongoDB에 데이터가 없으면 pykrx/yfinance에서 조회
            from pykrx import stock
            
            # 최근 거래일 데이터를 찾기 위해 최대 10일 전까지 확인
            end_date = datetime.now()
            start_date = end_date - timedelta(days=10)
            today = end_date.strftime("%Y%m%d")
            week_ago = start_date.strftime("%Y%m%d")
            
            if market.upper() == "KR":
                try:
                    # 최근 1주일 데이터 시도 (더 안정적)
                    df = stock.get_market_ohlcv(week_ago, today, symbol)
                    
                    if df is not None and not df.empty:
                        latest = df.iloc[-1]
                        prev = df.iloc[-2] if len(df) > 1 else latest
                        
                        current_price = float(latest["종가"])
                        previous_price = float(prev["종가"]) if len(df) > 1 else current_price
                        change = current_price - previous_price
                        change_percent = (change / previous_price * 100) if previous_price > 0 else 0
                        
                        return {
                            "symbol": symbol,
                            "price": current_price,
                            "change": change,
                            "change_percent": change_percent,
                            "volume": int(latest["거래량"]),
                            "timestamp": datetime.now().isoformat(),
                            "data_source": "pykrx_real"
                        }
                except Exception as e:
                    logger.warning(f"pykrx data fetch failed for {symbol}: {e}")
            
            elif market.upper() == "US":
                try:
                    import yfinance as yf
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d")
                    
                    if not hist.empty:
                        current_price = float(hist["Close"].iloc[-1])
                        previous_price = float(hist["Close"].iloc[-2]) if len(hist) > 1 else current_price
                        change = current_price - previous_price
                        change_percent = (change / previous_price * 100) if previous_price > 0 else 0
                        
                        return {
                            "symbol": symbol,
                            "price": current_price,
                            "change": change,
                            "change_percent": change_percent,
                            "volume": int(hist["Volume"].iloc[-1]),
                            "timestamp": datetime.now().isoformat(),
                            "data_source": "yfinance_real"
                        }
                except Exception as e:
                    logger.warning(f"yfinance data fetch failed for {symbol}: {e}")
            
            # 실패 시 fallback mock 데이터
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
                "timestamp": datetime.now().isoformat(),
                "data_source": "mock_fallback"
            }
            
        except Exception as e:
            logger.error(f"Error getting real time price for {symbol}: {e}")
            # 에러 시 기본값 반환
            return {
                "symbol": symbol,
                "price": 0,
                "change": 0,
                "change_percent": 0,
                "volume": 0,
                "timestamp": datetime.now().isoformat(),
                "data_source": "error_fallback"
            }