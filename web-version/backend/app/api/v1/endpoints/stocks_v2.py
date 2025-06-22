"""
주식 관련 API 엔드포인트 v2 (pykrx 사용)
"""

from app.core.redis_client import RedisClient
from app.data.pykrx_stock_data import PykrxStockDataFetcher
from fastapi import APIRouter, Depends, HTTPException, Query

router = APIRouter()


def get_stock_fetcher() -> PykrxStockDataFetcher:
    """스톡 데이터 페처 의존성"""
    redis_client = RedisClient.get_instance()
    return PykrxStockDataFetcher(redis_client=redis_client)


@router.get("/market/tickers/{market}")
async def get_market_tickers(
    market: str,
    page: int = Query(default=1, ge=1, description="페이지 번호 (1부터 시작)"),
    limit: int = Query(default=50, ge=1, le=500, description="페이지당 종목 수"),
    stock_fetcher: PykrxStockDataFetcher = Depends(get_stock_fetcher),
):
    """
    시장별 전체 종목 리스트 조회 (페이지네이션)
    Args:
        market: KOSPI, KOSDAQ, KONEX, US
        page: 페이지 번호
        limit: 페이지당 종목 수
    """
    try:
        if market.upper() in ["KOSPI", "KOSDAQ", "KONEX"]:
            # 한국 주식
            all_tickers = stock_fetcher.get_market_ticker_list(market.upper())
        elif market.upper() == "US":
            # 미국 주식 (제한된 리스트)
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
                "JPM": "JPMorgan Chase",
                "V": "Visa Inc.",
                "MA": "Mastercard",
                "UNH": "UnitedHealth Group",
                "JNJ": "Johnson & Johnson",
                "PG": "Procter & Gamble",
                "HD": "Home Depot",
                "DIS": "Walt Disney",
                "BAC": "Bank of America",
                "XOM": "ExxonMobil",
            }
            all_tickers = [
                {
                    "name": name,
                    "symbol": symbol,
                    "display": f"{name} ({symbol})",
                    "market": "US",
                }
                for symbol, name in us_symbols.items()
            ]
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 시장입니다")

        # 페이지네이션 계산
        total_count = len(all_tickers)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_tickers = all_tickers[start_idx:end_idx]

        return {
            "market": market.upper(),
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": (total_count + limit - 1) // limit,
            "tickers": paginated_tickers,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"종목 리스트 조회 중 오류 발생: {str(e)}"
        )


@router.get("/market/prices/{market}")
async def get_market_prices_v2(
    market: str,
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=20, ge=1, le=100, description="페이지당 종목 수"),
    stock_fetcher: PykrxStockDataFetcher = Depends(get_stock_fetcher),
):
    """
    시장별 실시간 주가 정보 조회 (페이지네이션)
    Args:
        market: KOSPI, KOSDAQ, KONEX, US
        page: 페이지 번호
        limit: 페이지당 종목 수
    """
    try:
        if market.upper() in ["KOSPI", "KOSDAQ", "KONEX"]:
            # pykrx로 오늘의 시장 OHLCV 조회
            all_stocks = stock_fetcher.get_market_ohlcv_today(
                market.upper(), limit * 10
            )  # 충분히 가져온 후 페이지네이션
        elif market.upper() == "US":
            # 미국 주식 인기 종목
            all_stocks = stock_fetcher.get_popular_stocks("US", limit * 5)
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 시장입니다")

        # 페이지네이션 적용
        total_count = len(all_stocks)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_stocks = all_stocks[start_idx:end_idx]

        return {
            "market": market.upper(),
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": (total_count + limit - 1) // limit,
            "stocks": paginated_stocks,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"시장 가격 조회 중 오류 발생: {str(e)}"
        )


@router.get("/search")
async def search_stocks_v2(
    query: str = Query(..., min_length=1, max_length=100, description="검색어"),
    market: str = Query("ALL", description="시장 (KOSPI/KOSDAQ/US/ALL)"),
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=20, ge=1, le=100, description="페이지당 결과 수"),
    stock_fetcher: PykrxStockDataFetcher = Depends(get_stock_fetcher),
):
    """
    종목 검색 (페이지네이션)
    Args:
        query: 검색어 (종목명 또는 종목코드)
        market: 검색할 시장
        page: 페이지 번호
        limit: 페이지당 결과 수
    """
    try:
        all_results = []

        if market.upper() in ["ALL", "KOSPI"]:
            kospi_results = stock_fetcher.search_stocks(query, "KR", limit * 2)
            # KOSPI 종목만 필터링
            for result in kospi_results:
                tickers = stock_fetcher.get_market_ticker_list("KOSPI")
                kospi_symbols = [t["symbol"] for t in tickers]
                if result["symbol"] in kospi_symbols:
                    result["market"] = "KOSPI"
                    all_results.append(result)

        if market.upper() in ["ALL", "KOSDAQ"]:
            kosdaq_results = stock_fetcher.search_stocks(query, "KR", limit * 2)
            # KOSDAQ 종목만 필터링
            for result in kosdaq_results:
                tickers = stock_fetcher.get_market_ticker_list("KOSDAQ")
                kosdaq_symbols = [t["symbol"] for t in tickers]
                if result["symbol"] in kosdaq_symbols:
                    result["market"] = "KOSDAQ"
                    all_results.append(result)

        if market.upper() in ["ALL", "US"]:
            us_results = stock_fetcher.search_stocks(query, "US", limit)
            all_results.extend(us_results)

        # 중복 제거
        seen = set()
        unique_results = []
        for result in all_results:
            key = f"{result['symbol']}_{result.get('market', 'KR')}"
            if key not in seen:
                seen.add(key)
                unique_results.append(result)

        # 페이지네이션 적용
        total_count = len(unique_results)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_results = unique_results[start_idx:end_idx]

        return {
            "query": query,
            "market": market.upper(),
            "page": page,
            "limit": limit,
            "total_count": total_count,
            "total_pages": (total_count + limit - 1) // limit,
            "results": paginated_results,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")


@router.get("/data/{symbol}")
async def get_stock_data_v2(
    symbol: str,
    market: str = Query(..., description="시장 (KOSPI/KOSDAQ/US)"),
    period: str = Query(
        default="1y", description="조회 기간 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y)"
    ),
    stock_fetcher: PykrxStockDataFetcher = Depends(get_stock_fetcher),
):
    """
    개별 종목 상세 데이터 조회
    Args:
        symbol: 종목 코드
        market: 시장 구분
        period: 조회 기간
    """
    try:
        from datetime import datetime, timedelta

        # 기간에 따른 시작일 계산
        period_map = {
            "1d": 1,
            "5d": 5,
            "1mo": 30,
            "3mo": 90,
            "6mo": 180,
            "1y": 365,
            "2y": 730,
            "5y": 1825,
        }
        days = period_map.get(period, 365)
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        end_date = datetime.now().strftime("%Y%m%d")

        # OHLCV 데이터 조회
        market_code = "KR" if market.upper() in ["KOSPI", "KOSDAQ"] else "US"
        df = stock_fetcher.get_stock_ohlcv(symbol, start_date, end_date, market_code)

        if df is None or df.empty:
            raise HTTPException(
                status_code=404, detail=f"종목 데이터를 찾을 수 없습니다: {symbol}"
            )

        # 현재 가격 정보
        current_price = float(df["Close"].iloc[-1])
        prev_price = float(df["Close"].iloc[-2]) if len(df) > 1 else current_price
        change = current_price - prev_price
        change_percent = (change / prev_price * 100) if prev_price > 0 else 0

        # 차트 데이터 준비
        chart_data = []
        for idx, row in df.iterrows():
            chart_data.append(
                {
                    "date": (
                        idx.strftime("%Y-%m-%d")
                        if hasattr(idx, "strftime")
                        else str(idx)
                    ),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                }
            )

        return {
            "symbol": symbol,
            "market": market.upper(),
            "period": period,
            "current_price": current_price,
            "change": change,
            "change_percent": change_percent,
            "volume": int(df["Volume"].iloc[-1]),
            "chart_data": chart_data[-min(len(chart_data), 500)],  # 최대 500개 포인트
            "data_points": len(chart_data),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"종목 데이터 조회 중 오류 발생: {str(e)}"
        )


@router.get("/popular")
async def get_popular_stocks_v2(
    market: str = Query("ALL", description="시장 (KOSPI/KOSDAQ/US/ALL)"),
    limit: int = Query(default=10, ge=1, le=50, description="결과 수 제한"),
    stock_fetcher: PykrxStockDataFetcher = Depends(get_stock_fetcher),
):
    """
    인기 종목 조회 (거래대금 기준)
    Args:
        market: 조회할 시장
        limit: 결과 수 제한
    """
    try:
        all_popular = []

        if market.upper() in ["ALL", "KOSPI", "KR"]:
            kr_popular = stock_fetcher.get_popular_stocks("KR", limit)
            all_popular.extend(kr_popular)

        if market.upper() in ["ALL", "US"]:
            us_popular = stock_fetcher.get_popular_stocks(
                "US", limit // 2 if market.upper() == "ALL" else limit
            )
            all_popular.extend(us_popular)

        # 거래대금으로 정렬
        if "trading_value" in all_popular[0] if all_popular else {}:
            all_popular.sort(key=lambda x: x.get("trading_value", 0), reverse=True)

        return {"market": market.upper(), "stocks": all_popular[:limit]}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"인기 종목 조회 중 오류 발생: {str(e)}"
        )


@router.get("/detail/{symbol}")
async def get_stock_detail_info(
    symbol: str,
    market: str = Query(..., description="시장 (KOSPI/KOSDAQ/US)"),
    stock_fetcher: PykrxStockDataFetcher = Depends(get_stock_fetcher),
):
    """
    상세 주식 정보 조회
    Args:
        symbol: 종목 코드
        market: 시장 구분
    Returns:
        상세 주식 정보 (전일종가, 일일변동폭, 52주 변동폭, 시가총액, 평균거래량 등)
    """
    try:
        import pandas as pd
        from datetime import datetime, timedelta
        from pykrx import stock
        
        today = datetime.now().strftime("%Y%m%d")
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        
        market_code = "KR" if market.upper() in ["KOSPI", "KOSDAQ"] else "US"
        
        if market_code == "KR":
            # 한국 주식 상세 정보
            
            # 1년간 OHLCV 데이터
            df = stock_fetcher.get_stock_ohlcv(symbol, one_year_ago, today, "KR")
            if df is None or df.empty:
                raise HTTPException(status_code=404, detail=f"종목 데이터를 찾을 수 없습니다: {symbol}")
            
            # 기본 가격 정보
            current_close = float(df["Close"].iloc[-1])
            previous_close = float(df["Close"].iloc[-2]) if len(df) > 1 else current_close
            current_high = float(df["High"].iloc[-1])
            current_low = float(df["Low"].iloc[-1])
            current_volume = int(df["Volume"].iloc[-1])
            
            # 52주 최고가/최저가
            year_high = float(df["High"].max())
            year_low = float(df["Low"].min())
            
            # 평균 거래량 (20일)
            avg_volume_20d = int(df["Volume"].tail(20).mean()) if len(df) >= 20 else current_volume
            
            # 일일 변동폭
            daily_range_low = current_low
            daily_range_high = current_high
            
            # 시가총액 조회 시도
            market_cap = None
            try:
                # pykrx를 통한 시가총액 조회
                market_str = "KOSPI" if market.upper() == "KOSPI" else "KOSDAQ"
                market_cap_data = stock.get_market_cap_by_date(today, today, market_str)
                if not market_cap_data.empty and symbol in market_cap_data.index:
                    market_cap = int(market_cap_data.loc[symbol, "시가총액"]) if "시가총액" in market_cap_data.columns else None
            except Exception:
                market_cap = None
            
            # PER/PBR 조회 시도
            per, pbr = None, None
            try:
                fundamental_data = stock.get_market_fundamental_by_date(today, today, market_str)
                if not fundamental_data.empty and symbol in fundamental_data.index:
                    per = float(fundamental_data.loc[symbol, "PER"]) if "PER" in fundamental_data.columns else None
                    pbr = float(fundamental_data.loc[symbol, "PBR"]) if "PBR" in fundamental_data.columns else None
            except Exception:
                per, pbr = None, None
            
            return {
                "symbol": symbol,
                "market": market.upper(),
                "basic_info": {
                    "current_price": current_close,
                    "previous_close": previous_close,
                    "change": current_close - previous_close,
                    "change_percent": ((current_close - previous_close) / previous_close * 100) if previous_close > 0 else 0,
                },
                "price_ranges": {
                    "daily_low": daily_range_low,
                    "daily_high": daily_range_high,
                    "daily_range": f"₩{daily_range_low:,.0f} - ₩{daily_range_high:,.0f}",
                    "year_low": year_low,
                    "year_high": year_high,
                    "week_52_range": f"₩{year_low:,.0f} - ₩{year_high:,.0f}",
                },
                "trading_info": {
                    "current_volume": current_volume,
                    "avg_volume_20d": avg_volume_20d,
                    "volume_ratio": (current_volume / avg_volume_20d) if avg_volume_20d > 0 else 1.0,
                },
                "financial_metrics": {
                    "market_cap": market_cap,
                    "market_cap_formatted": f"{market_cap/1000000000000:.2f}조 KRW" if market_cap else "N/A",
                    "per": per,
                    "pbr": pbr,
                    "dividend_yield": None,  # pykrx에서 직접 지원 안함
                },
                "last_updated": today
            }
            
        else:
            # 미국 주식 - 제한된 정보만 제공
            df = stock_fetcher.get_stock_ohlcv(symbol, one_year_ago, today, "US")
            if df is None or df.empty:
                raise HTTPException(status_code=404, detail=f"종목 데이터를 찾을 수 없습니다: {symbol}")
            
            current_close = float(df["Close"].iloc[-1])
            previous_close = float(df["Close"].iloc[-2]) if len(df) > 1 else current_close
            current_high = float(df["High"].iloc[-1])
            current_low = float(df["Low"].iloc[-1])
            current_volume = int(df["Volume"].iloc[-1])
            
            year_high = float(df["High"].max())
            year_low = float(df["Low"].min())
            avg_volume_20d = int(df["Volume"].tail(20).mean()) if len(df) >= 20 else current_volume
            
            return {
                "symbol": symbol,
                "market": market.upper(),
                "basic_info": {
                    "current_price": current_close,
                    "previous_close": previous_close,
                    "change": current_close - previous_close,
                    "change_percent": ((current_close - previous_close) / previous_close * 100) if previous_close > 0 else 0,
                },
                "price_ranges": {
                    "daily_low": current_low,
                    "daily_high": current_high,
                    "daily_range": f"${current_low:.2f} - ${current_high:.2f}",
                    "year_low": year_low,
                    "year_high": year_high,
                    "week_52_range": f"${year_low:.2f} - ${year_high:.2f}",
                },
                "trading_info": {
                    "current_volume": current_volume,
                    "avg_volume_20d": avg_volume_20d,
                    "volume_ratio": (current_volume / avg_volume_20d) if avg_volume_20d > 0 else 1.0,
                },
                "financial_metrics": {
                    "market_cap": None,
                    "market_cap_formatted": "N/A",
                    "per": None,
                    "pbr": None,
                    "dividend_yield": None,
                },
                "last_updated": today
            }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"상세 주식 정보 조회 중 오류 발생: {str(e)}"
        )


@router.get("/market/status")
async def get_market_status_v2(
    stock_fetcher: PykrxStockDataFetcher = Depends(get_stock_fetcher),
):
    """시장 상태 정보"""
    try:
        return stock_fetcher.get_market_status()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"시장 상태 조회 중 오류 발생: {str(e)}"
        )
