"""
캐시 스케줄러 서비스
매일 00시에 종목 목록 캐시를 갱신
"""

import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.core.cache import cache_manager
from app.data.stock_data import StockDataFetcher

logger = logging.getLogger(__name__)


class CacheScheduler:
    """캐시 갱신 스케줄러"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.stock_fetcher = StockDataFetcher()
        self.is_running = False
    
    async def refresh_stock_list_cache(self):
        """종목 목록 캐시 갱신"""
        try:
            logger.info("Starting stock list cache refresh...")
            
            # 캐시 TTL 설정 (24시간)
            CACHE_TTL_24H = 86400
            
            # 기존 캐시 삭제
            deleted_count = await cache_manager.clear_pattern("stocks:list:simple:*")
            logger.info(f"Cleared {deleted_count} existing cache entries")
            
            # 각 시장별로 새로운 데이터를 캐시에 저장
            markets = ["KR", "US", "ALL"]
            
            for market in markets:
                try:
                    stocks = []
                    
                    if market in ["ALL", "KR"]:
                        kr_stocks = self.stock_fetcher.get_all_kr_stocks()
                        simple_kr_stocks = [
                            {
                                "symbol": stock["symbol"],
                                "name": stock["name"],
                                "market": "KR"
                            }
                            for stock in kr_stocks
                        ]
                        stocks.extend(simple_kr_stocks)
                    
                    if market in ["ALL", "US"]:
                        us_stocks = self.stock_fetcher.get_all_us_stocks()
                        simple_us_stocks = [
                            {
                                "symbol": stock["symbol"],
                                "name": stock["name"],
                                "market": "US"
                            }
                            for stock in us_stocks
                        ]
                        stocks.extend(simple_us_stocks)
                    
                    # 결과를 캐시에 저장
                    result = {
                        "market": market,
                        "total_count": len(stocks),
                        "stocks": stocks
                    }
                    
                    cache_key = f"stocks:list:simple:{market}"
                    await cache_manager.set(cache_key, result, ttl=CACHE_TTL_24H)
                    logger.info(f"Cached {len(stocks)} stocks for market: {market}")
                    
                except Exception as e:
                    logger.error(f"Failed to refresh cache for market {market}: {e}")
            
            logger.info("Stock list cache refresh completed successfully")
            
        except Exception as e:
            logger.error(f"Stock list cache refresh failed: {e}")
    
    def start(self):
        """스케줄러 시작"""
        if self.is_running:
            logger.warning("Cache scheduler is already running")
            return
        
        try:
            # 매일 00시에 실행하는 크론 작업 추가
            self.scheduler.add_job(
                self.refresh_stock_list_cache,
                CronTrigger(hour=0, minute=0),
                id="refresh_stock_cache",
                name="Refresh stock list cache",
                replace_existing=True,
                misfire_grace_time=3600  # 1시간까지 지연 실행 허용
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info("Cache scheduler started successfully")
            
            # 시작 시 한 번 캐시 갱신 (선택사항)
            asyncio.create_task(self.refresh_stock_list_cache())
            
        except Exception as e:
            logger.error(f"Failed to start cache scheduler: {e}")
            self.is_running = False
    
    def stop(self):
        """스케줄러 중지"""
        if not self.is_running:
            logger.warning("Cache scheduler is not running")
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Cache scheduler stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop cache scheduler: {e}")


# 전역 스케줄러 인스턴스
cache_scheduler = CacheScheduler()