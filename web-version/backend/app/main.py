"""
Stock Dashboard Backend - FastAPI Application
고성능 주식 분석 API 서버
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import get_settings
from app.core.cache import init_redis
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 시 실행되는 라이프사이클 이벤트"""
    # 시작 시
    settings = get_settings()
    
    # Redis 연결 초기화
    await init_redis()
    
    print("🚀 Stock Dashboard API Server started!")
    print(f"📊 Environment: {settings.environment}")
    print(f"🔗 CORS Origins: {settings.allowed_origins}")
    
    yield
    
    # 종료 시
    print("🔚 Stock Dashboard API Server stopped!")


# FastAPI 앱 생성
app = FastAPI(
    title="Stock Dashboard API",
    description="📈 모던 주식 분석 대시보드 API",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 설정 로드
settings = get_settings()

# 미들웨어 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# API 라우터 등록
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """API 서버 상태 확인"""
    return {
        "message": "📈 Stock Dashboard API Server",
        "version": "2.0.0",
        "status": "running",
        "environment": settings.environment,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "timestamp": "2024-12-21"
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )