from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict, Any
import logging
from app.services.ai_recommendation_service import ai_recommendation_service

# 로거 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai-recommendations", tags=["AI Recommendations"])

@router.get("/top-stocks")
async def get_ai_recommendations(
    market: str = Query("KR", description="시장 (KR: 한국, US: 미국)"),
    top_n: int = Query(6, ge=1, le=10, description="추천 종목 수 (1-10)")
) -> Dict[str, Any]:
    """
    퀀트 지표 기반 AI 종목 추천
    
    - 퀀트 점수 상위 종목을 AI가 분석하여 추천
    - 예상 수익률, 위험도, 추천 이유 등 상세 정보 제공
    - 1시간마다 캐시 갱신
    """
    try:
        recommendations = await ai_recommendation_service.get_ai_recommendations(
            market=market,
            top_n=top_n
        )
        
        return {
            "success": True,
            "market": market,
            "count": len(recommendations),
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"AI recommendation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"AI 추천 생성 중 오류가 발생했습니다: {str(e)}"
        )