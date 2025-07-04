"""
API v1 라우터
모든 API 엔드포인트를 통합 관리
"""

from app.api.v1.endpoints import ai_analysis, interest_rates, stocks, stocks_v2, quant, indices, realtime, news
from app.api.v1 import ai_recommendations, backtest
from fastapi import APIRouter

api_router = APIRouter()

# 각 모듈별 라우터 등록
api_router.include_router(stocks.router, prefix="/stocks", tags=["stocks"])
api_router.include_router(stocks_v2.router, prefix="/stocks/v2", tags=["stocks-v2"])
api_router.include_router(
    interest_rates.router, prefix="/interest-rates", tags=["interest-rates"]
)
api_router.include_router(ai_analysis.router, prefix="/ai", tags=["ai-analysis"])
api_router.include_router(quant.router, prefix="/quant", tags=["quant-analysis"])
api_router.include_router(indices.router, prefix="/indices", tags=["indices"])
api_router.include_router(realtime.router, prefix="/stocks", tags=["realtime"])
api_router.include_router(news.router, prefix="/news", tags=["news"])
api_router.include_router(ai_recommendations.router, tags=["ai-recommendations"])
api_router.include_router(backtest.router, tags=["backtest"])
# api_router.include_router(predictions.router, prefix="/predictions", tags=["predictions"])
