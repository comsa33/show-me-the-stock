"""
Data Collection API endpoints
For initial data loading and manual collection
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from ...collectors.stock_data_collector import StockDataCollector
from ...collectors.scheduler import get_scheduler
from ...database.mongodb_client import get_mongodb_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/collection", tags=["data-collection"])


class CollectionRequest(BaseModel):
    """Request model for data collection"""
    symbols: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    market: str = "KR"  # KR or US


class CollectionResponse(BaseModel):
    """Response model for collection status"""
    status: str
    message: str
    task_id: Optional[str] = None


@router.post("/initialize-database")
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


@router.post("/collect-stock-list")
async def collect_stock_list(background_tasks: BackgroundTasks, 
                           request: CollectionRequest):
    """Collect and update stock list"""
    try:
        collector = StockDataCollector()
        
        if request.market == "KR":
            background_tasks.add_task(collector.collect_kr_stock_list)
            message = "Korean stock list collection started"
        else:
            # US stocks can be collected automatically or with specific symbols
            if request.symbols:
                background_tasks.add_task(
                    collector.collect_us_stock_list, 
                    request.symbols
                )
                message = f"US stock list collection started for {len(request.symbols)} specified symbols"
            else:
                # Collect comprehensive US stock list automatically
                background_tasks.add_task(collector.collect_us_stock_list)
                message = "US stock list collection started (fetching S&P 500, NASDAQ 100, Dow Jones, and popular stocks)"
        
        return CollectionResponse(status="started", message=message)
        
    except Exception as e:
        logger.error(f"Error starting stock list collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect-historical-data")
async def collect_historical_data(background_tasks: BackgroundTasks,
                                request: CollectionRequest):
    """Collect historical data for specified stocks and date range"""
    try:
        if not request.symbols:
            raise HTTPException(
                status_code=400,
                detail="Symbols required for historical data collection"
            )
        
        if not request.start_date or not request.end_date:
            # Default to last 1 year
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            request.start_date = start_date.strftime("%Y-%m-%d")
            request.end_date = end_date.strftime("%Y-%m-%d")
        
        collector = StockDataCollector()
        
        # Add task for each symbol
        for symbol in request.symbols:
            background_tasks.add_task(
                collector.collect_historical_data,
                symbol,
                request.market,
                request.start_date,
                request.end_date
            )
        
        return CollectionResponse(
            status="started",
            message=f"Historical data collection started for {len(request.symbols)} symbols from {request.start_date} to {request.end_date}"
        )
        
    except Exception as e:
        logger.error(f"Error starting historical data collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect-all-kr-historical")
async def collect_all_kr_historical(background_tasks: BackgroundTasks,
                                  years: int = 1,
                                  batch_size: int = 50,
                                  offset: int = 0):
    """Collect historical data for all Korean stocks (with batching)"""
    try:
        # Get all Korean stocks
        db = get_mongodb_client()
        kr_stocks = db.get_stock_list(market="KR")
        
        if not kr_stocks:
            # Try to collect stock list first
            logger.warning("No Korean stocks found. Collecting stock list first...")
            collector = StockDataCollector()
            collector.collect_kr_stock_list()
            # Retry getting stocks
            kr_stocks = db.get_stock_list(market="KR")
            
            if not kr_stocks:
                raise HTTPException(
                    status_code=404,
                    detail="Failed to collect Korean stock list. Please check the connection."
                )
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        collector = StockDataCollector()
        
        # Get batch of stocks
        total_stocks = len(kr_stocks)
        batch_stocks = kr_stocks[offset:offset + batch_size]
        
        # Collect data for each stock in batch
        for stock in batch_stocks:
            background_tasks.add_task(
                collector.collect_historical_data,
                stock["symbol"],
                "KR",
                start_str,
                end_str
            )
        
        return CollectionResponse(
            status="started",
            message=f"Historical data collection started for {len(batch_stocks)} Korean stocks (batch {offset//batch_size + 1} of {(total_stocks + batch_size - 1)//batch_size}) for {years} year(s). Total stocks: {total_stocks}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting Korean historical collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect-all-us-historical")
async def collect_all_us_historical(background_tasks: BackgroundTasks,
                                  years: int = 1,
                                  batch_size: int = 20,
                                  offset: int = 0):
    """Collect historical data for all US stocks (with batching)"""
    try:
        # Get all US stocks
        db = get_mongodb_client()
        us_stocks = db.get_stock_list(market="US")
        
        if not us_stocks:
            # Use default popular stocks
            from ...collectors.scheduler import DataCollectionScheduler
            scheduler = DataCollectionScheduler()
            default_symbols = scheduler.us_stocks
            
            # Collect stock list first
            collector = StockDataCollector()
            collector.collect_us_stock_list(default_symbols)
            
            # Retry getting stocks
            us_stocks = db.get_stock_list(market="US")
            
            if not us_stocks:
                raise HTTPException(
                    status_code=404,
                    detail="Failed to collect US stock list. Please check the connection."
                )
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        collector = StockDataCollector()
        
        # Get batch of stocks
        total_stocks = len(us_stocks)
        batch_stocks = us_stocks[offset:offset + batch_size]
        
        # Collect data for each stock in batch
        for stock in batch_stocks:
            background_tasks.add_task(
                collector.collect_historical_data,
                stock["symbol"],
                "US",
                start_str,
                end_str
            )
        
        return CollectionResponse(
            status="started",
            message=f"Historical data collection started for {len(batch_stocks)} US stocks (batch {offset//batch_size + 1} of {(total_stocks + batch_size - 1)//batch_size}) for {years} year(s). Total stocks: {total_stocks}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting US historical collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect-yearly-data")
async def collect_yearly_data(background_tasks: BackgroundTasks,
                            request: CollectionRequest,
                            year: int,
                            batch_size: int = 10):
    """Collect data for a specific year (useful for collecting all historical data)"""
    try:
        if not request.symbols:
            raise HTTPException(
                status_code=400,
                detail="Symbols required for yearly data collection"
            )
        
        # Calculate date range for the specific year
        start_date = datetime(year, 1, 1)
        end_date = datetime(year, 12, 31)
        
        # Adjust if end date is in the future
        if end_date > datetime.now():
            end_date = datetime.now()
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        collector = StockDataCollector()
        
        # Process in batches to avoid overwhelming the system
        for i in range(0, len(request.symbols), batch_size):
            batch = request.symbols[i:i + batch_size]
            for symbol in batch:
                background_tasks.add_task(
                    collector.collect_historical_data,
                    symbol,
                    request.market,
                    start_str,
                    end_str
                )
        
        return CollectionResponse(
            status="started",
            message=f"Data collection started for {len(request.symbols)} symbols for year {year}"
        )
        
    except Exception as e:
        logger.error(f"Error starting yearly data collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect-daily-data")
async def collect_daily_data(background_tasks: BackgroundTasks,
                           market: str = "KR",
                           date: Optional[str] = None):
    """Manually trigger daily data collection"""
    try:
        collector = StockDataCollector()
        
        if market == "KR":
            background_tasks.add_task(collector.collect_kr_daily_prices, date)
            background_tasks.add_task(collector.collect_kr_financial_data, date)
            message = f"Korean daily data collection started for {date or 'today'}"
        else:
            # Get US stocks from database
            db = get_mongodb_client()
            us_stocks = db.get_stock_list(market="US")
            symbols = [stock["symbol"] for stock in us_stocks]
            
            if not symbols:
                # Use default popular stocks
                from ...collectors.scheduler import DataCollectionScheduler
                scheduler = DataCollectionScheduler()
                symbols = scheduler.us_stocks
            
            background_tasks.add_task(
                collector.collect_us_daily_prices, 
                symbols, 
                date
            )
            background_tasks.add_task(
                collector.collect_us_financial_data,
                symbols,
                date
            )
            message = f"US daily data collection (prices + financial) started for {len(symbols)} stocks for {date or 'today'}"
        
        # Also collect indices
        background_tasks.add_task(collector.collect_indices_data, date)
        
        return CollectionResponse(status="started", message=message)
        
    except Exception as e:
        logger.error(f"Error starting daily data collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler-status")
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


@router.post("/start-scheduler")
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


@router.post("/stop-scheduler")
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


@router.post("/collect-financial-data")
async def collect_financial_data(background_tasks: BackgroundTasks,
                               request: CollectionRequest):
    """Collect financial data for specified stocks"""
    try:
        collector = StockDataCollector()
        
        if request.market == "KR":
            background_tasks.add_task(
                collector.collect_kr_financial_data,
                request.start_date  # Can be used as date parameter
            )
            message = f"Korean financial data collection started for {request.start_date or 'today'}"
        else:
            # US financial data
            if request.symbols:
                background_tasks.add_task(
                    collector.collect_us_financial_data,
                    request.symbols,
                    request.start_date
                )
                message = f"US financial data collection started for {len(request.symbols)} symbols"
            else:
                # Get all US stocks from database
                db = get_mongodb_client()
                us_stocks = db.get_stock_list(market="US")
                symbols = [stock["symbol"] for stock in us_stocks]
                
                if not symbols:
                    # Use default popular stocks
                    from ...collectors.scheduler import DataCollectionScheduler
                    scheduler = DataCollectionScheduler()
                    symbols = scheduler.us_stocks
                
                background_tasks.add_task(
                    collector.collect_us_financial_data,
                    symbols,
                    request.start_date
                )
                message = f"US financial data collection started for {len(symbols)} stocks"
        
        return CollectionResponse(status="started", message=message)
        
    except Exception as e:
        logger.error(f"Error starting financial data collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collection-status")
async def get_collection_status():
    """Get data collection status (number of stocks and data points)"""
    try:
        db = get_mongodb_client()
        
        # Count stocks
        kr_stocks = len(db.get_stock_list(market="KR"))
        us_stocks = len(db.get_stock_list(market="US"))
        
        # Count data points
        price_count = db.db.stock_price_daily.count_documents({})
        financial_count = db.db.stock_financial.count_documents({})
        indices_count = db.db.market_indices.count_documents({})
        realtime_count = db.db.stock_realtime.count_documents({})
        
        return {
            "stocks": {
                "KR": kr_stocks,
                "US": us_stocks,
                "total": kr_stocks + us_stocks
            },
            "data_points": {
                "price_daily": price_count,
                "financial": financial_count,
                "indices": indices_count,
                "realtime": realtime_count,
                "total": price_count + financial_count + indices_count + realtime_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting collection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect-all-data-by-year")
async def collect_all_data_by_year(background_tasks: BackgroundTasks,
                                  start_year: int = 2020,
                                  end_year: int = 2024,
                                  market: str = "KR"):
    """Collect all historical data year by year for better error handling"""
    try:
        db = get_mongodb_client()
        stocks = db.get_stock_list(market=market)
        
        if not stocks:
            raise HTTPException(
                status_code=404,
                detail=f"No {market} stocks found. Please collect stock list first."
            )
        
        collector = StockDataCollector()
        collection_tasks = []
        
        # Collect data year by year
        for year in range(start_year, end_year + 1):
            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
            
            # Adjust if end date is in the future
            if datetime.strptime(end_date, "%Y-%m-%d") > datetime.now():
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            for stock in stocks[:10]:  # Start with first 10 stocks
                background_tasks.add_task(
                    collector.collect_historical_data,
                    stock["symbol"],
                    market,
                    start_date,
                    end_date
                )
                collection_tasks.append(f"{stock['symbol']}_{year}")
        
        return CollectionResponse(
            status="started",
            message=f"Year-by-year collection started for {len(stocks[:10])} {market} stocks from {start_year} to {end_year}. Total tasks: {len(collection_tasks)}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting year-by-year collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect-us-financial-historical")
async def collect_us_financial_historical(background_tasks: BackgroundTasks,
                                        batch_size: int = 20,
                                        offset: int = 0):
    """
    Collect US financial data for all stocks (one-time historical collection)
    Note: yfinance provides current fundamental data only, not historical
    This will collect the most recent financial metrics for all US stocks
    """
    try:
        # Get all US stocks
        db = get_mongodb_client()
        us_stocks = db.get_stock_list(market="US")
        
        if not us_stocks:
            # Try to collect stock list first
            logger.warning("No US stocks found. Collecting stock list first...")
            collector = StockDataCollector()
            # Collect comprehensive US stock list
            background_tasks.add_task(collector.collect_us_stock_list)
            
            return CollectionResponse(
                status="started",
                message="US stock list collection started first. Please retry financial collection after stock list is complete."
            )
        
        collector = StockDataCollector()
        
        # Get batch of stocks
        total_stocks = len(us_stocks)
        batch_stocks = us_stocks[offset:offset + batch_size]
        symbols = [stock["symbol"] for stock in batch_stocks]
        
        # Get today's date for financial data
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Collect financial data for batch
        background_tasks.add_task(
            collector.collect_us_financial_data,
            symbols,
            today
        )
        
        # Calculate batch info
        current_batch = offset // batch_size + 1
        total_batches = (total_stocks + batch_size - 1) // batch_size
        has_more = offset + batch_size < total_stocks
        next_offset = offset + batch_size if has_more else None
        
        return {
            "status": "started",
            "message": f"US financial data collection started for {len(symbols)} stocks",
            "batch_info": {
                "current_batch": current_batch,
                "total_batches": total_batches,
                "batch_size": batch_size,
                "offset": offset,
                "next_offset": next_offset,
                "has_more": has_more,
                "total_stocks": total_stocks,
                "stocks_in_batch": len(symbols)
            }
        }
        
    except Exception as e:
        logger.error(f"Error starting US financial historical collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collect-all-us-financial")
async def collect_all_us_financial(background_tasks: BackgroundTasks,
                                 batch_size: int = 50,
                                 delay_seconds: int = 2,
                                 years_back: int = 0,
                                 interval_days: int = 30):
    """
    Collect financial data for ALL US stocks automatically in batches
    This will process all stocks without manual intervention
    
    Args:
        batch_size: Number of stocks per batch
        delay_seconds: Delay between batches
        years_back: How many years of historical data to collect (0 = only today)
        interval_days: Days between financial data points for historical data
    """
    try:
        # Get all US stocks
        db = get_mongodb_client()
        us_stocks = db.get_stock_list(market="US")
        
        if not us_stocks:
            # Try to collect stock list first
            logger.warning("No US stocks found. Collecting stock list first...")
            collector = StockDataCollector()
            collector.collect_us_stock_list()  # Sync call to ensure list is ready
            
            # Retry getting stocks
            us_stocks = db.get_stock_list(market="US")
            if not us_stocks:
                raise HTTPException(
                    status_code=404,
                    detail="Failed to collect US stock list. Please check the connection."
                )
        
        collector = StockDataCollector()
        total_stocks = len(us_stocks)
        
        # Determine date range
        end_date = datetime.now()
        if years_back > 0:
            start_date = end_date - timedelta(days=365 * years_back)
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
        else:
            # Only collect today's data
            start_str = end_str = end_date.strftime("%Y-%m-%d")
        
        # Process all stocks in batches
        batch_count = 0
        for i in range(0, total_stocks, batch_size):
            batch_stocks = us_stocks[i:i + batch_size]
            symbols = [stock["symbol"] for stock in batch_stocks]
            
            # Add delay between batches to avoid overwhelming the API
            if batch_count > 0:
                import asyncio
                await asyncio.sleep(delay_seconds)
            
            if years_back > 0:
                # Collect historical data with intervals
                background_tasks.add_task(
                    collector.collect_us_financial_data_range,
                    symbols,
                    start_str,
                    end_str,
                    interval_days
                )
            else:
                # Collect only today's data
                background_tasks.add_task(
                    collector.collect_us_financial_data,
                    symbols,
                    end_str
                )
            batch_count += 1
        
        message = f"US financial data collection started for ALL {total_stocks} stocks in {batch_count} batches"
        if years_back > 0:
            message += f" ({years_back} years of data with {interval_days}-day intervals)"
        
        return CollectionResponse(
            status="started",
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting complete US financial collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))