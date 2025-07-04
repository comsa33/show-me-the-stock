"""
주식 관련 API 엔드포인트
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from app.data.stock_data import StockDataFetcher
from app.core.cache import cache_manager
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()

# 전역 스톡 데이터 페처 인스턴스
stock_fetcher = StockDataFetcher()

# 캐시 TTL 설정 (24시간)
CACHE_TTL_24H = 86400


@router.get("/prices/{market}")
async def get_stock_prices(
    market: str,
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=20, ge=1, le=100, description="페이지당 종목 수"),
):
    """시장별 주식 목록 조회 (페이지네이션)"""
    try:
        # 새로운 페이지네이션 API 사용
        result = stock_fetcher.get_paginated_stocks(market, page, limit)
        
        # 실시간 가격 정보 추가 (실제 데이터)
        for stock in result["stocks"]:
            price_info = stock_fetcher.get_real_time_price(stock["symbol"], stock["market"])
            stock.update({
                "price": price_info["price"],
                "change": price_info["change"],
                "change_percent": price_info["change_percent"],
                "volume": price_info["volume"],
                "data_source": price_info.get("data_source", "unknown"),
                "timestamp": price_info.get("timestamp")
            })
        
        return {
            "market": market.upper(),
            "page": result["page"],
            "total_pages": result["total_pages"], 
            "total_count": result["total_count"],
            "limit": result["limit"],
            "stocks": result["stocks"]
        }

    except Exception as e:
        logger.error(f"주식 목록 조회 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500, detail=f"주식 목록 조회 중 오류 발생: {str(e)}"
        )


@router.get("/all/{market}")
async def get_all_stocks(
    market: str,
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=50, ge=1, le=200, description="페이지당 종목 수"),
):
    """전체 종목 리스트 조회 (페이지네이션)"""
    try:
        if market.upper() == "KR":
            all_stocks = stock_fetcher.get_all_kr_stocks()
        elif market.upper() == "US":
            all_stocks = stock_fetcher.get_all_us_stocks()
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 시장입니다 (KR/US)")
        
        # 페이지네이션 계산
        total_count = len(all_stocks)
        total_pages = (total_count + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        paginated_stocks = all_stocks[start_idx:end_idx]
        
        return {
            "market": market.upper(),
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "limit": limit,
            "stocks": paginated_stocks
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"전체 종목 조회 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500, detail=f"전체 종목 조회 중 오류 발생: {str(e)}"
        )


@router.get("/kospi")
async def get_kospi_stocks(
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=50, ge=1, le=200, description="페이지당 종목 수"),
):
    """KOSPI 종목 조회"""
    try:
        all_stocks = stock_fetcher.get_all_kospi_stocks()
        
        # 페이지네이션 계산
        total_count = len(all_stocks)
        total_pages = (total_count + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        paginated_stocks = all_stocks[start_idx:end_idx]
        
        return {
            "market": "KOSPI",
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "limit": limit,
            "stocks": paginated_stocks
        }

    except Exception as e:
        logger.error(f"KOSPI 종목 조회 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500, detail=f"KOSPI 종목 조회 중 오류 발생: {str(e)}"
        )


@router.get("/kosdaq")
async def get_kosdaq_stocks(
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=50, ge=1, le=200, description="페이지당 종목 수"),
):
    """KOSDAQ 종목 조회"""
    try:
        all_stocks = stock_fetcher.get_all_kosdaq_stocks()
        
        # 페이지네이션 계산
        total_count = len(all_stocks)
        total_pages = (total_count + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        paginated_stocks = all_stocks[start_idx:end_idx]
        
        return {
            "market": "KOSDAQ",
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "limit": limit,
            "stocks": paginated_stocks
        }

    except Exception as e:
        logger.error(f"KOSDAQ 종목 조회 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500, detail=f"KOSDAQ 종목 조회 중 오류 발생: {str(e)}"
        )


@router.get("/data/{symbol}")
async def get_stock_data(
    symbol: str,
    market: str = Query(..., description="시장 (KR/US)"),
    period: str = Query(default="1y", description="조회 기간"),
):
    """개별 주식 데이터 조회"""
    try:
        # 주식 데이터 조회
        data = stock_fetcher.get_stock_data(symbol, period, market)
        if data is None or data.empty:
            raise HTTPException(
                status_code=404, detail=f"주식 데이터를 찾을 수 없습니다: {symbol}"
            )

        # 현재 가격 정보
        current_price = float(data['Close'].iloc[-1])
        
        # 차트 데이터 준비
        chart_data = []
        for idx, row in data.iterrows():
            chart_data.append({
                "Date": idx.strftime('%Y-%m-%d') if hasattr(idx, 'strftime') else str(idx),
                "Open": float(row['Open']),
                "High": float(row['High']),
                "Low": float(row['Low']),
                "Close": float(row['Close']),
                "Volume": int(row['Volume'])
            })

        return {
            "symbol": symbol,
            "market": market.upper(),
            "period": period,
            "current_price": current_price,
            "data": chart_data,
            "data_points": len(chart_data)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"주식 데이터 조회 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500, detail=f"주식 데이터 조회 중 오류 발생: {str(e)}"
        )


@router.get("/search")
async def search_stocks(
    query: str = Query(..., min_length=1, description="검색어"),
    market: str = Query(default="ALL", description="시장 (KR/US/ALL)"),
    page: int = Query(default=1, ge=1, description="페이지 번호"),
    limit: int = Query(default=20, ge=1, le=100, description="페이지당 결과 수"),
):
    """종목 검색"""
    try:
        all_results = []
        
        if market.upper() in ["ALL", "KR"]:
            kr_stocks = stock_fetcher.get_all_kr_stocks()
            for stock in kr_stocks:
                if (query.lower() in stock["name"].lower() or 
                    query.lower() in stock["symbol"].lower()):
                    all_results.append(stock)
        
        if market.upper() in ["ALL", "US"]:
            us_stocks = stock_fetcher.get_all_us_stocks()
            for stock in us_stocks:
                if (query.lower() in stock["name"].lower() or 
                    query.lower() in stock["symbol"].lower()):
                    all_results.append(stock)
        
        # 페이지네이션 적용
        total_count = len(all_results)
        total_pages = (total_count + limit - 1) // limit
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        
        paginated_results = all_results[start_idx:end_idx]
        
        return {
            "query": query,
            "market": market.upper(),
            "page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "limit": limit,
            "results": paginated_results
        }

    except Exception as e:
        logger.error(f"종목 검색 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500, detail=f"종목 검색 중 오류 발생: {str(e)}"
        )


@router.get("/popular/{market}")
async def get_popular_stocks(
    market: str,
    limit: int = Query(default=10, ge=1, le=50, description="결과 수 제한"),
):
    """인기 종목 조회"""
    try:
        if market.upper() == "KR":
            # 한국 대형주 위주로 반환
            popular_symbols = [
                "005930", "000660", "035420", "051910", "373220",
                "068270", "006400", "005380", "005490", "000270"
            ]
            all_kr_stocks = stock_fetcher.get_all_kr_stocks()
            popular_stocks = []
            
            for stock in all_kr_stocks:
                if stock["symbol"] in popular_symbols:
                    # 실시간 가격 정보 추가
                    price_info = stock_fetcher.get_real_time_price(stock["symbol"], "KR")
                    stock.update({
                        "price": price_info["price"],
                        "change": price_info["change"],
                        "change_percent": price_info["change_percent"],
                        "volume": price_info["volume"]
                    })
                    popular_stocks.append(stock)
                
                if len(popular_stocks) >= limit:
                    break
                    
        elif market.upper() == "US":
            # 미국 대형주 위주로 반환
            popular_symbols = [
                "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
                "META", "NVDA", "NFLX", "AMD", "INTC"
            ]
            all_us_stocks = stock_fetcher.get_all_us_stocks()
            popular_stocks = []
            
            for stock in all_us_stocks:
                if stock["symbol"] in popular_symbols:
                    # 실시간 가격 정보 추가
                    price_info = stock_fetcher.get_real_time_price(stock["symbol"], "US")
                    stock.update({
                        "price": price_info["price"],
                        "change": price_info["change"],
                        "change_percent": price_info["change_percent"],
                        "volume": price_info["volume"]
                    })
                    popular_stocks.append(stock)
                
                if len(popular_stocks) >= limit:
                    break
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 시장입니다 (KR/US)")
        
        return {
            "market": market.upper(),
            "stocks": popular_stocks
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인기 종목 조회 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500, detail=f"인기 종목 조회 중 오류 발생: {str(e)}"
        )


@router.get("/list/simple")
async def get_simple_stock_list(
    market: str = Query(..., description="시장 (KR/US/ALL)"),
):
    """
    간단한 종목 목록 조회 (종목 코드와 이름만)
    페이지네이션 없이 전체 목록 반환
    Redis 캐싱 적용 (24시간)
    """
    try:
        # 캐시 키 생성
        cache_key = f"stocks:list:simple:{market.upper()}"
        
        # 캐시에서 조회
        cached_data = await cache_manager.get(cache_key)
        if cached_data:
            logger.info(f"Cache hit for key: {cache_key}")
            return cached_data
        
        # 캐시 미스 시 DB에서 조회
        logger.info(f"Cache miss for key: {cache_key}")
        stocks = []
        
        if market.upper() in ["ALL", "KR"]:
            kr_stocks = stock_fetcher.get_all_kr_stocks()
            # 종목 코드와 이름만 포함하는 간단한 형태로 변환
            simple_kr_stocks = [
                {
                    "symbol": stock["symbol"],
                    "name": stock["name"],
                    "market": "KR"
                }
                for stock in kr_stocks
            ]
            stocks.extend(simple_kr_stocks)
        
        if market.upper() in ["ALL", "US"]:
            us_stocks = stock_fetcher.get_all_us_stocks()
            # 종목 코드와 이름만 포함하는 간단한 형태로 변환
            simple_us_stocks = [
                {
                    "symbol": stock["symbol"],
                    "name": stock["name"],
                    "market": "US"
                }
                for stock in us_stocks
            ]
            stocks.extend(simple_us_stocks)
        
        if not stocks and market.upper() not in ["KR", "US", "ALL"]:
            raise HTTPException(status_code=400, detail="지원하지 않는 시장입니다 (KR/US/ALL)")
        
        result = {
            "market": market.upper(),
            "total_count": len(stocks),
            "stocks": stocks
        }
        
        # 결과를 캐시에 저장 (24시간)
        await cache_manager.set(cache_key, result, ttl=CACHE_TTL_24H)
        logger.info(f"Cached data for key: {cache_key}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"간단한 종목 목록 조회 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500, detail=f"간단한 종목 목록 조회 중 오류 발생: {str(e)}"
        )


@router.get("/list/simple/{market_type}")
async def get_simple_stock_list_by_market_type(
    market_type: str,
):
    """
    시장별 간단한 종목 목록 조회 (KOSPI/KOSDAQ/US)
    """
    try:
        stocks = []
        
        if market_type.upper() == "KOSPI":
            all_stocks = stock_fetcher.get_all_kospi_stocks()
        elif market_type.upper() == "KOSDAQ":
            all_stocks = stock_fetcher.get_all_kosdaq_stocks()
        elif market_type.upper() == "US":
            all_stocks = stock_fetcher.get_all_us_stocks()
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 시장입니다 (KOSPI/KOSDAQ/US)")
        
        # 종목 코드와 이름만 포함하는 간단한 형태로 변환
        simple_stocks = [
            {
                "symbol": stock["symbol"],
                "name": stock["name"]
            }
            for stock in all_stocks
        ]
        
        return {
            "market_type": market_type.upper(),
            "total_count": len(simple_stocks),
            "stocks": simple_stocks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시장별 간단한 종목 목록 조회 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500, detail=f"시장별 간단한 종목 목록 조회 중 오류 발생: {str(e)}"
        )


@router.get("/market/status")
async def get_market_status():
    """시장 상태 정보"""
    try:
        from datetime import datetime
        import random
        
        # Mock 시장 상태 데이터
        kospi_change = random.uniform(-2, 2)
        nasdaq_change = random.uniform(-1.5, 1.5)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "markets": {
                "KOSPI": {
                    "name": "코스피",
                    "index": round(2500 + random.uniform(-100, 100), 2),
                    "change": round(kospi_change, 2),
                    "change_percent": round(kospi_change / 2500 * 100, 2),
                    "status": "OPEN" if 9 <= datetime.now().hour < 16 else "CLOSED"
                },
                "KOSDAQ": {
                    "name": "코스닥",
                    "index": round(850 + random.uniform(-50, 50), 2),
                    "change": round(kospi_change * 0.7, 2),
                    "change_percent": round(kospi_change * 0.7 / 850 * 100, 2),
                    "status": "OPEN" if 9 <= datetime.now().hour < 16 else "CLOSED"
                },
                "NASDAQ": {
                    "name": "나스닥",
                    "index": round(15000 + random.uniform(-500, 500), 2),
                    "change": round(nasdaq_change * 100, 2),
                    "change_percent": round(nasdaq_change, 2),
                    "status": "OPEN" if 22 <= datetime.now().hour or datetime.now().hour < 5 else "CLOSED"
                }
            }
        }

    except Exception as e:
        logger.error(f"시장 상태 조회 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500, detail=f"시장 상태 조회 중 오류 발생: {str(e)}"
        )


@router.delete("/cache/clear")
async def clear_stock_cache():
    """
    종목 목록 캐시 수동 초기화 (관리자용)
    stocks:list:simple:* 패턴의 모든 캐시를 삭제
    """
    try:
        # 종목 목록 캐시 삭제
        deleted_count = await cache_manager.clear_pattern("stocks:list:simple:*")
        
        logger.info(f"Cleared {deleted_count} stock list cache entries")
        
        return {
            "message": "Stock list cache cleared successfully",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"캐시 초기화 중 오류 발생: {e}")
        raise HTTPException(
            status_code=500, detail=f"캐시 초기화 중 오류 발생: {str(e)}"
        )