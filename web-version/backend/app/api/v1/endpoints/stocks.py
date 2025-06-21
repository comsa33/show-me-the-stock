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
from app.data.stock_data import StockDataFetcher

router = APIRouter()
stock_fetcher = StockDataFetcher()


@router.get("/search")
async def search_stocks(
    query: str = Query(..., min_length=1, max_length=100, description="검색어"),
    market: str = Query("KR", description="시장 (KR/US)"),
    limit: int = Query(default=20, ge=1, le=100, description="결과 수 제한")
):
    """주식 검색"""
    try:
        results = stock_fetcher.search_stocks(query, market, limit)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"검색 중 오류 발생: {str(e)}")


@router.get("/list/{market}")
async def get_stock_list(
    market: str,
    limit: int = Query(default=50, ge=1, le=500, description="결과 수 제한")
):
    """시장별 주식 목록 조회"""
    try:
        if market.upper() == "KR":
            symbols_dict = stock_fetcher.kospi_symbols
        elif market.upper() == "US":
            symbols_dict = stock_fetcher.nasdaq_symbols
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 시장입니다")
        
        # 제한된 수만큼 반환
        limited_items = list(symbols_dict.items())[:limit]
        
        return {
            "market": market.upper(),
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
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주식 목록 조회 중 오류 발생: {str(e)}")


@router.get("/data/{symbol}")
async def get_stock_data(
    symbol: str,
    market: str = Query(..., description="시장 (KR/US)"),
    period: str = Query(default="1y", description="조회 기간"),
    include_indicators: bool = Query(default=True, description="기술적 지표 포함 여부")
):
    """개별 주식 데이터 조회"""
    try:
        # 주식 데이터 조회
        data = stock_fetcher.get_stock_data(symbol, period, market)
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail=f"주식 데이터를 찾을 수 없습니다: {symbol}")
        
        # 기본 정보
        result = {
            "symbol": symbol,
            "market": market.upper(),
            "period": period,
            "data": data.to_dict("records"),
            "current_price": float(data['Close'].iloc[-1]),
            "change": float(data['Close'].iloc[-1] - data['Close'].iloc[-2]) if len(data) > 1 else 0,
            "volume": int(data['Volume'].iloc[-1])
        }
        
        # 기술적 지표 추가
        if include_indicators:
            indicators = stock_fetcher.calculate_technical_indicators(data)
            result["technical_indicators"] = indicators
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"주식 데이터 조회 중 오류 발생: {str(e)}")


@router.get("/price/{symbol}")
async def get_stock_price(
    symbol: str,
    market: str = Query(..., description="시장 (KR/US)")
):
    """개별 주식 현재 가격 정보"""
    try:
        price_data = stock_fetcher.get_stock_price_data(symbol, market)
        
        # 주식 이름 찾기
        symbols_dict = stock_fetcher.kospi_symbols if market.upper() == "KR" else stock_fetcher.nasdaq_symbols
        name = None
        for stock_name, stock_symbol in symbols_dict.items():
            if stock_symbol == symbol:
                name = stock_name
                break
        
        return {
            "symbol": symbol,
            "name": name or symbol,
            "market": market.upper(),
            "price": price_data["price"],
            "change": price_data["change"],
            "change_percent": price_data["change_percent"],
            "volume": price_data["volume"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"가격 정보 조회 중 오류 발생: {str(e)}")


@router.get("/popular")
async def get_popular_stocks(
    market: str = Query("all", description="시장 (KR/US/all)"),
    limit: int = Query(default=10, ge=1, le=50, description="결과 수 제한")
):
    """인기 주식 목록"""
    try:
        popular_stocks = stock_fetcher.get_popular_stocks(market, limit)
        return {
            "market": market.upper(),
            "stocks": popular_stocks
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"인기 주식 조회 중 오류 발생: {str(e)}")


@router.get("/prices/{market}")
async def get_market_prices(
    market: str,
    limit: int = Query(default=20, ge=1, le=100, description="결과 수 제한")
):
    """시장별 주식 가격 목록 조회"""
    try:
        if market.upper() == "KR":
            symbols_dict = stock_fetcher.kospi_symbols
        elif market.upper() == "US":
            symbols_dict = stock_fetcher.nasdaq_symbols
        else:
            raise HTTPException(status_code=400, detail="지원하지 않는 시장입니다")
        
        stocks_with_prices = []
        symbol_items = list(symbols_dict.items())[:limit]
        
        for name, symbol in symbol_items:
            try:
                price_data = stock_fetcher.get_stock_price_data(symbol, market.upper())
                stocks_with_prices.append({
                    "name": name,
                    "symbol": symbol,
                    "display": f"{name} ({symbol})",
                    "market": market.upper(),
                    "price": price_data["price"],
                    "change": price_data["change"],
                    "change_percent": price_data["change_percent"],
                    "volume": price_data["volume"]
                })
            except Exception as e:
                print(f"Error fetching price for {symbol}: {str(e)}")
                # 가격 데이터 실패시 기본값으로 추가
                stocks_with_prices.append({
                    "name": name,
                    "symbol": symbol,
                    "display": f"{name} ({symbol})",
                    "market": market.upper(),
                    "price": 0,
                    "change": 0,
                    "change_percent": 0,
                    "volume": 0
                })
        
        return {
            "market": market.upper(),
            "total_available": len(symbols_dict),
            "returned_count": len(stocks_with_prices),
            "stocks": stocks_with_prices
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시장 가격 조회 중 오류 발생: {str(e)}")


@router.get("/market/status")
async def get_market_status():
    """시장 상태 정보"""
    try:
        status = stock_fetcher.get_market_status()
        return status
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시장 상태 조회 중 오류 발생: {str(e)}")


@router.get("/technical/{symbol}")
async def get_technical_indicators(
    symbol: str,
    market: str = Query(..., description="시장 (KR/US)"),
    period: str = Query(default="6mo", description="분석 기간"),
    indicators: str = Query(default="all", description="지표 타입 (all/ma/rsi/bollinger)")
):
    """기술적 지표 조회"""
    try:
        data = stock_fetcher.get_stock_data(symbol, period, market)
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail=f"주식 데이터를 찾을 수 없습니다: {symbol}")
        
        technical_data = stock_fetcher.calculate_technical_indicators(data, indicators)
        
        return {
            "symbol": symbol,
            "market": market.upper(),
            "period": period,
            "indicators": technical_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"기술적 지표 조회 중 오류 발생: {str(e)}")