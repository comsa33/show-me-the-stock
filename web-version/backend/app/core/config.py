"""
설정 관리 모듈
환경변수 기반 설정 및 Pydantic 검증
"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 기본 설정
    app_name: str = "Stock Dashboard API"
    environment: str = Field(
        default="development", description="환경 (development, production)"
    )
    debug: bool = Field(default=True, description="디버그 모드")

    # 서버 설정
    host: str = Field(default="0.0.0.0", description="서버 호스트")
    port: int = Field(default=8000, description="서버 포트")

    # CORS 설정
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="허용된 CORS 오리진",
    )

    # Redis 설정
    redis_url: str = Field(default="redis://localhost:6379", description="Redis URL")
    redis_host: str = Field(default="localhost", description="Redis 호스트")
    redis_port: int = Field(default=6379, description="Redis 포트")
    redis_db: int = Field(default=0, description="Redis 데이터베이스 번호")
    redis_password: str = Field(default="", description="Redis 비밀번호")

    # 캐시 설정
    cache_ttl: int = Field(default=300, description="캐시 TTL (초)")
    cache_enabled: bool = Field(default=True, description="캐시 활성화")

    # 외부 API 설정
    gemini_api_key: str = Field(default="", description="Gemini AI API 키")
    alpha_vantage_api_key: str = Field(default="", description="Alpha Vantage API 키")

    # 레이트 리미팅
    rate_limit_requests: int = Field(default=100, description="분당 요청 수 제한")
    rate_limit_window: int = Field(default=60, description="레이트 리미팅 윈도우 (초)")

    # 로깅
    log_level: str = Field(default="INFO", description="로그 레벨")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="로그 포맷",
    )

    # 보안 설정
    secret_key: str = Field(
        default="your-secret-key-change-in-production", description="JWT 서명용 비밀키"
    )
    access_token_expire_minutes: int = Field(
        default=30, description="액세스 토큰 만료 시간 (분)"
    )

    # 데이터 설정
    stock_data_cache_ttl: int = Field(
        default=60, description="주식 데이터 캐시 TTL (초)"
    )
    max_chart_points: int = Field(default=1000, description="차트 최대 데이터 포인트")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """설정 싱글톤 인스턴스 반환"""
    return Settings()
