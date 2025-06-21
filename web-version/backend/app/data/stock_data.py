from datetime import datetime, timedelta
from typing import Dict, List, Optional

import FinanceDataReader as fdr
import pandas as pd
import yfinance as yf


class StockDataFetcher:
    def __init__(self):
        self.kospi_symbols = self._get_kospi_symbols()
        self.nasdaq_symbols = self._get_popular_nasdaq_symbols()

    def _get_kospi_symbols(self) -> Dict[str, str]:
        """한국 주식 데이터 가져오기"""
        return {
            "삼성전자": "005930",
            "SK하이닉스": "000660",
            "NAVER": "035420",
            "LG화학": "051910",
            "LG에너지솔루션": "373220",
            "Celltrion": "068270",
            "삼성SDI": "006400",
            "현대차": "005380",
            "POSCO홀딩스": "005490",
            "기아": "000270",
            "LG전자": "066570",
            "삼성바이오로직스": "207940",
            "SK텔레콤": "017670",
            "CJ제일제당": "097950",
            "대한항공": "003490",
            "신한지주회사": "055550",
            "하나금융지주": "086790",
            "카카오": "035720",
            "대우조선해양": "042660",
            "에코프로비엠": "086520"
        }

    def _get_popular_nasdaq_symbols(self) -> Dict[str, str]:
        """미국 주식 데이터 가져오기"""
        return {
            # Big Tech
            "Apple": "AAPL",
            "Microsoft": "MSFT",
            "Google (Alphabet)": "GOOGL",
            "Amazon": "AMZN",
            "Meta (Facebook)": "META",
            "Tesla": "TSLA",
            "NVIDIA": "NVDA",
            "Netflix": "NFLX",
            
            # Semiconductor
            "AMD": "AMD",
            "Intel": "INTC",
            "Qualcomm": "QCOM",
            "Broadcom": "AVGO",
            
            # Financial
            "Berkshire Hathaway": "BRK-B",
            "JPMorgan Chase": "JPM",
            "Visa": "V",
            "Mastercard": "MA",
            "PayPal": "PYPL",
            
            # Healthcare
            "Johnson & Johnson": "JNJ",
            "UnitedHealth": "UNH",
            "Pfizer": "PFE",
            "Moderna": "MRNA",
            
            # Consumer
            "Coca-Cola": "KO",
            "PepsiCo": "PEP",
            "Walmart": "WMT",
            "McDonald's": "MCD",
            "Nike": "NKE",
            "Disney": "DIS"
        }

    def get_stock_data(self, symbol: str, period: str = "1y", market: str = "auto") -> Optional[pd.DataFrame]:
        """주식 데이터 조회"""
        try:
            if market.upper() == "KR":
                # 한국 주식 - FinanceDataReader 사용
                data = fdr.DataReader(symbol, start=self._get_start_date(period))
                if data is not None and not data.empty:
                    data = data.reset_index()
                    # 컬럼명 표준화
                    data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Change']
                    return data
            else:
                # 미국 주식 - yfinance 사용
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period)
                if data is not None and not data.empty:
                    data = data.reset_index()
                    # 컬럼명 표준화
                    data.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Dividends', 'Stock Splits']
                    return data[['Date', 'Open', 'High', 'Low', 'Close', 'Volume']]
                    
        except Exception as e:
            print(f"Error fetching stock data for {symbol}: {str(e)}")
            
        return None

    def get_stock_price_data(self, symbol: str, market: str = "KR") -> Dict:
        """현재 주식 가격 정보 조회"""
        try:
            data = self.get_stock_data(symbol, "5d", market)
            if data is None or data.empty:
                return {"price": 0, "change": 0, "change_percent": 0, "volume": 0}
            
            current_price = data['Close'].iloc[-1]
            prev_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
            change = current_price - prev_price
            change_percent = (change / prev_price * 100) if prev_price > 0 else 0
            volume = data['Volume'].iloc[-1]
            
            return {
                "price": float(current_price),
                "change": float(change),
                "change_percent": float(change_percent),
                "volume": int(volume)
            }
        except Exception as e:
            print(f"Error fetching price data for {symbol}: {str(e)}")
            return {"price": 0, "change": 0, "change_percent": 0, "volume": 0}

    def _get_start_date(self, period: str) -> str:
        """기간을 시작 날짜로 변환"""
        now = datetime.now()
        if period == "1d":
            start = now - timedelta(days=1)
        elif period == "5d":
            start = now - timedelta(days=5)
        elif period == "1mo":
            start = now - timedelta(days=30)
        elif period == "3mo":
            start = now - timedelta(days=90)
        elif period == "6mo":
            start = now - timedelta(days=180)
        elif period == "1y":
            start = now - timedelta(days=365)
        elif period == "2y":
            start = now - timedelta(days=730)
        elif period == "5y":
            start = now - timedelta(days=1825)
        else:
            start = now - timedelta(days=365)  # 기본값
        
        return start.strftime("%Y-%m-%d")

    def search_stocks(self, query: str, market: str = "KR", limit: int = 10) -> List[Dict]:
        """주식 검색"""
        symbols = self.kospi_symbols if market.upper() == "KR" else self.nasdaq_symbols
        results = []
        
        query_lower = query.lower()
        for name, symbol in symbols.items():
            if (query_lower in name.lower() or 
                query_lower in symbol.lower()):
                results.append({
                    "name": name,
                    "symbol": symbol,
                    "display": f"{name} ({symbol})",
                    "market": market.upper()
                })
                
        return results[:limit]

    def get_market_status(self) -> Dict:
        """시장 상태 조회"""
        return {
            "kr_market": {
                "status": "open" if 9 <= datetime.now().hour < 15.5 else "closed",
                "open_time": "09:00",
                "close_time": "15:30",
                "timezone": "Asia/Seoul"
            },
            "us_market": {
                "status": "open" if 9.5 <= datetime.now().hour < 16 else "closed",
                "open_time": "09:30",
                "close_time": "16:00", 
                "timezone": "America/New_York"
            }
        }

    def calculate_technical_indicators(self, data: pd.DataFrame, indicators: str = "all") -> Dict:
        """기술적 지표 계산"""
        if data is None or data.empty:
            return {}
        
        try:
            result = {}
            
            # 이동평균선
            if indicators in ["all", "ma"]:
                result["ma5"] = data['Close'].rolling(5).mean().iloc[-1]
                result["ma20"] = data['Close'].rolling(20).mean().iloc[-1]
                result["ma60"] = data['Close'].rolling(60).mean().iloc[-1]
            
            # RSI (간단 버전)
            if indicators in ["all", "rsi"]:
                delta = data['Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                result["rsi"] = rsi.iloc[-1] if not rsi.empty else 50
            
            # 볼린저 밴드
            if indicators in ["all", "bollinger"]:
                ma20 = data['Close'].rolling(20).mean()
                std20 = data['Close'].rolling(20).std()
                result["bollinger_upper"] = (ma20 + (std20 * 2)).iloc[-1]
                result["bollinger_lower"] = (ma20 - (std20 * 2)).iloc[-1]
                result["bollinger_middle"] = ma20.iloc[-1]
            
            return result
            
        except Exception as e:
            print(f"Error calculating technical indicators: {str(e)}")
            return {}

    def get_popular_stocks(self, market: str = "all", limit: int = 10) -> List[Dict]:
        """인기 주식 목록 조회"""
        try:
            popular_stocks = []
            
            if market.upper() in ["KR", "ALL"]:
                kr_popular = ["삼성전자", "SK하이닉스", "NAVER", "LG화학", "현대차"]
                for name in kr_popular[:limit//2 if market.upper() == "ALL" else limit]:
                    if name in self.kospi_symbols:
                        symbol = self.kospi_symbols[name]
                        price_data = self.get_stock_price_data(symbol, "KR")
                        popular_stocks.append({
                            "name": name,
                            "symbol": symbol,
                            "market": "KR",
                            "price": price_data["price"],
                            "change_percent": price_data["change_percent"]
                        })
            
            if market.upper() in ["US", "ALL"]:
                us_popular = ["Apple", "Microsoft", "Google (Alphabet)", "Amazon", "Tesla"]
                for name in us_popular[:limit//2 if market.upper() == "ALL" else limit]:
                    if name in self.nasdaq_symbols:
                        symbol = self.nasdaq_symbols[name]
                        price_data = self.get_stock_price_data(symbol, "US")
                        popular_stocks.append({
                            "name": name,
                            "symbol": symbol,
                            "market": "US",
                            "price": price_data["price"],
                            "change_percent": price_data["change_percent"]
                        })
            
            return popular_stocks
            
        except Exception as e:
            print(f"Error fetching popular stocks: {str(e)}")
            return []