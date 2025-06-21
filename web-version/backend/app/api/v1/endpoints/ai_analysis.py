"""
AI 분석 관련 API 엔드포인트
"""

from datetime import datetime
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.ai.gemini_analyzer import GeminiStockAnalyzer
from app.data.stock_data import StockDataFetcher
from app.models.stock import MarketType
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

# 글로벌 인스턴스
stock_fetcher = StockDataFetcher()
ai_analyzer = GeminiStockAnalyzer()


@router.get("/{symbol}/basic")
async def get_basic_analysis(
    symbol: str,
    market: MarketType = Query(..., description="시장 타입: KR, US")
):
    """기본 AI 주식 분석"""
    try:
        # 주식 데이터 가져오기
        data = stock_fetcher.get_stock_data(symbol, "3mo", market.value.lower())
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="주식 데이터를 찾을 수 없습니다")
        
        # AI 분석 수행
        analysis = ai_analyzer.analyze_stock(data, symbol, market.value.lower())
        
        return {
            "symbol": symbol,
            "market": market,
            "analysis_type": "basic",
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"기본 분석 실패: {str(e)}")


@router.get("/{symbol}/technical")
async def get_technical_analysis(
    symbol: str,
    market: MarketType = Query(..., description="시장 타입: KR, US")
):
    """기술적 지표 AI 분석"""
    try:
        # 주식 데이터 가져오기
        data = stock_fetcher.get_stock_data(symbol, "6mo", market.value.lower())
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="주식 데이터를 찾을 수 없습니다")
        
        # 기술적 지표 AI 분석 수행
        analysis = ai_analyzer.analyze_technical_indicators(data, symbol, market.value.lower())
        
        return {
            "symbol": symbol,
            "market": market,
            "analysis_type": "technical",
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"기술적 분석 실패: {str(e)}")


@router.get("/{symbol}/market-insights")
async def get_market_insights(
    symbol: str,
    market: MarketType = Query(..., description="시장 타입: KR, US")
):
    """시장 인사이트 AI 분석"""
    try:
        # 주식 데이터 가져오기
        data = stock_fetcher.get_stock_data(symbol, "1y", market.value.lower())
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="주식 데이터를 찾을 수 없습니다")
        
        # 시장 인사이트 AI 분석 수행
        analysis = ai_analyzer.analyze_market_insights(data, symbol, market.value.lower())
        
        return {
            "symbol": symbol,
            "market": market,
            "analysis_type": "market_insights",
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시장 인사이트 분석 실패: {str(e)}")


@router.get("/{symbol}/comprehensive")
async def get_comprehensive_analysis(
    symbol: str,
    market: MarketType = Query(..., description="시장 타입: KR, US")
):
    """종합 AI 분석 (모든 분석 타입 포함)"""
    try:
        # 주식 데이터 가져오기
        data = stock_fetcher.get_stock_data(symbol, "1y", market.value.lower())
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="주식 데이터를 찾을 수 없습니다")
        
        # 모든 분석 수행
        basic_analysis = ai_analyzer.analyze_stock(data, symbol, market.value.lower())
        technical_analysis = ai_analyzer.analyze_technical_indicators(data, symbol, market.value.lower())
        market_insights = ai_analyzer.analyze_market_insights(data, symbol, market.value.lower())
        
        return {
            "symbol": symbol,
            "market": market,
            "analysis_type": "comprehensive",
            "analyses": {
                "basic": basic_analysis,
                "technical": technical_analysis,
                "market_insights": market_insights
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"종합 분석 실패: {str(e)}")


@router.get("/market/overview")
async def get_market_overview(
    market: MarketType = Query(..., description="시장 타입: KR, US")
):
    """시장 전체 AI 분석"""
    try:
        # 주요 주식들의 데이터 가져오기
        if market == MarketType.KR:
            major_stocks = ["005930", "000660", "035420"]  # 삼성전자, SK하이닉스, NAVER
        else:
            major_stocks = ["AAPL", "MSFT", "GOOGL"]  # Apple, Microsoft, Google
        
        market_data = {}
        for symbol in major_stocks:
            data = stock_fetcher.get_stock_data(symbol, "1mo", market.value.lower())
            if data is not None and not data.empty:
                market_data[symbol] = data
        
        if not market_data:
            raise HTTPException(status_code=404, detail="시장 데이터를 찾을 수 없습니다")
        
        # 시장 전체 분석 수행
        overview = ai_analyzer.analyze_market_overview(market_data, market.value.lower())
        
        return {
            "market": market,
            "analysis_type": "market_overview",
            "overview": overview,
            "analyzed_stocks": list(market_data.keys()),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시장 개요 분석 실패: {str(e)}")