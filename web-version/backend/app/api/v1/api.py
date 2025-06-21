"""
API v1 라우터
모든 API 엔드포인트를 통합 관리
"""

from fastapi import APIRouter
from app.api.v1.endpoints import stocks, market, favorites, charts

api_router = APIRouter()

# 각 모듈별 라우터 등록
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(market.router, prefix="/market", tags=["market"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["favorites"])
api_router.include_router(charts.router, prefix="/charts", tags=["charts"])