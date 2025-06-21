"""
API v1 라우터
모든 API 엔드포인트를 통합 관리
"""

from fastapi import APIRouter
from app.api.v1.endpoints import stocks, stocks_v2, interest_rates

api_router = APIRouter()

# 각 모듈별 라우터 등록
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(stocks_v2.router, prefix="/stocks/v2", tags=["stocks-v2"])
api_router.include_router(interest_rates.router, prefix="/interest-rates", tags=["interest-rates"])
# TODO: AI 분석 및 예측 기능은 추후 활성화
# api_router.include_router(ai_analysis.router, prefix="/ai", tags=["ai-analysis"])
# api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])