"""
주식 관련 API 엔드포인트
"""

from typing import List
from fastapi import APIRouter, HTTPException, Query
from app.models.stock import (
    StockSearchRequest, StockSearchResult, StockDataRequest, 
    StockDataResponse, MultiStockDataResponse, MarketType, PeriodType,
    APIResponse
)
from app.services.stock_service import stock_service

router = APIRouter()


@router.get("/search", response_model=List[StockSearchResult])
async def search_stocks(
    query: str = Query(..., min_length=1, max_length=100, description="검색어"),
    market: MarketType = Query(..., description="시장 (KR/US)"),
    limit: int = Query(default=20, ge=1, le=100, description="결과 수 제한")
):
    """
    주식 검색
    
    - **query**: 검색어 (주식명 또는 심볼)
    - **market**: 시장 (KR: 한국, US: 미국)
    - **limit**: 최대 결과 수
    """
    try:
        results = await stock_service.search_stocks(query, market, limit)
        
        return [
            StockSearchResult(
                symbol=result["symbol"],
                name=result["name"],
                display=result["display"],
                score=result["score"],
                market=result["market"]
            )
            for result in results
        ]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")


@router.get("/list/{market}")
async def get_stock_list(
    market: MarketType,
    limit: int = Query(default=50, ge=1, le=500, description="결과 수 제한")
):
    """
    시장별 주식 목록 조회
    
    - **market**: 시장 (KR: 한국, US: 미국)
    - **limit**: 최대 결과 수
    """
    try:
        if market == MarketType.KR:
            symbols_dict = await stock_service.get_kospi_symbols()
        else:
            symbols_dict = await stock_service.get_nasdaq_symbols()
        
        # 제한된 수만큼 반환
        limited_items = list(symbols_dict.items())[:limit]
        
        return {
            "market": market,
            "total_available": len(symbols_dict),
            "returned_count": len(limited_items),
            "stocks": [
                {
                    "name": name,
                    "symbol": symbol,
                    "display": f"{name} ({symbol})"
                }
                for name, symbol in limited_items
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주식 목록 조회 중 오류 발생: {str(e)}")


@router.get("/suggestions/{market}")
async def get_stock_suggestions(
    market: MarketType,
    limit: int = Query(default=20, ge=1, le=50, description="추천 수")
):
    """
    인기 주식 추천
    
    - **market**: 시장 (KR: 한국, US: 미국)
    - **limit**: 추천 주식 수
    """
    try:
        if market == MarketType.KR:
            popular_names = [
                "삼성전자", "SK하이닉스", "NAVER", "LG화학", "KB금융",
                "LG에너지솔루션", "Celltrion", "삼성SDI", "SK아이이기술", "HMM",
                "현대차", "POSCO홀딩스", "기아", "LG전자", "삼성바이오로직스",
                "SK텔레콤", "CJ제일제당", "대한항공", "카카오", "대우조선해양"
            ]
            symbols_dict = await stock_service.get_kospi_symbols()
        else:
            popular_names = [
                "Apple", "Microsoft", "Amazon", "Google (Alphabet)", "Tesla",
                "Meta (Facebook)", "NVIDIA", "Netflix", "AMD", "Intel",
                "Berkshire Hathaway", "JPMorgan Chase", "Visa", "Mastercard", "Coca-Cola",
                "Disney", "Nike", "McDonald's", "PayPal", "Uber"
            ]
            symbols_dict = await stock_service.get_nasdaq_symbols()
        
        suggestions = []
        for name in popular_names[:limit]:
            if name in symbols_dict:
                suggestions.append({
                    "name": name,
                    "symbol": symbols_dict[name],
                    "display": f"{name} ({symbols_dict[name]})",
                    "market": market
                })
        
        return {
            "market": market,
            "suggestions": suggestions
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"추천 주식 조회 중 오류 발생: {str(e)}")


@router.get("/data/{symbol}", response_model=StockDataResponse)
async def get_stock_data(
    symbol: str,
    market: MarketType = Query(..., description="시장 (KR/US)"),
    period: PeriodType = Query(default=PeriodType.ONE_YEAR, description="조회 기간"),
    include_indicators: bool = Query(default=True, description="기술적 지표 포함 여부")
):
    """
    개별 주식 데이터 조회
    
    - **symbol**: 주식 심볼
    - **market**: 시장 (KR: 한국, US: 미국)
    - **period**: 조회 기간
    - **include_indicators**: 기술적 지표 포함 여부
    """
    try:
        result = await stock_service.get_stock_data(
            symbol=symbol,
            period=period,
            market=market,
            include_indicators=include_indicators
        )
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"주식 데이터를 찾을 수 없습니다: {symbol}")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주식 데이터 조회 중 오류 발생: {str(e)}")


@router.post("/data/multiple", response_model=MultiStockDataResponse)
async def get_multiple_stock_data(request: StockDataRequest):
    """
    다중 주식 데이터 조회
    
    여러 주식의 데이터를 한 번에 조회합니다.
    """
    try:
        if len(request.symbols) > 10:
            raise HTTPException(status_code=400, detail="최대 10개 주식까지 조회 가능합니다")
        
        result = await stock_service.get_multiple_stocks(
            symbols=request.symbols,
            period=request.period,
            market=request.market,
            include_indicators=request.include_indicators
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"다중 주식 데이터 조회 중 오류 발생: {str(e)}")


@router.get("/info/{symbol}")
async def get_stock_info(
    symbol: str,
    market: MarketType = Query(..., description="시장 (KR/US)")
):
    """
    주식 기본 정보 조회
    
    - **symbol**: 주식 심볼
    - **market**: 시장 (KR: 한국, US: 미국)
    """
    try:
        # 주식 이름 조회
        stock_name = await stock_service._get_stock_name(symbol, market)
        
        if market == MarketType.KR:
            currency = "KRW"
            exchange = "KRX"
        else:
            currency = "USD"
            exchange = "NASDAQ"
        
        return {
            "symbol": symbol,
            "name": stock_name,
            "market": market,
            "currency": currency,
            "exchange": exchange
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주식 정보 조회 중 오류 발생: {str(e)}")