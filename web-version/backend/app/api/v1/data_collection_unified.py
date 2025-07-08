"""
Unified Data Collection API endpoints
Consolidates v1 and v3 features with new data providers only
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from ...collectors.stock_data_collector_v3 import collector_v3
from ...collectors.scheduler import get_scheduler
from ...database.mongodb_client import get_mongodb_client
from ...collectors.index_data_collector import get_index_collector

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/data", tags=["data-collection"])


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


# ===== Database Operations =====

@router.post("/initialize")
async def initialize_database():
    """Initialize MongoDB indexes"""
    try:
        db = get_mongodb_client()
        db.create_indexes()
        return CollectionResponse(
            status="success",
            message="Database indexes created successfully"
        )
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_collection_status():
    """Get comprehensive data collection status"""
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
        
        # Count indices
        kr_indices = db.db.market_indices.count_documents({"market": "KR"})
        us_indices = db.db.market_indices.count_documents({"market": "US"})
        
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
            "indices": {
                "KR": kr_indices,
                "US": us_indices,
                "total": kr_indices + us_indices
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


# ===== Stock List Collection =====

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
            message = "Korean stock list collection started"
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


# ===== Price Data Collection =====

@router.post("/prices/historical")
async def collect_historical_prices(
    background_tasks: BackgroundTasks,
    request: CollectionRequest
):
    """
    Collect historical price data for specified stocks
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


@router.post("/prices/all/{market}")
async def collect_all_historical_prices(
    market: str,
    background_tasks: BackgroundTasks,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(None, description="Limit number of stocks to collect")
):
    """
    Collect historical prices for all stocks in a market
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


# ===== Financial Data Collection =====

@router.post("/financial/{market}")
async def collect_financial_data(
    market: str,
    background_tasks: BackgroundTasks,
    symbols: Optional[List[str]] = Query(None, description="Specific symbols to collect"),
    limit: Optional[int] = Query(None, description="Limit number of stocks")
):
    """
    Collect financial data for stocks
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


# ===== Daily Collection =====

@router.post("/daily/{market}")
async def collect_daily_data(
    market: str,
    background_tasks: BackgroundTasks
):
    """
    Collect daily data (prices and financials) for a market
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


# ===== Batch Collection =====

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


# ===== Index Data Collection =====

@router.post("/indices/historical")
async def collect_indices_historical(
    background_tasks: BackgroundTasks,
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    market: Optional[str] = Query(None, description="Market (KR/US/ALL)")
):
    """
    Collect historical index data for market indices
    """
    try:
        index_collector = get_index_collector()
        
        # Determine which markets to collect
        markets_to_collect = []
        if market is None or market.upper() == "ALL":
            markets_to_collect = ["KR", "US"]
        else:
            markets_to_collect = [market.upper()]
        
        # Convert dates for Korean market
        kr_start = None
        kr_end = None
        if start_date:
            kr_start = start_date.replace("-", "")
        if end_date:
            kr_end = end_date.replace("-", "")
        
        # Start collection tasks
        messages = []
        for mkt in markets_to_collect:
            if mkt == "KR":
                background_tasks.add_task(
                    index_collector.collect_korean_indices,
                    kr_start,
                    kr_end
                )
                messages.append("Korean indices")
            elif mkt == "US":
                background_tasks.add_task(
                    index_collector.collect_us_indices,
                    start_date,
                    end_date
                )
                messages.append("US indices")
        
        date_range = f"{start_date or '1 year ago'} to {end_date or 'today'}"
        
        return CollectionResponse(
            status="started",
            message=f"Historical index collection started for {', '.join(messages)} from {date_range}"
        )
        
    except Exception as e:
        logger.error(f"Error starting historical index collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/indices/daily")
async def collect_indices_daily(background_tasks: BackgroundTasks):
    """
    Collect today's index data
    """
    try:
        index_collector = get_index_collector()
        
        background_tasks.add_task(index_collector.collect_daily_indices)
        
        return CollectionResponse(
            status="started",
            message="Daily index collection started for all markets"
        )
        
    except Exception as e:
        logger.error(f"Error starting daily index collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Scheduler Management =====

@router.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status and jobs"""
    try:
        scheduler = get_scheduler()
        jobs = scheduler.get_jobs()
        
        job_info = []
        for job in jobs:
            job_info.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "scheduler_running": scheduler.scheduler.running,
            "jobs": job_info
        }
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/start")
async def start_scheduler():
    """Start the data collection scheduler"""
    try:
        scheduler = get_scheduler()
        if not scheduler.scheduler.running:
            scheduler.start()
            return CollectionResponse(
                status="success",
                message="Scheduler started successfully"
            )
        else:
            return CollectionResponse(
                status="info",
                message="Scheduler is already running"
            )
            
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the data collection scheduler"""
    try:
        scheduler = get_scheduler()
        if scheduler.scheduler.running:
            scheduler.stop()
            return CollectionResponse(
                status="success",
                message="Scheduler stopped successfully"
            )
        else:
            return CollectionResponse(
                status="info",
                message="Scheduler is not running"
            )
            
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))