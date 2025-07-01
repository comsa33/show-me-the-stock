"""
퀀트 투자 분석 API 엔드포인트
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
import logging

from app.services.quant_service import quant_service, QuantIndicator, BacktestResult
from app.services.recommendation_service import recommendation_service, InvestmentProfile, StockRecommendation, PortfolioRecommendation

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/indicators", response_model=List[QuantIndicator])
async def get_quant_indicators(
    market: str = Query("KR", description="시장 (KR/US)"),
    limit: int = Query(50, description="반환할 종목 수", ge=1, le=100),
    sort_by: str = Query("quant_score", description="정렬 기준"),
    sort_order: str = Query("desc", description="정렬 순서 (asc/desc)"),
    per_min: Optional[float] = Query(None, description="PER 최소값"),
    per_max: Optional[float] = Query(None, description="PER 최대값"),
    pbr_min: Optional[float] = Query(None, description="PBR 최소값"),
    pbr_max: Optional[float] = Query(None, description="PBR 최대값"),
    roe_min: Optional[float] = Query(None, description="ROE 최소값"),
    roe_max: Optional[float] = Query(None, description="ROE 최대값"),
):
    """
    퀀트 지표 조회
    
    주요 재무 지표와 기술적 지표를 계산하여 종합 퀀트 점수와 함께 반환합니다.
    """
    try:
        # 퀀트 지표 데이터 가져오기
        indicators = await quant_service.get_quant_indicators(market, limit * 2)  # 필터링을 위해 더 많이 가져옴
        
        # 필터링 적용
        filtered_indicators = []
        for indicator in indicators:
            include = True
            
            if per_min is not None and indicator.per < per_min:
                include = False
            if per_max is not None and indicator.per > per_max:
                include = False
            if pbr_min is not None and indicator.pbr < pbr_min:
                include = False
            if pbr_max is not None and indicator.pbr > pbr_max:
                include = False
            if roe_min is not None and indicator.roe < roe_min:
                include = False
            if roe_max is not None and indicator.roe > roe_max:
                include = False
            
            if include:
                filtered_indicators.append(indicator)
        
        # 정렬 적용
        reverse = sort_order.lower() == "desc"
        
        if sort_by == "quant_score":
            filtered_indicators.sort(key=lambda x: x.quant_score, reverse=reverse)
        elif sort_by == "per":
            filtered_indicators.sort(key=lambda x: x.per, reverse=reverse)
        elif sort_by == "pbr":
            filtered_indicators.sort(key=lambda x: x.pbr, reverse=reverse)
        elif sort_by == "roe":
            filtered_indicators.sort(key=lambda x: x.roe, reverse=reverse)
        elif sort_by == "roa":
            filtered_indicators.sort(key=lambda x: x.roa, reverse=reverse)
        elif sort_by == "momentum_3m":
            filtered_indicators.sort(key=lambda x: x.momentum_3m, reverse=reverse)
        elif sort_by == "volatility":
            filtered_indicators.sort(key=lambda x: x.volatility, reverse=reverse)
        elif sort_by == "market_cap":
            filtered_indicators.sort(key=lambda x: x.market_cap, reverse=reverse)
        elif sort_by == "name":
            filtered_indicators.sort(key=lambda x: x.name, reverse=reverse)
        
        # 결과 제한
        result = filtered_indicators[:limit]
        
        logger.info(f"퀀트 지표 조회 완료: {market} 시장 {len(result)}개 종목")
        return result
        
    except Exception as e:
        logger.error(f"퀀트 지표 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="퀀트 지표 조회에 실패했습니다.")


@router.get("/indicators/{symbol}", response_model=QuantIndicator)
async def get_stock_quant_indicator(
    symbol: str,
    market: str = Query("KR", description="시장 (KR/US)")
):
    """
    개별 종목 퀀트 지표 조회
    """
    try:
        # 전체 지표에서 해당 종목 찾기
        indicators = await quant_service.get_quant_indicators(market, 200)
        
        for indicator in indicators:
            if indicator.symbol == symbol:
                logger.info(f"종목 {symbol} 퀀트 지표 조회 완료")
                return indicator
        
        raise HTTPException(status_code=404, detail=f"종목 {symbol}을 찾을 수 없습니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"종목 {symbol} 퀀트 지표 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="종목 퀀트 지표 조회에 실패했습니다.")


@router.post("/backtest", response_model=BacktestResult)
async def run_strategy_backtest(
    strategy: str = Query(..., description="전략 ID (value/momentum/quality/lowvol/size)"),
    market: str = Query("KR", description="시장 (KR/US)"),
    period: str = Query("1y", description="백테스트 기간 (1y/2y/3y)")
):
    """
    팩터 전략 백테스트 실행
    
    선택한 팩터 전략에 따라 종목을 선별하고 과거 성과를 시뮬레이션합니다.
    """
    try:
        # 지원되는 전략 확인
        supported_strategies = ["value", "momentum", "quality", "lowvol", "size"]
        if strategy not in supported_strategies:
            raise HTTPException(
                status_code=400, 
                detail=f"지원되지 않는 전략입니다. 지원 전략: {', '.join(supported_strategies)}"
            )
        
        # 지원되는 기간 확인
        supported_periods = ["1y", "2y", "3y"]
        if period not in supported_periods:
            raise HTTPException(
                status_code=400,
                detail=f"지원되지 않는 기간입니다. 지원 기간: {', '.join(supported_periods)}"
            )
        
        # 백테스트 실행
        result = await quant_service.run_factor_strategy_backtest(strategy, market, period)
        
        logger.info(f"백테스트 완료: {strategy} 전략, {market} 시장, {period} 기간")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"백테스트 실행 실패: {e}")
        raise HTTPException(status_code=500, detail="백테스트 실행에 실패했습니다.")


@router.get("/strategies")
async def get_available_strategies():
    """
    사용 가능한 팩터 전략 목록 조회
    """
    try:
        strategies = [
            {
                "id": "value",
                "name": "가치 전략 (Value)",
                "description": "저평가된 우량 기업을 선별하여 투자",
                "factors": ["PER < 15", "PBR < 1.5", "ROE > 10%"],
                "risk_level": "중간",
                "expected_return": "중간",
                "suitable_for": "안정적 수익을 추구하는 투자자"
            },
            {
                "id": "momentum",
                "name": "모멘텀 전략 (Momentum)",
                "description": "상승 추세가 지속되는 종목에 투자",
                "factors": ["3개월 수익률 > 15%", "거래량 증가", "기술적 지표 양호"],
                "risk_level": "높음",
                "expected_return": "높음",
                "suitable_for": "적극적 투자를 선호하는 투자자"
            },
            {
                "id": "quality",
                "name": "품질 전략 (Quality)",
                "description": "재무 건전성이 우수한 기업에 투자",
                "factors": ["ROE > 15%", "부채비율 < 50%", "매출 성장 > 10%"],
                "risk_level": "낮음",
                "expected_return": "중간",
                "suitable_for": "안정성을 중시하는 장기 투자자"
            },
            {
                "id": "lowvol",
                "name": "저변동성 전략 (Low Volatility)",
                "description": "변동성이 낮은 안정적인 종목에 투자",
                "factors": ["변동성 < 20%", "베타 < 1.0", "배당수익률 > 3%"],
                "risk_level": "낮음",
                "expected_return": "낮음",
                "suitable_for": "보수적 투자를 선호하는 투자자"
            },
            {
                "id": "size",
                "name": "소형주 전략 (Size)",
                "description": "성장 잠재력이 큰 소형주에 투자",
                "factors": ["시가총액 < 1조원", "매출 성장 > 20%", "PEG < 1.0"],
                "risk_level": "높음",
                "expected_return": "높음",
                "suitable_for": "성장 투자를 추구하는 투자자"
            }
        ]
        
        logger.info("전략 목록 조회 완료")
        return {
            "strategies": strategies,
            "total_count": len(strategies)
        }
        
    except Exception as e:
        logger.error(f"전략 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="전략 목록 조회에 실패했습니다.")


@router.get("/market-summary")
async def get_market_quant_summary(
    market: str = Query("KR", description="시장 (KR/US)")
):
    """
    시장 퀀트 지표 요약 정보
    """
    try:
        # 퀀트 지표 데이터 가져오기
        indicators = await quant_service.get_quant_indicators(market, 100)
        
        if not indicators:
            raise HTTPException(status_code=404, detail="퀀트 지표 데이터를 찾을 수 없습니다.")
        
        # 요약 통계 계산
        per_values = [ind.per for ind in indicators if ind.per > 0]
        pbr_values = [ind.pbr for ind in indicators if ind.pbr > 0]
        roe_values = [ind.roe for ind in indicators]
        quant_scores = [ind.quant_score for ind in indicators]
        
        # 추천 분포
        recommendations = {}
        for ind in indicators:
            rec = ind.recommendation
            recommendations[rec] = recommendations.get(rec, 0) + 1
        
        summary = {
            "market": market,
            "total_stocks": len(indicators),
            "avg_per": round(sum(per_values) / len(per_values), 2) if per_values else 0,
            "avg_pbr": round(sum(pbr_values) / len(pbr_values), 2) if pbr_values else 0,
            "avg_roe": round(sum(roe_values) / len(roe_values), 2) if roe_values else 0,
            "avg_quant_score": round(sum(quant_scores) / len(quant_scores), 1) if quant_scores else 0,
            "recommendations": recommendations,
            "top_performers": [
                {
                    "symbol": ind.symbol,
                    "name": ind.name,
                    "quant_score": ind.quant_score,
                    "recommendation": ind.recommendation
                }
                for ind in sorted(indicators, key=lambda x: x.quant_score, reverse=True)[:5]
            ]
        }
        
        logger.info(f"{market} 시장 퀀트 요약 정보 조회 완료")
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"시장 요약 정보 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="시장 요약 정보 조회에 실패했습니다.")


@router.post("/recommendations", response_model=List[StockRecommendation])
async def get_stock_recommendations(
    profile: InvestmentProfile,
    market: str = Query("KR", description="시장 (KR/US)"),
    max_recommendations: int = Query(10, description="최대 추천 종목 수", ge=1, le=20)
):
    """
    개인화된 종목 추천
    
    투자자 프로필을 기반으로 맞춤형 종목을 추천합니다.
    """
    try:
        recommendations = await recommendation_service.get_personalized_recommendations(
            profile, market, max_recommendations
        )
        
        logger.info(f"종목 추천 완료: {len(recommendations)}개 종목")
        return recommendations
        
    except Exception as e:
        logger.error(f"종목 추천 실패: {e}")
        raise HTTPException(status_code=500, detail="종목 추천에 실패했습니다.")


@router.post("/portfolio-recommendations", response_model=List[PortfolioRecommendation])
async def get_portfolio_recommendations(
    profile: InvestmentProfile,
    market: str = Query("KR", description="시장 (KR/US)"),
    portfolio_size: int = Query(8, description="포트폴리오 종목 수", ge=5, le=15)
):
    """
    포트폴리오 추천
    
    투자자 프로필에 맞는 다양한 포트폴리오 구성을 추천합니다.
    """
    try:
        portfolios = await recommendation_service.get_portfolio_recommendations(
            profile, market, portfolio_size
        )
        
        logger.info(f"포트폴리오 추천 완료: {len(portfolios)}개 포트폴리오")
        return portfolios
        
    except Exception as e:
        logger.error(f"포트폴리오 추천 실패: {e}")
        raise HTTPException(status_code=500, detail="포트폴리오 추천에 실패했습니다.")


@router.get("/investment-profiles")
async def get_investment_profile_templates():
    """
    투자자 프로필 템플릿 조회
    """
    try:
        templates = [
            {
                "id": "conservative_income",
                "name": "안정 수익 추구형",
                "profile": {
                    "risk_tolerance": "conservative",
                    "investment_goal": "income",
                    "investment_period": "long",
                    "preferred_sectors": ["금융", "유틸리티", "소비재"],
                    "max_volatility": 20.0,
                    "min_dividend_yield": 3.0
                },
                "description": "안정적인 배당 수익을 추구하는 보수적 투자자",
                "suitable_for": "은퇴자, 안정성 중시 투자자"
            },
            {
                "id": "balanced_growth",
                "name": "균형 성장형",
                "profile": {
                    "risk_tolerance": "moderate",
                    "investment_goal": "balanced",
                    "investment_period": "medium",
                    "preferred_sectors": ["기술", "헬스케어", "소비재"],
                    "max_volatility": 25.0,
                    "min_dividend_yield": 1.0
                },
                "description": "성장과 안정성을 균형있게 추구하는 투자자",
                "suitable_for": "일반 투자자, 중간 위험 선호"
            },
            {
                "id": "aggressive_growth",
                "name": "적극 성장 추구형",
                "profile": {
                    "risk_tolerance": "aggressive",
                    "investment_goal": "growth",
                    "investment_period": "long",
                    "preferred_sectors": ["기술", "바이오", "신에너지"],
                    "max_volatility": 35.0,
                    "min_dividend_yield": 0.0
                },
                "description": "높은 성장을 추구하는 공격적 투자자",
                "suitable_for": "젊은 투자자, 고위험 고수익 선호"
            },
            {
                "id": "tech_focused",
                "name": "기술 특화형",
                "profile": {
                    "risk_tolerance": "moderate",
                    "investment_goal": "growth",
                    "investment_period": "medium",
                    "preferred_sectors": ["반도체", "인터넷", "소프트웨어"],
                    "max_volatility": 30.0,
                    "min_dividend_yield": 0.0
                },
                "description": "기술 섹터에 집중하는 투자자",
                "suitable_for": "기술 트렌드에 관심 많은 투자자"
            },
            {
                "id": "value_investor",
                "name": "가치 투자형",
                "profile": {
                    "risk_tolerance": "moderate",
                    "investment_goal": "balanced",
                    "investment_period": "long",
                    "preferred_sectors": ["금융", "에너지", "소재"],
                    "max_volatility": 22.0,
                    "min_dividend_yield": 2.0
                },
                "description": "저평가된 가치주를 선호하는 투자자",
                "suitable_for": "장기 투자자, 가치 투자 철학 보유"
            }
        ]
        
        logger.info("투자자 프로필 템플릿 조회 완료")
        return {
            "templates": templates,
            "total_count": len(templates)
        }
        
    except Exception as e:
        logger.error(f"프로필 템플릿 조회 실패: {e}")
        raise HTTPException(status_code=500, detail="프로필 템플릿 조회에 실패했습니다.")