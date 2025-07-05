"""
Stock Dashboard FastAPI Application
"""

from app.api.v1.api import api_router
from app.core.config import get_settings
from app.services.realtime_service import realtime_service
from app.services.cache_scheduler import cache_scheduler
from app.core.cache import init_redis
from app.collectors.scheduler import get_scheduler
from app.database.mongodb_client import get_mongodb_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

settings = get_settings()

app = FastAPI(
    title="Stock Dashboard API",
    description="AI-powered stock analysis dashboard backend with ML predictions",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api/v1")

# 로거 설정
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행되는 이벤트"""
    try:
        # Redis 초기화
        logger.info("Redis 초기화 중...")
        await init_redis()
        
        # 실시간 서비스 초기화
        logger.info("실시간 주식 알림 서비스 초기화 중...")
        await realtime_service.initialize()
        await realtime_service.start_monitoring()
        logger.info("실시간 주식 알림 서비스가 성공적으로 시작되었습니다.")
        
        # 캐시 스케줄러 시작
        logger.info("캐시 스케줄러 시작 중...")
        cache_scheduler.start()
        logger.info("캐시 스케줄러가 성공적으로 시작되었습니다.")
        
        # MongoDB 사용 시 초기화
        if settings.use_mongodb and settings.mongodb_uri:
            logger.info("MongoDB 초기화 중...")
            try:
                mongodb_client = get_mongodb_client()
                mongodb_client.create_indexes()
                logger.info("MongoDB가 성공적으로 초기화되었습니다.")
                
                # 데이터 수집 스케줄러 시작
                logger.info("데이터 수집 스케줄러 시작 중...")
                data_scheduler = get_scheduler()
                data_scheduler.start()
                logger.info("데이터 수집 스케줄러가 성공적으로 시작되었습니다.")
            except Exception as mongo_error:
                logger.error(f"MongoDB 초기화 실패: {mongo_error}")
                logger.info("외부 API 모드로 전환합니다.")
                settings.use_mongodb = False
        
    except Exception as e:
        logger.error(f"서비스 시작 실패: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행되는 이벤트"""
    try:
        # 실시간 서비스 종료
        logger.info("실시간 주식 알림 서비스 종료 중...")
        await realtime_service.stop_monitoring()
        logger.info("실시간 주식 알림 서비스가 안전하게 종료되었습니다.")
        
        # 캐시 스케줄러 종료
        logger.info("캐시 스케줄러 종료 중...")
        cache_scheduler.stop()
        logger.info("캐시 스케줄러가 안전하게 종료되었습니다.")
        
        # MongoDB 사용 시 스케줄러 종료
        if settings.use_mongodb and settings.mongodb_uri:
            try:
                logger.info("데이터 수집 스케줄러 종료 중...")
                data_scheduler = get_scheduler()
                data_scheduler.stop()
                logger.info("데이터 수집 스케줄러가 안전하게 종료되었습니다.")
            except Exception as scheduler_error:
                logger.error(f"스케줄러 종료 중 오류: {scheduler_error}")
        
    except Exception as e:
        logger.error(f"서비스 종료 중 오류: {e}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Stock Dashboard API", "version": "2.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "stock-dashboard-backend",
        "version": "2.0.0",
    }


@app.get("/api/v1/stocks")
async def get_stocks():
    """Get stock list"""
    return {
        "stocks": [
            {"symbol": "AAPL", "name": "Apple Inc.", "price": 150.00},
            {"symbol": "GOOGL", "name": "Alphabet Inc.", "price": 2800.00},
            {"symbol": "MSFT", "name": "Microsoft Corporation", "price": 300.00},
        ]
    }


@app.get("/api/v1/market/status")
async def get_market_status():
    """Get market status"""
    return {"status": "open", "next_close": "16:00 EST", "timezone": "America/New_York"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
