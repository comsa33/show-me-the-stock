"""
Stock Search API endpoints
Provides optimized endpoints for stock search functionality
"""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from pydantic import BaseModel
import logging

from ....database.mongodb_client import get_mongodb_client

logger = logging.getLogger(__name__)
router = APIRouter()


class StockSearchItem(BaseModel):
    """Stock item for search results"""
    symbol: str
    name: str
    market: str
    exchange: Optional[str] = None


class StockSearchResponse(BaseModel):
    """Response model for stock search"""
    stocks: List[StockSearchItem]
    total: int
    market: Optional[str] = None


@router.get("/all", response_model=StockSearchResponse)
async def get_all_stocks_for_search(
    market: Optional[str] = Query(None, description="Filter by market (KR/US)")
):
    """
    Get all stocks optimized for search functionality
    Returns minimal data for fast loading and caching
    
    Args:
        market: Optional market filter (KR or US)
    """
    try:
        db = get_mongodb_client()
        
        # Build query
        query = {"is_active": True}
        if market:
            query["market"] = market.upper()
        
        # Get stocks with only necessary fields
        stocks = list(db.db.stock_list.find(
            query,
            {
                "symbol": 1,
                "name": 1,
                "market": 1,
                "exchange": 1,
                "_id": 0
            }
        ).sort("symbol", 1))
        
        # Format response
        stock_items = []
        for stock in stocks:
            stock_items.append(StockSearchItem(
                symbol=stock["symbol"],
                name=stock["name"],
                market=stock["market"],
                exchange=stock.get("exchange")
            ))
        
        return StockSearchResponse(
            stocks=stock_items,
            total=len(stock_items),
            market=market.upper() if market else None
        )
        
    except Exception as e:
        logger.error(f"Error getting stocks for search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/combined", response_model=StockSearchResponse)
async def get_combined_stocks():
    """
    Get all stocks (KR + US) in a single response
    Optimized for frontend caching
    """
    try:
        db = get_mongodb_client()
        
        # Get all active stocks
        stocks = list(db.db.stock_list.find(
            {"is_active": True},
            {
                "symbol": 1,
                "name": 1,
                "market": 1,
                "exchange": 1,
                "_id": 0
            }
        ).sort([("market", 1), ("symbol", 1)]))
        
        # Format response
        stock_items = []
        for stock in stocks:
            stock_items.append(StockSearchItem(
                symbol=stock["symbol"],
                name=stock["name"],
                market=stock["market"],
                exchange=stock.get("exchange")
            ))
        
        return StockSearchResponse(
            stocks=stock_items,
            total=len(stock_items)
        )
        
    except Exception as e:
        logger.error(f"Error getting combined stocks: {e}")
        raise HTTPException(status_code=500, detail=str(e))