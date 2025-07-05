"""
Stock Service Factory
Returns appropriate stock service based on configuration
"""
from typing import Union
from ..core.config import get_settings
from ..services.mongodb_stock_service import get_mongodb_stock_service, MongoDBStockService
from ..data.pykrx_stock_data import PykrxStockDataFetcher
from ..core.redis_client import RedisClient
import logging

logger = logging.getLogger(__name__)


class StockServiceFactory:
    """Factory for creating stock service instances"""
    
    @staticmethod
    def get_service() -> Union[MongoDBStockService, PykrxStockDataFetcher]:
        """Get appropriate stock service based on configuration"""
        settings = get_settings()
        
        if settings.use_mongodb and settings.mongodb_uri:
            logger.info("Using MongoDB stock service")
            return get_mongodb_stock_service()
        else:
            logger.info("Using external API stock service (pykrx)")
            redis_client = RedisClient.get_instance()
            return PykrxStockDataFetcher(redis_client=redis_client)
    
    @staticmethod
    def is_using_mongodb() -> bool:
        """Check if MongoDB is being used"""
        settings = get_settings()
        return settings.use_mongodb and settings.mongodb_uri is not None