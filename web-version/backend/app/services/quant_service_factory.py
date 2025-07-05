"""
Quant Service Factory
Returns appropriate quant service based on configuration
"""
from typing import Union
from ..core.config import get_settings
from .mongodb_quant_service import get_mongodb_quant_service, MongoDBQuantService
from .limited_quant_service import limited_quant_service, LimitedQuantService
import logging

logger = logging.getLogger(__name__)


class QuantServiceFactory:
    """Factory for creating quant service instances"""
    
    @staticmethod
    def get_service() -> Union[MongoDBQuantService, LimitedQuantService]:
        """Get appropriate quant service based on configuration"""
        settings = get_settings()
        
        if settings.use_mongodb and settings.mongodb_uri:
            logger.info("Using MongoDB quant service")
            return get_mongodb_quant_service()
        else:
            logger.info("Using external API quant service")
            return limited_quant_service
    
    @staticmethod
    def is_using_mongodb() -> bool:
        """Check if MongoDB is being used"""
        settings = get_settings()
        return settings.use_mongodb and settings.mongodb_uri is not None