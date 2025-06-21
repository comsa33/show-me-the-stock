from datetime import datetime, timedelta
from typing import Dict, List, Optional

import FinanceDataReader as fdr
import pandas as pd
import streamlit as st
import yfinance as yf


class StockDataFetcher:
    def __init__(self):
        self.kospi_symbols = self._get_kospi_symbols()
        self.nasdaq_symbols = self._get_popular_nasdaq_symbols()

    def _get_kospi_symbols(self) -> Dict[str, str]:
        """한국 주식 데이터 가져오기 (안정성 개선)"""
        # 기본 주식 목록 (백업)
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
            "롯데케미칼": "051910",
            "LG전자": "066570",
            "삼성바이오로직스": "207940",
            "SK텔레콤": "017670",
            "CJ제일제당": "097950",
            "대한항공": "003490",
            "신한지주회사": "055550",
            "하나금융지주": "086790",
            "카카오": "035720",
            "KB국민은행": "105560",
            "대우조선해양": "042660",
            "에코프로비엠": "086520"
        }
        
        try:
            # 우선 기본 주식만 사용하도록 수정
            # FinanceDataReader API가 불안정한 경우가 많음
            return default_stocks
            
            # 나중에 API가 안정되면 아래 코드 사용 가능
            # kospi_companies = fdr.StockListing("KOSPI")
            # kosdaq_companies = fdr.StockListing("KOSDAQ")
            # all_companies = pd.concat([kospi_companies, kosdaq_companies], ignore_index=True)
            # all_companies = all_companies.drop_duplicates(subset=['Code'])
            # all_companies = all_companies.dropna(subset=['Name', 'Code'])
            # result = dict(zip(all_companies["Name"], all_companies["Code"]))
            # return result
            
        except Exception as e:
            print(f"KOSPI 데이터 로드 실패: {e}")
            return default_stocks

    def _get_popular_nasdaq_symbols(self) -> Dict[str, str]:
        """미국 주식 데이터 가져오기 (확장된 목록)"""
        return {
            # Tech Giants (FAANG+)
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
            
            # Financial Services
            "Berkshire Hathaway": "BRK-B",
            "JPMorgan Chase": "JPM",
            "Visa": "V",
            "Mastercard": "MA",
            "Bank of America": "BAC",
            "Wells Fargo": "WFC",
            "Goldman Sachs": "GS",
            "American Express": "AXP",
            
            # Healthcare & Pharma
            "Johnson & Johnson": "JNJ",
            "UnitedHealth": "UNH",
            "Pfizer": "PFE",
            "Moderna": "MRNA",
            "AbbVie": "ABBV",
            "Merck": "MRK",
            "Eli Lilly": "LLY",
            
            # Consumer & Retail
            "Procter & Gamble": "PG",
            "Coca-Cola": "KO",
            "PepsiCo": "PEP",
            "Walmart": "WMT",
            "Home Depot": "HD",
            "McDonald's": "MCD",
            "Nike": "NKE",
            "Starbucks": "SBUX",
            "Target": "TGT",
            
            # Communications
            "Disney": "DIS",
            "Verizon": "VZ",
            "AT&T": "T",
            "Comcast": "CMCSA",
            
            # Technology (Others)
            "IBM": "IBM",
            "Oracle": "ORCL",
            "Salesforce": "CRM",
            "Adobe": "ADBE",
            "Cisco": "CSCO",
            "Qualcomm": "QCOM",
            
            # Growth & New Economy
            "PayPal": "PYPL",
            "Zoom": "ZM",
            "Uber": "UBER",
            "Airbnb": "ABNB",
            "Spotify": "SPOT",
            "Pinterest": "PINS",
            "Snapchat": "SNAP",
            "Square (Block)": "SQ",
            "Palantir": "PLTR",
            "CrowdStrike": "CRWD",
            "Snowflake": "SNOW",
            
            # Energy & Industrial
            "ExxonMobil": "XOM",
            "Chevron": "CVX",
            "General Electric": "GE",
            "Boeing": "BA",
            "Caterpillar": "CAT",
            
            # ETFs (Popular)
            "SPDR S&P 500": "SPY",
            "Invesco QQQ": "QQQ",
            "iShares Core S&P 500": "IVV",
        }

    @st.cache_data(ttl=300)
    def get_stock_data(
        _self, symbol: str, period: str = "1y", market: str = "US"
    ) -> Optional[pd.DataFrame]:
        try:
            if market == "KR":
                if symbol in _self.kospi_symbols.values():
                    data = fdr.DataReader(
                        symbol, start=datetime.now() - timedelta(days=365)
                    )
                else:
                    return None
            else:
                ticker = yf.Ticker(symbol)
                data = ticker.history(period=period)

            if data.empty:
                return None

            data.reset_index(inplace=True)
            if "Date" not in data.columns and "Datetime" not in data.columns:
                data.reset_index(inplace=True)

            return data
        except Exception as e:
            st.error(f"데이터 가져오기 오류: {str(e)}")
            return None

    @st.cache_data(ttl=300)
    def get_multiple_stocks(
        _self, symbols: List[str], period: str = "1y", market: str = "US"
    ) -> Dict[str, pd.DataFrame]:
        results = {}
        for symbol in symbols:
            data = _self.get_stock_data(symbol, period, market)
            if data is not None:
                results[symbol] = data
        return results

    def get_real_time_price(self, symbol: str, market: str = "US") -> Optional[float]:
        try:
            if market == "KR":
                data = fdr.DataReader(symbol, start=datetime.now().strftime("%Y-%m-%d"))
                if not data.empty:
                    return data["Close"].iloc[-1]
            else:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                return info.get("currentPrice") or info.get("regularMarketPrice")
        except Exception:
            return None

    def search_stock(self, query: str, market: str = "US") -> List[Dict[str, str]]:
        """주식 검색 기능 - 더 정교한 검색 로직"""
        results = []
        query_lower = query.lower().strip()
        
        if not query_lower or len(query_lower) < 1:
            return results
        
        if market == "KR":
            symbols_dict = self.kospi_symbols
        else:
            symbols_dict = self.nasdaq_symbols
            
        # 검색 로직 개선
        for name, symbol in symbols_dict.items():
            name_lower = name.lower()
            symbol_upper = symbol.upper()
            query_upper = query.upper()
            
            # 정확한 매칭부터 부분 매칭까지
            score = 0
            
            # 심볼 정확 매칭 (최고 점수)
            if symbol_upper == query_upper:
                score = 100
            # 심볼 시작 매칭
            elif symbol_upper.startswith(query_upper):
                score = 90
            # 이름 정확 매칭
            elif name_lower == query_lower:
                score = 85
            # 이름 시작 매칭
            elif name_lower.startswith(query_lower):
                score = 80
            # 심볼 포함
            elif query_upper in symbol_upper:
                score = 70
            # 이름 포함
            elif query_lower in name_lower:
                score = 60
            # 단어 경계 매칭
            elif any(word.startswith(query_lower) for word in name_lower.split()):
                score = 50
                
            if score > 0:
                results.append({
                    "name": name, 
                    "symbol": symbol, 
                    "score": score,
                    "display": f"{name} ({symbol})"
                })
        
        # 점수순으로 정렬하고 상위 50개만 반환
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:50]
    
    def get_stock_suggestions(self, market: str = "US", limit: int = 20) -> List[Dict[str, str]]:
        """인기 주식 추천 목록"""
        if market == "KR":
            # 한국 인기 주식
            popular_names = [
                "삼성전자", "SK하이닉스", "NAVER", "LG화학", "KB금융",
                "LG에너지솔루션", "Celltrion", "삼성SDI", "SK아이이기술", "HMM",
                "현대차", "POSCO홀딩스", "기아", "LG전자", "삼성바이오로직스",
                "SK텔레콤", "CJ제일제당", "대한항공", "카카오", "대우조선해양"
            ]
            symbols_dict = self.kospi_symbols
        else:
            # 미국 인기 주식
            popular_names = [
                "Apple", "Microsoft", "Amazon", "Google (Alphabet)", "Tesla",
                "Meta (Facebook)", "NVIDIA", "Netflix", "AMD", "Intel",
                "Berkshire Hathaway", "JPMorgan Chase", "Visa", "Mastercard", "Coca-Cola",
                "Disney", "Nike", "McDonald's", "PayPal", "Uber"
            ]
            symbols_dict = self.nasdaq_symbols
            
        results = []
        for name in popular_names:
            if name in symbols_dict:
                results.append({
                    "name": name,
                    "symbol": symbols_dict[name],
                    "display": f"{name} ({symbols_dict[name]})"
                })
                if len(results) >= limit:
                    break
                    
        return results
