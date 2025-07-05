import os
from typing import List, Dict, Any
from datetime import datetime
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
import json
import logging
from app.core.config import get_settings
from app.services.quant_service_factory import QuantServiceFactory
from app.core.redis_client import RedisClient
from app.core.cache import cached
import enum

# 로거 설정
logger = logging.getLogger(__name__)

# 설정 가져오기
settings = get_settings()

# Gemini 클라이언트 생성
client = genai.Client(api_key=settings.gemini_api_key)

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class TimeHorizon(str, enum.Enum):
    SHORT = "SHORT"  # 1-3개월
    MEDIUM = "MEDIUM"  # 3-6개월
    LONG = "LONG"  # 6개월 이상

class KeyIndicator(BaseModel):
    name: str = Field(description="지표명 (예: PER, PBR, ROE)")
    value: float = Field(description="지표값")

class StockRecommendation(BaseModel):
    symbol: str = Field(description="종목 코드")
    name: str = Field(description="종목명")
    current_price: float = Field(description="현재가")
    predicted_price: float = Field(description="예상 목표가")
    predicted_return: float = Field(description="예상 수익률 (%)")
    confidence: float = Field(description="추천 신뢰도 (0-100)")
    risk_level: RiskLevel = Field(description="투자 위험도")
    time_horizon: TimeHorizon = Field(description="투자 기간")
    key_indicators: List[KeyIndicator] = Field(description="핵심 지표들 (PER, PBR, ROE 등)")
    reasoning: List[str] = Field(description="추천 이유 3-5개")
    warnings: List[str] = Field(description="주의사항 및 리스크 요인", default_factory=list)

class AIRecommendationService:
    def __init__(self):
        self.client = client
        self.quant_service = QuantServiceFactory.get_service()
        self.redis_client = RedisClient.get_instance()

    @cached(ttl=3600, key_prefix="ai_recommendations")  # 1시간 캐시
    async def get_ai_recommendations(self, market: str = 'KR', top_n: int = 6) -> List[Dict[str, Any]]:
        """
        퀀트 지표 상위 종목을 AI가 분석하여 추천
        """
        try:
            # 1. 퀀트 지표 데이터 가져오기
            # MongoDB service uses get_quant_indicators, External API uses get_limited_quant_indicators
            if hasattr(self.quant_service, 'get_quant_indicators'):
                # MongoDB service
                quant_indicators = await self.quant_service.get_quant_indicators(market=market)
            else:
                # External API service
                quant_indicators = await self.quant_service.get_limited_quant_indicators(market=market)
            
            # 2. 퀀트 점수 기준 상위 종목 선택
            # 객체를 딕셔너리로 변환
            indicators_dict = [indicator.model_dump() for indicator in quant_indicators]
            # MongoDB service uses 'quant_score', External API uses 'limited_quant_score'
            score_key = 'quant_score' if 'quant_score' in indicators_dict[0] else 'limited_quant_score'
            sorted_stocks = sorted(
                indicators_dict, 
                key=lambda x: x[score_key], 
                reverse=True
            )[:top_n]
            
            if not sorted_stocks:
                logger.warning(f"No stocks found for market {market}")
                return []
            
            # 3. AI 분석을 위한 프롬프트 생성
            prompt = self._create_analysis_prompt(sorted_stocks, market)
            
            # 4. Gemini API 호출
            response = self.client.models.generate_content(
                model="gemini-2.5-flash-lite-preview-06-17",
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=64000,
                    response_mime_type="application/json",
                    response_schema=list[StockRecommendation],
                    thinking_config=types.ThinkingConfig(
                        thinking_budget=0
                    )
                ),
            )
            
            # 5. 응답 파싱
            recommendations = response.parsed
            
            # 6. 결과 변환
            result = []
            for rec in recommendations:
                # key_indicators를 딕셔너리로 변환
                key_indicators_dict = {
                    indicator.name: indicator.value 
                    for indicator in rec.key_indicators
                }
                
                result.append({
                    "symbol": rec.symbol,
                    "name": rec.name,
                    "currentPrice": rec.current_price,
                    "predictedPrice": rec.predicted_price,
                    "predictedReturn": rec.predicted_return,
                    "confidence": rec.confidence,
                    "riskLevel": rec.risk_level.value,
                    "timeHorizon": rec.time_horizon.value,
                    "keyIndicators": key_indicators_dict,
                    "reasoning": rec.reasoning,
                    "warnings": rec.warnings
                })
            
            return result
            
        except Exception as e:
            logger.error(f"AI recommendation error: {str(e)}")
            # 에러 시 빈 배열 반환
            return []
    
    def _create_analysis_prompt(self, stocks: List[Dict], market: str) -> str:
        """AI 분석을 위한 프롬프트 생성"""
        
        market_name = "한국" if market == 'KR' else "미국"
        
        stock_info = "\n".join([
            f"""
종목: {stock['name']} ({stock['symbol']})
- 퀀트 점수: {stock.get('quant_score', stock.get('limited_quant_score', 0))}/100
- PER: {stock.get('per', 'N/A')}
- PBR: {stock.get('pbr', 'N/A')}
- ROE: {stock.get('roe', stock.get('estimated_roe', 'N/A'))}%
- EPS: {stock.get('eps', 'N/A')}
- 현재가: {stock.get('current_price', 0):,}
- 시가총액: {stock.get('market_cap', 0):,}백만원
- 3개월 모멘텀: {stock.get('momentum_3m', 'N/A')}%
- 변동성: {stock.get('volatility', 'N/A')}%
- 추천 상태: {stock.get('recommendation', 'N/A')}
- 데이터 완전성: {stock.get('data_completeness', 'N/A')}
"""
            for stock in stocks
        ])
        
        prompt = f"""
당신은 {market_name} 주식시장의 전문 퀀트 애널리스트입니다. 
다음은 퀀트 지표 기준 상위 {len(stocks)}개 종목의 데이터입니다:

{stock_info}

각 종목에 대해 다음 사항을 분석하여 투자 추천을 제공해주세요:

1. 현재가 대비 3-6개월 후 예상 목표가와 수익률
2. 추천 신뢰도 (0-100점)
3. 투자 위험도 (LOW/MEDIUM/HIGH)
4. 투자 기간 (SHORT: 1-3개월, MEDIUM: 3-6개월, LONG: 6개월 이상)
5. 핵심 투자 지표들 (PER, PBR, ROE 등)
6. 추천 이유 3-5개 (구체적이고 데이터 기반)
7. 주의사항 및 리스크 요인

분석 시 다음 사항을 고려하세요:
- 퀀트 점수가 높은 이유
- PER, PBR이 업종 평균 대비 어떤지
- ROE가 지속 가능한 수준인지
- 모멘텀과 변동성의 관계
- 시가총액 규모에 따른 리스크
- 데이터 완전성이 제한적인 경우 보수적으로 평가

각 종목별로 투자자가 이해하기 쉽게 설명해주세요.
ALWAYS ANSWER IN KOREAN.
"""
        
        return prompt
    
    def _get_fallback_recommendations(self, stocks: List[Dict]) -> List[Dict[str, Any]]:
        """AI 호출 실패 시 기본 추천 생성"""
        recommendations = []
        
        for stock in stocks:
            # 간단한 규칙 기반 추천
            quant_score = stock.get('quant_score', stock.get('limited_quant_score', 0))
            momentum = stock.get('momentum_3m', 0)
            volatility = stock.get('volatility', 20)
            
            # 예상 수익률 계산 (간단한 규칙)
            predicted_return = (quant_score / 100 * 20) + (momentum * 0.3)
            predicted_return = max(-30, min(50, predicted_return))  # -30% ~ +50% 제한
            
            # 위험도 평가
            if volatility < 15 and quant_score > 70:
                risk_level = "LOW"
            elif volatility > 30 or quant_score < 40:
                risk_level = "HIGH"
            else:
                risk_level = "MEDIUM"
            
            # 신뢰도 계산
            confidence = min(95, quant_score * 0.8 + (100 - volatility) * 0.2)
            
            recommendations.append({
                "symbol": stock['symbol'],
                "name": stock['name'],
                "currentPrice": stock['current_price'],
                "predictedPrice": stock['current_price'] * (1 + predicted_return / 100),
                "predictedReturn": round(predicted_return, 2),
                "confidence": round(confidence, 0),
                "riskLevel": risk_level,
                "timeHorizon": "MEDIUM",
                "keyIndicators": {
                    "PER": stock.get('per', 0),
                    "PBR": stock.get('pbr', 0),
                    "ROE": stock.get('roe', stock.get('estimated_roe', 0)),
                    "quantScore": stock.get('quant_score', stock.get('limited_quant_score', 0))
                },
                "reasoning": [
                    f"퀀트 점수 {stock.get('quant_score', stock.get('limited_quant_score', 0))}점으로 상위권",
                    f"PER {stock.get('per', 0)}배로 {'저평가' if stock.get('per', 15) < 15 else '적정가'}",
                    f"ROE {stock.get('roe', stock.get('estimated_roe', 0))}%로 {'우수한' if stock.get('roe', stock.get('estimated_roe', 0)) > 15 else '양호한'} 수익성",
                    f"3개월 모멘텀 {momentum}%로 {'상승' if momentum > 0 else '하락'} 추세"
                ],
                "warnings": [
                    f"변동성 {volatility}%로 {'안정적' if volatility < 20 else '변동성 높음'}",
                    "AI 분석 불가로 규칙 기반 추천"
                ] if volatility > 20 else ["AI 분석 불가로 규칙 기반 추천"]
            })
        
        return recommendations

# 서비스 인스턴스 생성
ai_recommendation_service = AIRecommendationService()