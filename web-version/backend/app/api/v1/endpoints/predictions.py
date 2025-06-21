"""
AI 예측 관련 API 엔드포인트
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.models.hybrid_model import HybridStockPredictor
from app.models.backtesting import BacktestEngine
from app.data.stock_data import StockDataFetcher
from app.models.stock import MarketType
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

# 글로벌 인스턴스
stock_fetcher = StockDataFetcher()
predictor = HybridStockPredictor()
backtester = BacktestEngine()


@router.get("/{symbol}/price-prediction")
async def predict_stock_price(
    symbol: str,
    market: MarketType = Query(..., description="시장 타입: KR, US"),
    days: int = Query(7, ge=1, le=30, description="예측 일수: 1-30일")
):
    """주가 예측"""
    try:
        # 주식 데이터 가져오기
        data = stock_fetcher.get_stock_data(symbol, "2y", market.value.lower())
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="주식 데이터를 찾을 수 없습니다")
        
        # 예측 수행
        predictions = predictor.predict_future_prices(data, days)
        
        return {
            "symbol": symbol,
            "market": market,
            "prediction_days": days,
            "predictions": predictions,
            "model_info": {
                "type": "hybrid",
                "components": ["VAE", "Transformer", "LSTM"],
                "ensemble": True
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"가격 예측 실패: {str(e)}")


@router.get("/{symbol}/trend-prediction")
async def predict_stock_trend(
    symbol: str,
    market: MarketType = Query(..., description="시장 타입: KR, US"),
    horizon: int = Query(14, ge=1, le=60, description="예측 기간: 1-60일")
):
    """주가 트렌드 예측"""
    try:
        # 주식 데이터 가져오기
        data = stock_fetcher.get_stock_data(symbol, "1y", market.value.lower())
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="주식 데이터를 찾을 수 없습니다")
        
        # 트렌드 예측 수행
        trend_prediction = predictor.predict_trend(data, horizon)
        
        return {
            "symbol": symbol,
            "market": market,
            "prediction_horizon": horizon,
            "trend": trend_prediction,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"트렌드 예측 실패: {str(e)}")


@router.get("/{symbol}/volatility-prediction")
async def predict_volatility(
    symbol: str,
    market: MarketType = Query(..., description="시장 타입: KR, US"),
    days: int = Query(7, ge=1, le=30, description="예측 일수: 1-30일")
):
    """변동성 예측"""
    try:
        # 주식 데이터 가져오기
        data = stock_fetcher.get_stock_data(symbol, "1y", market.value.lower())
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="주식 데이터를 찾을 수 없습니다")
        
        # 변동성 예측 수행
        volatility_prediction = predictor.predict_volatility(data, days)
        
        return {
            "symbol": symbol,
            "market": market,
            "prediction_days": days,
            "volatility": volatility_prediction,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"변동성 예측 실패: {str(e)}")


@router.post("/{symbol}/backtest")
async def run_backtest(
    symbol: str,
    market: MarketType = Query(..., description="시장 타입: KR, US"),
    start_date: str = Query(..., description="백테스트 시작일 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="백테스트 종료일 (YYYY-MM-DD)"),
    strategy: str = Query("buy_and_hold", description="투자 전략")
):
    """백테스팅 실행"""
    try:
        # 주식 데이터 가져오기
        data = stock_fetcher.get_stock_data(symbol, "max", market.value.lower())
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="주식 데이터를 찾을 수 없습니다")
        
        # 백테스트 실행
        results = backtester.run_backtest(
            data=data,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            strategy=strategy
        )
        
        return {
            "symbol": symbol,
            "market": market,
            "backtest_period": {
                "start": start_date,
                "end": end_date
            },
            "strategy": strategy,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"백테스트 실패: {str(e)}")


@router.get("/{symbol}/risk-analysis")
async def analyze_risk(
    symbol: str,
    market: MarketType = Query(..., description="시장 타입: KR, US"),
    confidence_level: float = Query(0.95, ge=0.9, le=0.99, description="신뢰도")
):
    """리스크 분석"""
    try:
        # 주식 데이터 가져오기
        data = stock_fetcher.get_stock_data(symbol, "1y", market.value.lower())
        if data is None or data.empty:
            raise HTTPException(status_code=404, detail="주식 데이터를 찾을 수 없습니다")
        
        # 리스크 분석 수행
        risk_analysis = predictor.analyze_risk(data, confidence_level)
        
        return {
            "symbol": symbol,
            "market": market,
            "confidence_level": confidence_level,
            "risk_metrics": risk_analysis,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"리스크 분석 실패: {str(e)}")


@router.get("/model/performance")
async def get_model_performance():
    """모델 성능 지표 조회"""
    try:
        performance = predictor.get_model_performance()
        
        return {
            "model_type": "hybrid",
            "components": ["VAE", "Transformer", "LSTM"],
            "performance_metrics": performance,
            "last_updated": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"모델 성능 조회 실패: {str(e)}")