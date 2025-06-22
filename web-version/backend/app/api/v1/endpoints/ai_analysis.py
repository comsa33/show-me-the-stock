"""
AI 분석 관련 API 엔드포인트 - Google Gemini 통합
"""

import logging
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, Query
from app.services.ai_analysis import gemini_analyzer

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/stock/analyze")
async def analyze_stock(
    symbol: str,
    market: str = Query(..., description="시장 (KR/US)"),
    analysis_type: str = Query("beginner", description="분석 타입 (beginner/swing/invest)"),
):
    """
    Google Gemini를 사용한 AI 주식 분석
    Args:
        symbol: 종목 코드
        market: 시장 구분 (KR/US)
        analysis_type: 분석 타입 (beginner: 3일, swing: 1개월, invest: 3개월)
    """
    try:
        logger.info(f"Starting AI analysis for {symbol} ({market}) - {analysis_type}")
        
        # Gemini AI 분석 실행
        analysis_result = await gemini_analyzer.analyze_stock(symbol, market, analysis_type)
        
        # Pydantic 모델을 딕셔너리로 변환
        analysis_dict = analysis_result.model_dump()
        
        return {
            "symbol": symbol,
            "market": market,
            "analysis_type": analysis_type,
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis_dict,
            "ai_provider": "Google Gemini 2.5 Flash" if gemini_analyzer.client else "Mock Data"
        }

    except Exception as e:
        logger.error(f"AI 분석 중 오류 발생 ({symbol}): {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"AI 분석 중 오류 발생: {str(e)}"
        )


@router.get("/stock/analysis-history/{symbol}")
async def get_analysis_history(
    symbol: str,
    market: str = Query(..., description="시장 (KR/US)"),
    limit: int = Query(default=10, ge=1, le=50, description="결과 수 제한"),
):
    """
    종목별 분석 히스토리 조회 (향후 구현 예정)
    """
    # TODO: 실제 구현에서는 데이터베이스에서 과거 분석 결과를 조회
    return {
        "symbol": symbol,
        "market": market,
        "history": [],
        "message": "분석 히스토리 기능은 향후 구현 예정입니다."
    }


@router.get("/market/sentiment")
async def get_market_sentiment(
    market: str = Query(default="ALL", description="시장 (KR/US/ALL)"),
):
    """
    시장 전체 감성 분석 (향후 구현 예정)
    """
    try:
        from datetime import datetime
        import random
        
        # Mock 시장 감성 데이터
        sentiments = {}
        
        if market.upper() in ["ALL", "KR"]:
            sentiments["KR"] = {
                "sentiment": random.choice(["긍정", "부정", "중립"]),
                "score": random.randint(40, 80),
                "trend": random.choice(["상승", "하락", "횡보"]),
                "confidence": f"{random.randint(65, 85)}%"
            }
        
        if market.upper() in ["ALL", "US"]:
            sentiments["US"] = {
                "sentiment": random.choice(["긍정", "부정", "중립"]),
                "score": random.randint(40, 80),
                "trend": random.choice(["상승", "하락", "횡보"]),
                "confidence": f"{random.randint(65, 85)}%"
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "market": market.upper(),
            "sentiments": sentiments,
            "note": "실제 구현에서는 Gemini API로 시장 뉴스를 분석합니다."
        }
        
    except Exception as e:
        logger.error(f"시장 감성 분석 중 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"시장 감성 분석 중 오류 발생: {str(e)}"
        )
