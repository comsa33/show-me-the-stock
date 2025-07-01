"""
종목 추천 서비스
퀀트 분석 결과를 기반으로 개인화된 종목 추천 제공
"""

import logging
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.services.quant_service import quant_service, QuantIndicator

logger = logging.getLogger(__name__)


class InvestmentProfile(BaseModel):
    """투자자 프로필"""
    risk_tolerance: str  # conservative, moderate, aggressive
    investment_goal: str  # income, growth, balanced
    investment_period: str  # short, medium, long
    preferred_sectors: List[str] = []
    max_volatility: float = 30.0
    min_dividend_yield: float = 0.0


class StockRecommendation(BaseModel):
    """종목 추천 결과"""
    symbol: str
    name: str
    market: str
    recommendation_score: float
    recommendation_reason: str
    entry_price_range: Dict[str, float]
    target_price: float
    stop_loss: float
    expected_return: float
    risk_level: str
    investment_period: str
    key_factors: List[str]
    quant_data: Optional[QuantIndicator] = None


class PortfolioRecommendation(BaseModel):
    """포트폴리오 추천"""
    portfolio_name: str
    description: str
    expected_return: float
    risk_level: str
    recommended_allocation: Dict[str, float]  # symbol -> weight
    stocks: List[StockRecommendation]
    rebalance_frequency: str
    total_score: float


class RecommendationService:
    """종목 추천 서비스"""
    
    def __init__(self):
        self.sector_mapping = {
            # 한국 주요 종목 섹터 매핑
            "005930": "반도체",  # 삼성전자
            "000660": "반도체",  # SK하이닉스
            "035420": "인터넷",  # NAVER
            "051910": "화학",    # LG화학
            "005380": "자동차",  # 현대차
            "068270": "바이오",  # 셀트리온
            "006400": "배터리",  # 삼성SDI
            "035720": "인터넷",  # 카카오
            "207940": "바이오",  # 삼성바이오로직스
            "066570": "전자",    # LG전자
            
            # 미국 주요 종목 섹터 매핑
            "AAPL": "기술",      # Apple
            "MSFT": "기술",      # Microsoft
            "GOOGL": "기술",     # Alphabet
            "AMZN": "소매",      # Amazon
            "TSLA": "자동차",    # Tesla
            "META": "기술",      # Meta
            "NVDA": "반도체",    # NVIDIA
            "NFLX": "미디어",    # Netflix
            "ADBE": "기술",      # Adobe
            "CRM": "기술"        # Salesforce
        }
    
    async def get_personalized_recommendations(
        self, 
        profile: InvestmentProfile,
        market: str = "KR",
        max_recommendations: int = 10
    ) -> List[StockRecommendation]:
        """개인화된 종목 추천"""
        
        try:
            # 퀀트 지표 데이터 가져오기
            quant_indicators = await quant_service.get_quant_indicators(market, 100)
            
            # 투자자 프로필에 따른 필터링 및 점수 계산
            scored_stocks = []
            
            for indicator in quant_indicators:
                # 프로필 기반 필터링
                if not self._meets_profile_criteria(indicator, profile):
                    continue
                
                # 추천 점수 계산
                recommendation_score = self._calculate_recommendation_score(indicator, profile)
                
                # 추천 이유 생성
                reason = self._generate_recommendation_reason(indicator, profile)
                
                # 가격 목표 계산
                entry_range, target_price, stop_loss = self._calculate_price_targets(indicator)
                
                # 예상 수익률 계산
                expected_return = self._calculate_expected_return(indicator, profile)
                
                # 위험 수준 평가
                risk_level = self._assess_risk_level(indicator)
                
                # 투자 기간 추천
                investment_period = self._recommend_investment_period(indicator, profile)
                
                # 핵심 팩터 추출
                key_factors = self._extract_key_factors(indicator, profile)
                
                recommendation = StockRecommendation(
                    symbol=indicator.symbol,
                    name=indicator.name,
                    market=indicator.market,
                    recommendation_score=recommendation_score,
                    recommendation_reason=reason,
                    entry_price_range=entry_range,
                    target_price=target_price,
                    stop_loss=stop_loss,
                    expected_return=expected_return,
                    risk_level=risk_level,
                    investment_period=investment_period,
                    key_factors=key_factors,
                    quant_data=indicator
                )
                
                scored_stocks.append(recommendation)
            
            # 추천 점수 기준 정렬
            scored_stocks.sort(key=lambda x: x.recommendation_score, reverse=True)
            
            # 상위 N개 추천
            result = scored_stocks[:max_recommendations]
            
            logger.info(f"개인화 추천 완료: {len(result)}개 종목 ({market} 시장)")
            return result
            
        except Exception as e:
            logger.error(f"개인화 추천 실패: {e}")
            return []
    
    async def get_portfolio_recommendations(
        self,
        profile: InvestmentProfile,
        market: str = "KR",
        target_portfolio_size: int = 8
    ) -> List[PortfolioRecommendation]:
        """포트폴리오 추천"""
        
        try:
            # 개별 종목 추천 가져오기
            stock_recommendations = await self.get_personalized_recommendations(
                profile, market, target_portfolio_size * 2
            )
            
            if not stock_recommendations:
                return []
            
            # 리스크 수준별 포트폴리오 구성
            portfolios = []
            
            # 보수적 포트폴리오
            if profile.risk_tolerance in ["conservative", "moderate"]:
                conservative_portfolio = self._build_conservative_portfolio(
                    stock_recommendations, target_portfolio_size
                )
                portfolios.append(conservative_portfolio)
            
            # 균형 포트폴리오
            balanced_portfolio = self._build_balanced_portfolio(
                stock_recommendations, target_portfolio_size
            )
            portfolios.append(balanced_portfolio)
            
            # 성장 포트폴리오
            if profile.risk_tolerance in ["moderate", "aggressive"]:
                growth_portfolio = self._build_growth_portfolio(
                    stock_recommendations, target_portfolio_size
                )
                portfolios.append(growth_portfolio)
            
            logger.info(f"포트폴리오 추천 완료: {len(portfolios)}개 포트폴리오")
            return portfolios
            
        except Exception as e:
            logger.error(f"포트폴리오 추천 실패: {e}")
            return []
    
    def _meets_profile_criteria(self, indicator: QuantIndicator, profile: InvestmentProfile) -> bool:
        """투자자 프로필 조건 확인"""
        
        # 변동성 조건
        if indicator.volatility > profile.max_volatility:
            return False
        
        # 리스크 허용도에 따른 필터링
        if profile.risk_tolerance == "conservative":
            if indicator.debt_ratio > 50 or indicator.roe < 10:
                return False
        elif profile.risk_tolerance == "moderate":
            if indicator.debt_ratio > 70 or indicator.roe < 5:
                return False
        
        # 투자 목표에 따른 필터링
        if profile.investment_goal == "income":
            # 배당 수익을 위한 조건 (실제로는 배당수익률 데이터 필요)
            if indicator.roe < 10 or indicator.volatility > 25:
                return False
        elif profile.investment_goal == "growth":
            # 성장을 위한 조건
            if indicator.momentum_3m < -10:
                return False
        
        # 선호 섹터 확인 (선호 섹터가 있는 경우에만 적용)
        if profile.preferred_sectors and len(profile.preferred_sectors) > 0:
            sector = self.sector_mapping.get(indicator.symbol, "기타")
            # 기타 섹터는 허용하고, 선호 섹터 중 하나라도 매칭되면 통과
            if sector != "기타" and sector not in profile.preferred_sectors:
                return False
        
        return True
    
    def _calculate_recommendation_score(self, indicator: QuantIndicator, profile: InvestmentProfile) -> float:
        """추천 점수 계산"""
        
        base_score = indicator.quant_score
        
        # 프로필별 가중치 조정
        profile_bonus = 0
        
        # 리스크 허용도 보너스
        if profile.risk_tolerance == "conservative":
            if indicator.volatility < 20 and indicator.debt_ratio < 40:
                profile_bonus += 10
        elif profile.risk_tolerance == "aggressive":
            if indicator.momentum_3m > 10:
                profile_bonus += 10
        
        # 투자 목표 보너스
        if profile.investment_goal == "growth":
            if indicator.roe > 15 and indicator.momentum_3m > 5:
                profile_bonus += 8
        elif profile.investment_goal == "income":
            if indicator.roe > 12 and indicator.volatility < 25:
                profile_bonus += 8
        
        # 투자 기간 보너스
        if profile.investment_period == "long":
            if indicator.roe > 15 and indicator.debt_ratio < 50:
                profile_bonus += 5
        
        final_score = min(100, base_score + profile_bonus)
        return round(final_score, 1)
    
    def _generate_recommendation_reason(self, indicator: QuantIndicator, profile: InvestmentProfile) -> str:
        """추천 이유 생성"""
        
        reasons = []
        
        # 퀀트 점수 기반
        if indicator.quant_score > 70:
            reasons.append("우수한 퀀트 지표")
        
        # 밸류에이션
        if indicator.per < 15 and indicator.pbr < 2:
            reasons.append("매력적인 밸류에이션")
        
        # 수익성
        if indicator.roe > 15:
            reasons.append("높은 자기자본이익률")
        
        # 모멘텀
        if indicator.momentum_3m > 10:
            reasons.append("강한 상승 모멘텀")
        
        # 안정성
        if indicator.debt_ratio < 30:
            reasons.append("건전한 재무구조")
        
        # 프로필 매칭
        if profile.risk_tolerance == "conservative" and indicator.volatility < 20:
            reasons.append("낮은 변동성으로 안정적")
        
        if not reasons:
            reasons.append("종합적인 투자 매력도 양호")
        
        return ", ".join(reasons)
    
    def _calculate_price_targets(self, indicator: QuantIndicator) -> tuple:
        """가격 목표 계산"""
        
        # 현재가 추정 (실제로는 실시간 가격 데이터 필요)
        if indicator.market.upper() == "KR":
            current_price = 50000 + (indicator.quant_score * 1000)  # 임시 계산
        else:
            current_price = 100 + (indicator.quant_score * 5)  # 임시 계산
        
        # 진입 가격 범위 (현재가 ±5%)
        entry_range = {
            "min": round(current_price * 0.95, 2),
            "max": round(current_price * 1.05, 2)
        }
        
        # 목표가 (퀀트 점수 기반)
        target_multiplier = 1.1 + (indicator.quant_score / 100 * 0.3)  # 10-40% 상승
        target_price = round(current_price * target_multiplier, 2)
        
        # 손절가 (현재가 -10%)
        stop_loss = round(current_price * 0.9, 2)
        
        return entry_range, target_price, stop_loss
    
    def _calculate_expected_return(self, indicator: QuantIndicator, profile: InvestmentProfile) -> float:
        """예상 수익률 계산"""
        
        # 기본 수익률 (퀀트 점수 기반)
        base_return = (indicator.quant_score / 100) * 20  # 최대 20%
        
        # 모멘텀 보정
        momentum_adjust = indicator.momentum_3m * 0.3
        
        # 프로필별 조정
        if profile.investment_goal == "growth":
            base_return *= 1.2
        elif profile.investment_goal == "income":
            base_return *= 0.8
        
        # 위험 조정
        risk_adjust = (50 - indicator.volatility) / 50 * 0.1
        
        expected_return = base_return + momentum_adjust + risk_adjust
        return round(max(-20, min(50, expected_return)), 1)
    
    def _assess_risk_level(self, indicator: QuantIndicator) -> str:
        """위험 수준 평가"""
        
        risk_score = 0
        
        # 변동성
        if indicator.volatility > 30:
            risk_score += 3
        elif indicator.volatility > 20:
            risk_score += 2
        else:
            risk_score += 1
        
        # 부채비율
        if indicator.debt_ratio > 70:
            risk_score += 3
        elif indicator.debt_ratio > 50:
            risk_score += 2
        else:
            risk_score += 1
        
        # 밸류에이션
        if indicator.per > 30 or indicator.pbr > 4:
            risk_score += 2
        
        if risk_score <= 3:
            return "낮음"
        elif risk_score <= 6:
            return "보통"
        else:
            return "높음"
    
    def _recommend_investment_period(self, indicator: QuantIndicator, profile: InvestmentProfile) -> str:
        """투자 기간 추천"""
        
        if profile.investment_period == "short":
            return "단기 (1-3개월)"
        elif profile.investment_period == "medium":
            return "중기 (3-12개월)"
        else:
            # 품질 지표가 좋으면 장기 투자 추천
            if indicator.roe > 15 and indicator.debt_ratio < 40:
                return "장기 (1년 이상)"
            else:
                return "중기 (3-12개월)"
    
    def _extract_key_factors(self, indicator: QuantIndicator, profile: InvestmentProfile) -> List[str]:
        """핵심 팩터 추출"""
        
        factors = []
        
        # 밸류 팩터
        if indicator.per < 15:
            factors.append("저PER")
        if indicator.pbr < 1.5:
            factors.append("저PBR")
        
        # 품질 팩터
        if indicator.roe > 15:
            factors.append("고ROE")
        if indicator.debt_ratio < 30:
            factors.append("저부채")
        
        # 모멘텀 팩터
        if indicator.momentum_3m > 10:
            factors.append("상승모멘텀")
        
        # 저변동성 팩터
        if indicator.volatility < 20:
            factors.append("저변동성")
        
        # 퀀트 점수
        if indicator.quant_score > 70:
            factors.append("우수한퀀트점수")
        
        return factors[:4]  # 최대 4개 팩터
    
    def _build_conservative_portfolio(
        self, 
        recommendations: List[StockRecommendation], 
        size: int
    ) -> PortfolioRecommendation:
        """보수적 포트폴리오 구성"""
        
        # 저위험 종목 선별
        conservative_stocks = [
            stock for stock in recommendations 
            if stock.risk_level in ["낮음", "보통"] and stock.quant_data.volatility < 25
        ]
        
        selected = conservative_stocks[:size]
        
        # 균등 가중치
        equal_weight = 1.0 / len(selected) if selected else 0
        allocation = {stock.symbol: equal_weight for stock in selected}
        
        avg_return = sum(stock.expected_return for stock in selected) / len(selected) if selected else 0
        
        return PortfolioRecommendation(
            portfolio_name="안정 추구형 포트폴리오",
            description="변동성이 낮고 안정적인 종목들로 구성된 보수적 포트폴리오",
            expected_return=round(avg_return * 0.8, 1),  # 보수적 조정
            risk_level="낮음",
            recommended_allocation=allocation,
            stocks=selected,
            rebalance_frequency="분기별",
            total_score=sum(stock.recommendation_score for stock in selected) / len(selected) if selected else 0
        )
    
    def _build_balanced_portfolio(
        self, 
        recommendations: List[StockRecommendation], 
        size: int
    ) -> PortfolioRecommendation:
        """균형 포트폴리오 구성"""
        
        # 다양한 위험 수준의 종목 선별
        selected = recommendations[:size]
        
        # 리스크 기반 가중치 (낮은 리스크에 더 많은 비중)
        total_score = sum(stock.recommendation_score for stock in selected)
        allocation = {}
        
        for stock in selected:
            weight = stock.recommendation_score / total_score if total_score > 0 else 1.0 / len(selected)
            allocation[stock.symbol] = round(weight, 3)
        
        avg_return = sum(stock.expected_return for stock in selected) / len(selected) if selected else 0
        
        return PortfolioRecommendation(
            portfolio_name="균형 성장형 포트폴리오",
            description="성장성과 안정성을 균형있게 고려한 포트폴리오",
            expected_return=round(avg_return, 1),
            risk_level="보통",
            recommended_allocation=allocation,
            stocks=selected,
            rebalance_frequency="반기별",
            total_score=total_score / len(selected) if selected else 0
        )
    
    def _build_growth_portfolio(
        self, 
        recommendations: List[StockRecommendation], 
        size: int
    ) -> PortfolioRecommendation:
        """성장 포트폴리오 구성"""
        
        # 고성장 종목 선별
        growth_stocks = [
            stock for stock in recommendations 
            if stock.expected_return > 10 and stock.quant_data.roe > 12
        ]
        
        selected = growth_stocks[:size]
        
        # 성장성 기반 가중치
        total_return = sum(stock.expected_return for stock in selected)
        allocation = {}
        
        for stock in selected:
            weight = stock.expected_return / total_return if total_return > 0 else 1.0 / len(selected)
            allocation[stock.symbol] = round(weight, 3)
        
        avg_return = sum(stock.expected_return for stock in selected) / len(selected) if selected else 0
        
        return PortfolioRecommendation(
            portfolio_name="적극 성장형 포트폴리오",
            description="높은 성장 잠재력을 가진 종목들로 구성된 공격적 포트폴리오",
            expected_return=round(avg_return * 1.2, 1),  # 성장 프리미엄
            risk_level="높음",
            recommended_allocation=allocation,
            stocks=selected,
            rebalance_frequency="월별",
            total_score=sum(stock.recommendation_score for stock in selected) / len(selected) if selected else 0
        )


# 전역 서비스 인스턴스
recommendation_service = RecommendationService()