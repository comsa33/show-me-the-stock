"""
캐시 관리 모듈
Redis 기반 고성능 캐싱 시스템
"""

import pickle
from functools import wraps
from typing import Any, Optional

import redis.asyncio as redis
from app.core.config import get_settings

# Redis 클라이언트 인스턴스
redis_client: Optional[redis.Redis] = None


async def init_redis():
    """Redis 연결 초기화"""
    global redis_client
    settings = get_settings()

    try:
        redis_client = redis.from_url(
            settings.redis_url,
            password=settings.redis_password,
            decode_responses=False,  # bytes로 받아서 pickle 사용
            socket_connect_timeout=5,
            socket_keepalive=True,
            health_check_interval=30,
        )

        # 연결 테스트
        await redis_client.ping()
        print("✅ Redis connected successfully")

    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        redis_client = None


async def get_redis() -> Optional[redis.Redis]:
    """Redis 클라이언트 반환"""
    global redis_client
    if redis_client is None:
        await init_redis()
    return redis_client


class CacheManager:
    """캐시 관리자 클래스"""

    def __init__(self):
        self.settings = get_settings()

    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        if not self.settings.cache_enabled:
            return None

        client = await get_redis()
        if client is None:
            return None

        try:
            cached_data = await client.get(key)
            if cached_data:
                return pickle.loads(cached_data)
        except Exception as e:
            print(f"Cache get error: {e}")

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """캐시에 값 저장"""
        if not self.settings.cache_enabled:
            return False

        client = await get_redis()
        if client is None:
            return False

        try:
            ttl = ttl or self.settings.cache_ttl
            serialized_data = pickle.dumps(value)
            await client.setex(key, ttl, serialized_data)
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """캐시에서 값 삭제"""
        client = await get_redis()
        if client is None:
            return False

        try:
            await client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """패턴 매칭으로 캐시 삭제"""
        client = await get_redis()
        if client is None:
            return 0

        try:
            keys = await client.keys(pattern)
            if keys:
                return await client.delete(*keys)
            return 0
        except Exception as e:
            print(f"Cache clear pattern error: {e}")
            return 0


# 전역 캐시 매니저 인스턴스
cache_manager = CacheManager()


def cached(ttl: int = None, key_prefix: str = ""):
    """
    함수 결과를 캐시하는 데코레이터

    Args:
        ttl: 캐시 유지 시간 (초)
        key_prefix: 캐시 키 접두사
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # 캐시에서 조회
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 함수 실행
            result = await func(*args, **kwargs)

            # 결과 캐시
            await cache_manager.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


# 자주 사용되는 캐시 키 패턴
class CacheKeys:
    """캐시 키 상수"""

    STOCK_DATA = "stock_data:{symbol}:{period}"
    MARKET_STATUS = "market_status"
    INTEREST_RATES = "interest_rates:{country}"
    STOCK_LIST = "stock_list:{market}"
    AI_ANALYSIS = "ai_analysis:{symbol}:{analysis_type}"
    USER_FAVORITES = "user_favorites:{user_id}"
