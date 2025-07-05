"""
Stock Data Collection Scheduler
Schedules daily data collection for Korean and US markets
"""
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from .stock_data_collector import StockDataCollector

logger = logging.getLogger(__name__)


class DataCollectionScheduler:
    """Manages scheduled data collection tasks"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.collector = StockDataCollector()
        self.kr_tz = pytz.timezone('Asia/Seoul')
        self.us_tz = pytz.timezone('America/New_York')
        
        # Popular US stocks to collect
        self.us_stocks = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "BRK-B",
            "JPM", "JNJ", "V", "PG", "UNH", "HD", "MA", "DIS", "PYPL", "BAC",
            "ADBE", "CMCSA", "NFLX", "PFE", "INTC", "VZ", "PEP", "KO", "T",
            "NKE", "XOM", "CSCO", "MRK", "ABT", "TMO", "ABBV", "CRM", "WMT",
            "CVX", "ACN", "MCD", "COST", "NEE", "DHR", "MDT", "LLY", "BMY",
            "UNP", "QCOM", "TXN", "HON", "PM", "LIN", "ORCL", "IBM", "AMD",
            "GE", "CAT", "BA", "MMM", "AMGN", "SBUX", "RTX", "NOW", "GS",
            "BLK", "ISRG", "SPGI", "DE", "GILD", "CVS", "BKNG", "MDLZ", "ZTS",
            "SCHW", "MO", "ADP", "TGT", "CI", "INTU", "SYK", "ANTM", "LMT"
        ]
    
    def setup_jobs(self):
        """Setup scheduled jobs"""
        logger.info("Setting up data collection jobs...")
        
        # Korean market daily collection - 6:00 PM KST (after market close)
        self.scheduler.add_job(
            self.collect_korean_daily_data,
            CronTrigger(
                hour=18,
                minute=0,
                timezone=self.kr_tz,
                day_of_week='mon-fri'
            ),
            id='kr_daily_collection',
            name='Korean Market Daily Collection',
            misfire_grace_time=3600
        )
        
        # US market daily collection - 5:00 PM EST (1 hour after market close)
        self.scheduler.add_job(
            self.collect_us_daily_data,
            CronTrigger(
                hour=17,
                minute=0,
                timezone=self.us_tz,
                day_of_week='mon-fri'
            ),
            id='us_daily_collection',
            name='US Market Daily Collection',
            misfire_grace_time=3600
        )
        
        # Korean financial data collection - 6:30 PM KST
        self.scheduler.add_job(
            self.collect_korean_financial_data,
            CronTrigger(
                hour=18,
                minute=30,
                timezone=self.kr_tz,
                day_of_week='mon-fri'
            ),
            id='kr_financial_collection',
            name='Korean Financial Data Collection',
            misfire_grace_time=3600
        )
        
        # US financial data collection - 5:30 PM EST
        self.scheduler.add_job(
            self.collect_us_financial_data,
            CronTrigger(
                hour=17,
                minute=30,
                timezone=self.us_tz,
                day_of_week='mon-fri'
            ),
            id='us_financial_collection',
            name='US Financial Data Collection',
            misfire_grace_time=3600
        )
        
        # Indices collection - 7:00 PM KST for both markets
        self.scheduler.add_job(
            self.collect_indices_data,
            CronTrigger(
                hour=19,
                minute=0,
                timezone=self.kr_tz,
                day_of_week='mon-fri'
            ),
            id='indices_collection',
            name='Market Indices Collection',
            misfire_grace_time=3600
        )
        
        logger.info("All jobs scheduled successfully")
    
    def collect_korean_daily_data(self):
        """Collect Korean market daily data"""
        try:
            logger.info("Starting Korean market daily collection...")
            
            # Check if today is a trading day
            today = datetime.now(self.kr_tz)
            if self._is_korean_holiday(today):
                logger.info("Today is a Korean holiday, skipping collection")
                return
            
            # Collect data
            self.collector.collect_kr_daily_prices()
            
            logger.info("Korean market daily collection completed")
            
        except Exception as e:
            logger.error(f"Error in Korean daily collection: {e}")
    
    def collect_us_daily_data(self):
        """Collect US market daily data"""
        try:
            logger.info("Starting US market daily collection...")
            
            # Check if today is a trading day
            today = datetime.now(self.us_tz)
            if self._is_us_holiday(today):
                logger.info("Today is a US holiday, skipping collection")
                return
            
            # Collect data
            self.collector.collect_us_daily_prices(self.us_stocks)
            
            logger.info("US market daily collection completed")
            
        except Exception as e:
            logger.error(f"Error in US daily collection: {e}")
    
    def collect_korean_financial_data(self):
        """Collect Korean financial data"""
        try:
            logger.info("Starting Korean financial data collection...")
            
            today = datetime.now(self.kr_tz)
            if self._is_korean_holiday(today):
                logger.info("Today is a Korean holiday, skipping collection")
                return
            
            self.collector.collect_kr_financial_data()
            
            logger.info("Korean financial data collection completed")
            
        except Exception as e:
            logger.error(f"Error in Korean financial collection: {e}")
    
    def collect_us_financial_data(self):
        """Collect US financial data"""
        try:
            logger.info("Starting US financial data collection...")
            
            today = datetime.now(self.us_tz)
            if self._is_us_holiday(today):
                logger.info("Today is a US holiday, skipping collection")
                return
            
            # Use the same stocks as daily collection
            self.collector.collect_us_financial_data(self.us_stocks)
            
            logger.info("US financial data collection completed")
            
        except Exception as e:
            logger.error(f"Error in US financial collection: {e}")
    
    def collect_indices_data(self):
        """Collect market indices data"""
        try:
            logger.info("Starting indices data collection...")
            
            self.collector.collect_indices_data()
            
            logger.info("Indices data collection completed")
            
        except Exception as e:
            logger.error(f"Error in indices collection: {e}")
    
    def _is_korean_holiday(self, date: datetime) -> bool:
        """Check if date is Korean market holiday"""
        # Simple weekend check for now
        # TODO: Add proper Korean holiday calendar
        return date.weekday() >= 5  # Saturday or Sunday
    
    def _is_us_holiday(self, date: datetime) -> bool:
        """Check if date is US market holiday"""
        # Simple weekend check for now
        # TODO: Add proper US market holiday calendar
        return date.weekday() >= 5  # Saturday or Sunday
    
    def start(self):
        """Start the scheduler"""
        self.setup_jobs()
        self.scheduler.start()
        logger.info("Data collection scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Data collection scheduler stopped")
    
    def get_jobs(self):
        """Get list of scheduled jobs"""
        return self.scheduler.get_jobs()


# Global scheduler instance
_scheduler = None


def get_scheduler() -> DataCollectionScheduler:
    """Get scheduler singleton"""
    global _scheduler
    if _scheduler is None:
        _scheduler = DataCollectionScheduler()
    return _scheduler