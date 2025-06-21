import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import redis
import yfinance as yf
from pykrx import stock

logger = logging.getLogger(__name__)


class PykrxStockDataFetcher:
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.cache_timeout = 300  # 5분 캐시
        self.long_cache_timeout = 3600  # 1시간 캐시 (종목 리스트용)

    def _get_cache_key(self, key_type: str, *args) -> str:
        """캐시 키 생성"""
        return f"stock:{key_type}:{':'.join(map(str, args))}"

    def _get_from_cache(self, key: str) -> Optional[dict]:
        """Redis에서 캐시된 데이터 조회"""
        if not self.redis_client:
            return None
        try:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
        return None

    def _set_to_cache(self, key: str, data: dict, timeout: int = None) -> None:
        """Redis에 데이터 캐시"""
        if not self.redis_client:
            return
        try:
            timeout = timeout or self.cache_timeout
            self.redis_client.setex(key, timeout, json.dumps(data, default=str))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")

    def get_market_ticker_list(
        self, market: str = "KOSPI", date: str = None
    ) -> List[Dict[str, str]]:
        """
        시장별 전체 종목 리스트 조회 (pykrx 사용)
        Args:
            market: KOSPI, KOSDAQ, KONEX
            date: 조회 날짜 (YYYYMMDD), None이면 최근 영업일
        Returns:
            List[Dict]: [{"name": "종목명", "symbol": "종목코드"}, ...]
        """
        cache_key = self._get_cache_key("ticker_list", market, date or "latest")

        # 캐시에서 조회
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            # pykrx로 종목 리스트 조회
            if date:
                tickers = stock.get_market_ticker_list(date, market=market)
            else:
                tickers = stock.get_market_ticker_list(market=market)

            # 종목명과 함께 정보 구성
            result = []
            for ticker in tickers:
                try:
                    name = stock.get_market_ticker_name(ticker)
                    if name:  # 종목명이 있는 경우만 추가
                        result.append(
                            {
                                "name": name,
                                "symbol": ticker,
                                "display": f"{name} ({ticker})",
                                "market": market,
                            }
                        )
                    time.sleep(0.1)  # API 호출 제한 방지
                except Exception as e:
                    logger.warning(f"Failed to get name for ticker {ticker}: {e}")
                    continue

            # 캐시에 저장 (종목 리스트는 오래 캐시)
            self._set_to_cache(cache_key, result, self.long_cache_timeout)

            return result

        except Exception as e:
            logger.error(f"Error fetching ticker list for {market}: {e}")
            return []

    def get_market_ohlcv_today(
        self, market: str = "KOSPI", limit: int = 50
    ) -> List[Dict]:
        """
        오늘의 시장 전체 OHLCV 조회 (pykrx 사용)
        Args:
            market: KOSPI, KOSDAQ, KONEX
            limit: 조회할 종목 수 제한
        Returns:
            List[Dict]: 주가 정보 리스트
        """
        cache_key = self._get_cache_key("market_ohlcv", market, limit)

        # 캐시에서 조회
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            # 최근 영업일 계산
            today = datetime.now().strftime("%Y%m%d")

            # pykrx로 전체 시장 OHLCV 조회
            df = stock.get_market_ohlcv(today, market=market)

            if df is None or df.empty:
                # 오늘 데이터가 없으면 어제 데이터 시도
                yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
                df = stock.get_market_ohlcv(yesterday, market=market)

            if df is None or df.empty:
                return []

            # 종목 이름 정보 추가
            result = []
            count = 0
            for ticker, row in df.iterrows():
                if count >= limit:
                    break

                try:
                    name = stock.get_market_ticker_name(ticker)
                    if not name:
                        continue

                    # 등락률 계산
                    close_price = float(row["종가"])
                    open_price = float(row["시가"])
                    change = close_price - open_price
                    change_percent = (
                        (change / open_price * 100) if open_price > 0 else 0
                    )

                    stock_data = {
                        "name": name,
                        "symbol": ticker,
                        "display": f"{name} ({ticker})",
                        "market": market,
                        "price": close_price,
                        "change": change,
                        "change_percent": change_percent,
                        "volume": int(row["거래량"]),
                        "open": float(row["시가"]),
                        "high": float(row["고가"]),
                        "low": float(row["저가"]),
                    }
                    result.append(stock_data)
                    count += 1

                except Exception as e:
                    logger.warning(f"Error processing ticker {ticker}: {e}")
                    continue

            # 캐시에 저장
            self._set_to_cache(cache_key, result)

            return result

        except Exception as e:
            logger.error(f"Error fetching market OHLCV for {market}: {e}")
            return []

    def get_stock_ohlcv(
        self, symbol: str, start_date: str, end_date: str = None, market: str = "KR"
    ) -> Optional[pd.DataFrame]:
        """
        개별 종목 OHLCV 조회
        Args:
            symbol: 종목 코드
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD), None이면 오늘
            market: KR 또는 US
        Returns:
            pd.DataFrame: OHLCV 데이터
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")

        cache_key = self._get_cache_key("ohlcv", symbol, start_date, end_date, market)

        try:
            if market.upper() == "KR":
                # pykrx 사용
                df = stock.get_market_ohlcv(start_date, end_date, symbol)
                if df is not None and not df.empty:
                    # 컬럼명 영어로 변경
                    df.columns = [
                        "Open",
                        "High",
                        "Low",
                        "Close",
                        "Volume",
                        "Amount",
                        "Change",
                    ]
                    df = df[["Open", "High", "Low", "Close", "Volume"]]  # 필요한 컬럼만
                    return df
            else:
                # 미국 주식은 yfinance 사용
                ticker = yf.Ticker(symbol)
                # 날짜 형식 변환
                start = datetime.strptime(start_date, "%Y%m%d").strftime("%Y-%m-%d")
                end = datetime.strptime(end_date, "%Y%m%d").strftime("%Y-%m-%d")
                df = ticker.history(start=start, end=end)
                if df is not None and not df.empty:
                    return df[["Open", "High", "Low", "Close", "Volume"]]

        except Exception as e:
            logger.error(f"Error fetching OHLCV for {symbol}: {e}")

        return None

    def get_popular_stocks(self, market: str = "KR", limit: int = 10) -> List[Dict]:
        """
        인기 종목 조회 (거래대금 상위)
        Args:
            market: KR 또는 US
            limit: 조회할 종목 수
        Returns:
            List[Dict]: 인기 종목 리스트
        """
        cache_key = self._get_cache_key("popular", market, limit)

        # 캐시에서 조회
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            if market.upper() == "KR":
                # KOSPI와 KOSDAQ에서 거래대금 상위 종목 조회
                kospi_data = self.get_market_ohlcv_today("KOSPI", limit // 2)
                kosdaq_data = self.get_market_ohlcv_today("KOSDAQ", limit // 2)

                # 거래대금으로 정렬 (가격 * 거래량)
                all_data = kospi_data + kosdaq_data
                for item in all_data:
                    item["trading_value"] = item["price"] * item["volume"]

                # 거래대금 상위로 정렬
                sorted_data = sorted(
                    all_data, key=lambda x: x["trading_value"], reverse=True
                )
                result = sorted_data[:limit]

            else:
                # 미국 주식 인기 종목 (고정 리스트)
                us_symbols = [
                    "AAPL",
                    "MSFT",
                    "GOOGL",
                    "AMZN",
                    "TSLA",
                    "META",
                    "NVDA",
                    "NFLX",
                    "AMD",
                    "INTC",
                ]
                result = []
                for symbol in us_symbols[:limit]:
                    try:
                        ticker = yf.Ticker(symbol)
                        hist = ticker.history(period="2d")
                        if not hist.empty:
                            current_price = float(hist["Close"].iloc[-1])
                            prev_price = (
                                float(hist["Close"].iloc[-2])
                                if len(hist) > 1
                                else current_price
                            )
                            change = current_price - prev_price
                            change_percent = (
                                (change / prev_price * 100) if prev_price > 0 else 0
                            )

                            result.append(
                                {
                                    "name": symbol,
                                    "symbol": symbol,
                                    "market": "US",
                                    "price": current_price,
                                    "change": change,
                                    "change_percent": change_percent,
                                    "volume": int(hist["Volume"].iloc[-1]),
                                    "trading_value": current_price
                                    * hist["Volume"].iloc[-1],
                                }
                            )
                    except Exception as e:
                        logger.warning(f"Error fetching US stock {symbol}: {e}")

            # 캐시에 저장
            self._set_to_cache(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"Error fetching popular stocks for {market}: {e}")
            return []

    def search_stocks(
        self, query: str, market: str = "KR", limit: int = 20
    ) -> List[Dict]:
        """
        종목 검색
        Args:
            query: 검색어
            market: KR 또는 US
            limit: 결과 수 제한
        Returns:
            List[Dict]: 검색 결과
        """
        try:
            if market.upper() == "KR":
                # KOSPI와 KOSDAQ에서 검색
                kospi_list = self.get_market_ticker_list("KOSPI")
                kosdaq_list = self.get_market_ticker_list("KOSDAQ")
                all_stocks = kospi_list + kosdaq_list
            else:
                # 미국 주식은 제한된 리스트에서 검색
                us_symbols = {
                    "AAPL": "Apple Inc.",
                    "MSFT": "Microsoft Corporation",
                    "GOOGL": "Alphabet Inc.",
                    "AMZN": "Amazon.com Inc.",
                    "TSLA": "Tesla Inc.",
                    "META": "Meta Platforms Inc.",
                    "NVDA": "NVIDIA Corporation",
                    "NFLX": "Netflix Inc.",
                    "AMD": "Advanced Micro Devices",
                    "INTC": "Intel Corporation",
                }
                all_stocks = [
                    {
                        "name": name,
                        "symbol": symbol,
                        "display": f"{name} ({symbol})",
                        "market": "US",
                    }
                    for symbol, name in us_symbols.items()
                ]

            # 검색 수행
            query_lower = query.lower()
            results = []
            for stock in all_stocks:
                if (
                    query_lower in stock["name"].lower()
                    or query_lower in stock["symbol"].lower()
                ):
                    results.append(stock)
                    if len(results) >= limit:
                        break

            return results

        except Exception as e:
            logger.error(f"Error searching stocks: {e}")
            return []

    def get_market_status(self) -> Dict:
        """시장 상태 조회"""
        now = datetime.now()

        # 한국 시장 (09:00-15:30)
        kr_open = now.replace(hour=9, minute=0, second=0, microsecond=0)
        kr_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        kr_status = "open" if kr_open <= now <= kr_close else "closed"

        # 미국 시장 (현지시간 09:30-16:00, UTC 기준으로 계산)
        us_status = "open" if 14 <= now.hour < 21 else "closed"  # 대략적인 계산

        return {
            "kr_market": {
                "status": kr_status,
                "open_time": "09:00",
                "close_time": "15:30",
                "timezone": "Asia/Seoul",
            },
            "us_market": {
                "status": us_status,
                "open_time": "09:30",
                "close_time": "16:00",
                "timezone": "America/New_York",
            },
        }
