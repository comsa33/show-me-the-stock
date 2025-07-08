"""
Data Collection V3 API endpoints
Uses new data providers instead of pykrx
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from ...collectors.stock_data_collector_v3 import collector_v3
from ...database.mongodb_client import get_mongodb_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/collection/v3", tags=["data-collection-v3"])


class CollectionRequest(BaseModel):
    """Request model for data collection"""
    symbols: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    market: str = "KR"  # KR or US
    limit: Optional[int] = None


class CollectionResponse(BaseModel):
    """Response model for collection status"""
    status: str
    message: str
    details: Optional[dict] = None


@router.post("/stocks/list/{market}")
async def collect_stock_list(
    market: str,
    background_tasks: BackgroundTasks
):
    """
    Collect and update stock list for specified market
    
    Args:
        market: Market code (KR or US)
    """
    try:
        market = market.upper()
        if market not in ["KR", "US"]:
            raise HTTPException(status_code=400, detail="Market must be KR or US")
        
        if market == "KR":
            background_tasks.add_task(collector_v3.collect_kr_stock_list)
            message = "Korean stock list collection started (using MongoDB existing data)"
        else:
            background_tasks.add_task(collector_v3.collect_us_stock_list)
            message = "US stock list collection started"
        
        return CollectionResponse(
            status="started",
            message=message
        )
        
    except Exception as e:
        logger.error(f"Error starting stock list collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stocks/prices/historical")
async def collect_historical_prices(
    background_tasks: BackgroundTasks,
    request: CollectionRequest
):
    """
    Collect historical price data for specified stocks
    
    Args:
        request: Collection request with symbols, dates, and market
    """
    try:
        if not request.symbols:
            raise HTTPException(
                status_code=400,
                detail="Symbols required for historical price collection"
            )
        
        if not request.start_date or not request.end_date:
            # Default to last 1 year
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            request.start_date = start_date.strftime("%Y-%m-%d")
            request.end_date = end_date.strftime("%Y-%m-%d")
        
        # Collect for each symbol
        for symbol in request.symbols:
            background_tasks.add_task(
                collector_v3.collect_historical_prices,
                symbol,
                request.start_date,
                request.end_date,
                request.market
            )
        
        return CollectionResponse(
            status="started",
            message=f"Historical price collection started for {len(request.symbols)} {request.market} stocks",
            details={
                "symbols": request.symbols,
                "start_date": request.start_date,
                "end_date": request.end_date,
                "market": request.market
            }
        )
        
    except Exception as e:
        logger.error(f"Error starting historical price collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stocks/prices/all/{market}")
async def collect_all_historical_prices(
    market: str,
    background_tasks: BackgroundTasks,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(None, description="Limit number of stocks to collect")
):
    """
    Collect historical prices for all stocks in a market
    
    Args:
        market: Market code (KR or US)
        start_date: Start date for historical data
        end_date: End date for historical data
        limit: Maximum number of stocks to process
    """
    try:
        market = market.upper()
        if market not in ["KR", "US"]:
            raise HTTPException(status_code=400, detail="Market must be KR or US")
        
        background_tasks.add_task(
            collector_v3.collect_all_historical_prices,
            market,
            start_date,
            end_date,
            limit
        )
        
        return CollectionResponse(
            status="started",
            message=f"Started collecting historical prices for all {market} stocks",
            details={
                "market": market,
                "start_date": start_date or "1 year ago",
                "end_date": end_date or "today",
                "limit": limit or "all stocks"
            }
        )
        
    except Exception as e:
        logger.error(f"Error starting all historical price collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stocks/financial/{market}")
async def collect_financial_data(
    market: str,
    background_tasks: BackgroundTasks,
    symbols: Optional[List[str]] = Query(None, description="Specific symbols to collect"),
    limit: Optional[int] = Query(None, description="Limit number of stocks")
):
    """
    Collect financial data for stocks
    
    Args:
        market: Market code (KR or US)
        symbols: Optional list of specific symbols
        limit: Maximum number of stocks to process
    """
    try:
        market = market.upper()
        if market not in ["KR", "US"]:
            raise HTTPException(status_code=400, detail="Market must be KR or US")
        
        if symbols:
            # Collect for specific symbols
            for symbol in symbols:
                background_tasks.add_task(
                    collector_v3.collect_financial_data,
                    symbol,
                    market
                )
            message = f"Started collecting financial data for {len(symbols)} {market} stocks"
        else:
            # Collect for all stocks
            background_tasks.add_task(
                collector_v3.collect_all_financial_data,
                market,
                limit
            )
            message = f"Started collecting financial data for all {market} stocks"
        
        return CollectionResponse(
            status="started",
            message=message,
            details={
                "market": market,
                "symbols": symbols,
                "limit": limit
            }
        )
        
    except Exception as e:
        logger.error(f"Error starting financial data collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/daily/{market}")
async def collect_daily_data(
    market: str,
    background_tasks: BackgroundTasks
):
    """
    Collect daily data (prices and financials) for a market
    
    Args:
        market: Market code (KR or US)
    """
    try:
        market = market.upper()
        if market not in ["KR", "US"]:
            raise HTTPException(status_code=400, detail="Market must be KR or US")
        
        background_tasks.add_task(
            collector_v3.collect_daily_data,
            market
        )
        
        return CollectionResponse(
            status="started",
            message=f"Daily data collection started for {market} market"
        )
        
    except Exception as e:
        logger.error(f"Error starting daily data collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_collection_status():
    """Get current data collection status"""
    try:
        db = get_mongodb_client()
        
        # Count stocks by market
        kr_stocks = db.db.stock_list.count_documents({"market": "KR"})
        us_stocks = db.db.stock_list.count_documents({"market": "US"})
        
        # Count price data
        kr_prices = db.db.stock_price_daily.count_documents({"market": "KR"})
        us_prices = db.db.stock_price_daily.count_documents({"market": "US"})
        
        # Count financial data
        kr_financial = db.db.stock_financial.count_documents({"market": "KR"})
        us_financial = db.db.stock_financial.count_documents({"market": "US"})
        
        # Get latest data dates
        latest_kr_price = db.db.stock_price_daily.find_one(
            {"market": "KR"},
            sort=[("date", -1)]
        )
        latest_us_price = db.db.stock_price_daily.find_one(
            {"market": "US"},
            sort=[("date", -1)]
        )
        
        return {
            "stocks": {
                "KR": kr_stocks,
                "US": us_stocks,
                "total": kr_stocks + us_stocks
            },
            "price_data": {
                "KR": {
                    "count": kr_prices,
                    "latest_date": latest_kr_price["date"] if latest_kr_price else None
                },
                "US": {
                    "count": us_prices,
                    "latest_date": latest_us_price["date"] if latest_us_price else None
                },
                "total": kr_prices + us_prices
            },
            "financial_data": {
                "KR": kr_financial,
                "US": us_financial,
                "total": kr_financial + us_financial
            },
            "data_providers": {
                "KR": "FinanceDataReader (FDR)",
                "US": "Yahoo Finance",
                "indices": "Yahoo Finance"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting collection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch/yearly")
async def collect_yearly_batch(
    background_tasks: BackgroundTasks,
    market: str = Query(..., description="Market code (KR or US)"),
    year: int = Query(..., description="Year to collect data for"),
    batch_size: int = Query(50, description="Number of stocks per batch"),
    offset: int = Query(0, description="Starting offset for batch")
):
    """
    Collect data for a specific year in batches
    
    Args:
        market: Market code (KR or US)
        year: Year to collect (e.g., 2023)
        batch_size: Number of stocks to process
        offset: Starting position in stock list
    """
    try:
        market = market.upper()
        if market not in ["KR", "US"]:
            raise HTTPException(status_code=400, detail="Market must be KR or US")
        
        # Get stock list
        db = get_mongodb_client()
        stocks = list(db.db.stock_list.find(
            {"market": market, "is_active": True},
            {"symbol": 1, "name": 1}
        ).skip(offset).limit(batch_size))
        
        if not stocks:
            return CollectionResponse(
                status="completed",
                message="No more stocks to process",
                details={"offset": offset, "batch_size": batch_size}
            )
        
        # Calculate date range for the year
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        # Adjust if end date is in the future
        if datetime.strptime(end_date, "%Y-%m-%d") > datetime.now():
            end_date = datetime.now().strftime("%Y-%m-%d")
        
        # Collect data for each stock in batch
        for stock in stocks:
            symbol = stock["symbol"]
            
            # Collect historical prices
            background_tasks.add_task(
                collector_v3.collect_historical_prices,
                symbol,
                start_date,
                end_date,
                market
            )
            
            # Collect financial data (once per symbol)
            background_tasks.add_task(
                collector_v3.collect_financial_data,
                symbol,
                market
            )
        
        # Check if there are more stocks
        total_stocks = db.db.stock_list.count_documents({"market": market, "is_active": True})
        has_more = offset + batch_size < total_stocks
        next_offset = offset + batch_size if has_more else None
        
        return CollectionResponse(
            status="started",
            message=f"Started collecting {year} data for {len(stocks)} {market} stocks",
            details={
                "year": year,
                "stocks_in_batch": len(stocks),
                "offset": offset,
                "next_offset": next_offset,
                "has_more": has_more,
                "total_stocks": total_stocks,
                "date_range": f"{start_date} to {end_date}"
            }
        )
        
    except Exception as e:
        logger.error(f"Error starting yearly batch collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indicators/calculate")
async def calculate_technical_indicators(
    background_tasks: BackgroundTasks,
    market: str = Query(..., description="Market code (KR or US)"),
    symbols: Optional[List[str]] = Query(None, description="Specific symbols to calculate")
):
    """
    Calculate technical indicators for stocks based on existing price data
    
    Args:
        market: Market code (KR or US)
        symbols: Optional list of specific symbols
    """
    try:
        market = market.upper()
        if market not in ["KR", "US"]:
            raise HTTPException(status_code=400, detail="Market must be KR or US")
        
        db = get_mongodb_client()
        
        if symbols:
            stocks_to_process = symbols
        else:
            # Get all active stocks for the market
            stocks = list(db.db.stock_list.find(
                {"market": market, "is_active": True},
                {"symbol": 1}
            ))
            stocks_to_process = [s["symbol"] for s in stocks]
        
        # For now, return a message that indicators will be calculated
        # This can be implemented to calculate various technical indicators
        
        return CollectionResponse(
            status="info",
            message=f"Technical indicator calculation would process {len(stocks_to_process)} {market} stocks",
            details={
                "market": market,
                "stock_count": len(stocks_to_process),
                "indicators": ["SMA", "EMA", "RSI", "MACD", "Bollinger Bands", "Momentum"]
            }
        )
        
    except Exception as e:
        logger.error(f"Error calculating indicators: {e}")
        raise HTTPException(status_code=500, detail=str(e))