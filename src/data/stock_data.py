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
        try:
            kospi_companies = fdr.StockListing("KOSPI")
            return dict(zip(kospi_companies["Name"], kospi_companies["Code"]))
        except Exception:
            return {
                "삼성전자": "005930",
                "SK하이닉스": "000660",
                "NAVER": "035420",
                "LG화학": "051910",
                "KB금융": "105560",
            }

    def _get_popular_nasdaq_symbols(self) -> Dict[str, str]:
        return {
            "Apple": "AAPL",
            "Microsoft": "MSFT",
            "Amazon": "AMZN",
            "Google": "GOOGL",
            "Tesla": "TSLA",
            "Meta": "META",
            "Netflix": "NFLX",
            "NVIDIA": "NVDA",
            "AMD": "AMD",
            "Intel": "INTC",
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
        results = []
        if market == "KR":
            for name, code in self.kospi_symbols.items():
                if query.lower() in name.lower() or query.upper() in code:
                    results.append({"name": name, "symbol": code})
        else:
            for name, symbol in self.nasdaq_symbols.items():
                if query.lower() in name.lower() or query.upper() in symbol:
                    results.append({"name": name, "symbol": symbol})
        return results[:10]
