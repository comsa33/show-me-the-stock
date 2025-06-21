import redis
import logging
from typing import Optional
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class RedisClient:
    _instance: Optional[redis.Redis] = None
    
    @classmethod
    def get_instance(cls) -> Optional[redis.Redis]:
        """Redis 클라이언트 싱글톤 인스턴스 반환"""
        if cls._instance is None:
            try:
                settings = get_settings()
                cls._instance = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
                # 연결 테스트
                cls._instance.ping()
                logger.info("Redis connection established successfully")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                cls._instance = None
                
        return cls._instance
    
    @classmethod
    def is_available(cls) -> bool:
        """Redis 사용 가능 여부 확인"""
        return cls.get_instance() is not None