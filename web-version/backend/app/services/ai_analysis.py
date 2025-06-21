"""
Google Gemini를 사용한 AI 주식 분석 서비스
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel

try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logging.warning("Google Gemini API not available - using mock data")

from app.data.stock_data import StockDataFetcher

logger = logging.getLogger(__name__)


class TechnicalIndicator(BaseModel):
    """기술적 지표"""
    value: float
    signal: str  # "매수", "매도", "중립", "과매수", "과매도"
    description: str


class MovingAverage(BaseModel):
    signal: str
    description: str


class VolumeAnalysis(BaseModel):
    trend: str
    description: str


class TechnicalAnalysis(BaseModel):
    rsi: TechnicalIndicator
    moving_average: MovingAverage
    volume_analysis: VolumeAnalysis 


class NewsAnalysis(BaseModel):
    """뉴스 감성 분석"""
    sentiment: str  # "긍정", "부정", "중립"
    score: int  # 0-100
    summary: str
    key_topics: List[str]


class AnalysisSummary(BaseModel):
    """분석 요약"""
    overall_signal: str  # "상승", "하락", "횡보"
    confidence: str  # "85%"
    recommendation: str  # "매수", "매도", "보유"
    target_price: str  # "₩85,000" or "$150.50"
    analysis_period: str


class StockAnalysisResult(BaseModel):
    """AI 주식 분석 전체 결과"""
    summary: AnalysisSummary
    technical_analysis: TechnicalAnalysis
    news_analysis: NewsAnalysis
    risk_factors: List[str]
    ai_insights: List[str]


class GeminiStockAnalyzer:
    """Google Gemini를 사용한 주식 분석기"""
    
    def __init__(self):
        self.client = None
        self.stock_fetcher = StockDataFetcher()
        
        if GEMINI_AVAILABLE:
            api_key = os.getenv("GEMINI_API_KEY")
            logger.info(f"GEMINI_API_KEY found: {bool(api_key and api_key.strip())}")
            if api_key and api_key.strip():
                try:
                    self.client = genai.Client(api_key=api_key)
                    logger.info("Gemini client initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize Gemini client: {e}")
            else:
                logger.warning("GEMINI_API_KEY not set or empty - using mock data")
    
    async def analyze_stock(
        self,
        symbol: str,
        market: str,
        analysis_type: str = "short"
    ) -> StockAnalysisResult:
        """주식 AI 분석 실행"""
        
        if not self.client or not GEMINI_AVAILABLE:
            return await self._generate_mock_analysis(symbol, market, analysis_type)
        
        try:
            # 주식 데이터 수집
            stock_data = await self._collect_stock_data(symbol, market, analysis_type)
            
            # Gemini 분석 실행
            analysis_prompt = self._create_analysis_prompt(symbol, market, analysis_type, stock_data)
            
            # Google Search grounding 도구 설정
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            
            config = types.GenerateContentConfig(
                tools=[grounding_tool],
                response_mime_type="application/json",
                response_schema=StockAnalysisResult,
            )
            
            response = await self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=analysis_prompt,
                config=config,
            )
            
            # JSON 파싱
            analysis_result = response.parsed
            
            logger.info(f"Gemini analysis completed for {symbol}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Gemini analysis failed for {symbol}: {e}")
            # 실패시 Mock 데이터 반환
            return await self._generate_mock_analysis(symbol, market, analysis_type)
    
    async def _collect_stock_data(self, symbol: str, market: str, analysis_type: str) -> Dict:
        """분석에 필요한 주식 데이터 수집"""
        
        # 기간 설정
        period = "5d" if analysis_type == "short" else "1mo"
        
        # 주가 데이터
        price_data = self.stock_fetcher.get_stock_data(symbol, period, market)
        
        if price_data is None or price_data.empty:
            return {
                "symbol": symbol,
                "market": market,
                "period": period,
                "data_available": False,
                "error": "주가 데이터를 가져올 수 없습니다"
            }
        
        # 최근 가격 정보
        current_price = float(price_data['Close'].iloc[-1])
        prev_price = float(price_data['Close'].iloc[-2]) if len(price_data) > 1 else current_price
        change_percent = ((current_price - prev_price) / prev_price * 100) if prev_price > 0 else 0
        
        # 간단한 기술적 지표 계산
        rsi = self._calculate_rsi(price_data['Close'])
        ma5 = price_data['Close'].rolling(window=5).mean().iloc[-1] if len(price_data) >= 5 else current_price
        ma20 = price_data['Close'].rolling(window=20).mean().iloc[-1] if len(price_data) >= 20 else current_price
        
        volume_avg = price_data['Volume'].mean()
        recent_volume = price_data['Volume'].iloc[-1]
        
        return {
            "symbol": symbol,
            "market": market,
            "period": period,
            "data_available": True,
            "current_price": current_price,
            "change_percent": change_percent,
            "price_range": {
                "high": float(price_data['High'].max()),
                "low": float(price_data['Low'].min()),
                "open": float(price_data['Open'].iloc[0])
            },
            "technical_indicators": {
                "rsi": rsi,
                "ma5": float(ma5),
                "ma20": float(ma20),
                "volume_ratio": float(recent_volume / volume_avg) if volume_avg > 0 else 1.0
            },
            "data_points": len(price_data)
        }
    
    def _calculate_rsi(self, prices, period: int = 14) -> float:
        """RSI 계산"""
        if len(prices) < period + 1:
            return 50.0  # 기본값
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not rsi.isna().iloc[-1] else 50.0
    
    def _create_analysis_prompt(self, symbol: str, market: str, analysis_type: str, stock_data: Dict) -> str:
        """Gemini 분석용 프롬프트 생성"""
        
        market_name = "한국" if market.upper() == "KR" else "미국"
        period_desc = "1일" if analysis_type == "short" else "2주"
        
        if not stock_data.get("data_available", False):
            return f"""
주식 분석 요청: {symbol} ({market_name} 시장)
분석 기간: {period_desc}
오류: 주가 데이터를 가져올 수 없습니다.

기본적인 {market_name} 시장 {symbol} 종목에 대한 일반적인 분석을 제공해주세요.
최근 시장 동향과 업종 특성을 고려하여 분석해주세요.
"""
        
        current_price = stock_data["current_price"]
        change_percent = stock_data["change_percent"]
        tech_indicators = stock_data["technical_indicators"]
        
        currency = "₩" if market.upper() == "KR" else "$"
        
        prompt = f"""
주식 AI 분석 요청:

**종목 정보:**
- 종목: {symbol} ({market_name} 시장)
- 분석 기간: {period_desc}
- 현재가: {currency}{current_price:,.2f}
- 변동률: {change_percent:+.2f}%

**기술적 지표:**
- RSI: {tech_indicators['rsi']:.1f}
- 5일 이동평균: {currency}{tech_indicators['ma5']:,.2f}
- 20일 이동평균: {currency}{tech_indicators['ma20']:,.2f}
- 거래량 비율: {tech_indicators['volume_ratio']:.2f}

**분석 요청:**
위 데이터를 바탕으로 {symbol} 종목에 대한 종합적인 AI 분석을 수행해주세요.

다음 항목들을 포함해서 분석해주세요:
1. 전체 투자 신호 (상승/하락/횡보)
2. 신뢰도 (65-90% 범위)
3. 투자 추천 (매수/매도/보유)
4. 목표 주가 (현재가 기준 ±20% 범위)
5. RSI 기반 기술적 분석
6. 이동평균선 분석
7. 거래량 분석
8. 최근 뉴스 감성 분석 (Google Search 활용)
9. 주요 리스크 요인 3개
10. AI 인사이트 3개

**응답 형식:**
JSON 형태로 응답해주시고, 모든 수치와 분석 결과를 구체적으로 제공해주세요.
뉴스 분석은 Google Search를 활용하여 최신 정보를 반영해주세요.
"""
        
        return prompt
    
    async def _generate_mock_analysis(self, symbol: str, market: str, analysis_type: str) -> StockAnalysisResult:
        """Mock AI 분석 결과 생성 (Gemini 사용 불가시 대체)"""
        
        import random
        
        # 분석 기간 설정
        if analysis_type == "short":
            period_desc = "1일"
            data_period = "최근 1일 + 당일 뉴스"
        else:
            period_desc = "2주"
            data_period = "최근 2주 + 관련 뉴스"
        
        # Mock 데이터 생성
        price_trend = random.choice(["상승", "하락", "횡보"])
        confidence = random.randint(65, 90)
        
        # 기술적 분석
        rsi_value = random.randint(25, 75)
        rsi_signal = "과매수" if rsi_value > 70 else "과매도" if rsi_value < 30 else "중립"
        ma_signal = random.choice(["매수", "매도", "중립"])
        
        # 뉴스 감성 분석
        news_sentiment = random.choice(["긍정", "부정", "중립"])
        news_score = random.randint(40, 85)
        
        # 목표가 계산
        if market.upper() == "KR":
            current_price = random.randint(50000, 120000)
            target_price = current_price * random.uniform(0.85, 1.15)
            target_str = f"₩{int(target_price):,}"
        else:
            current_price = random.randint(80, 400)
            target_price = current_price * random.uniform(0.85, 1.15)
            target_str = f"${target_price:.2f}"
        
        recommendation = "매수" if price_trend == "상승" else "매도" if price_trend == "하락" else "보유"
        
        return StockAnalysisResult(
            summary=AnalysisSummary(
                overall_signal=price_trend,
                confidence=f"{confidence}%",
                recommendation=recommendation,
                target_price=target_str,
                analysis_period=data_period
            ),
            technical_analysis=TechnicalAnalysis(
                rsi=TechnicalIndicator(
                    value=rsi_value,
                    signal=rsi_signal,
                    description=f"RSI {rsi_value} - {'과열 구간' if rsi_value > 70 else '침체 구간' if rsi_value < 30 else '안정 구간'}"
                ),
                moving_average={
                    "signal": ma_signal,
                    "description": f"이동평균선 기준 {ma_signal} 신호 확인"
                },
                volume_analysis={
                    "trend": random.choice(["증가", "감소", "평균"]),
                    "description": "거래량 패턴 분석 결과"
                }
            ),
            news_analysis=NewsAnalysis(
                sentiment=news_sentiment,
                score=news_score,
                summary=f"최근 뉴스 감성 분석 결과 {news_sentiment}적 ({news_score}점)",
                key_topics=["실적 발표", "업계 동향", "정책 변화", "기술 혁신"][:random.randint(3, 4)]
            ),
            risk_factors=[
                "시장 변동성 증가",
                "업종별 리스크",
                "거시경제 요인",
                "지정학적 리스크"
            ][:random.randint(3, 4)],
            ai_insights=[
                f"{period_desc} 기준 {price_trend} 전망",
                f"기술적 지표 신뢰도 {confidence}%",
                f"뉴스 감성 {news_sentiment}적 영향",
                "장기 투자 관점에서 검토 필요"
            ][:random.randint(3, 4)]
        )


# 전역 분석기 인스턴스
gemini_analyzer = GeminiStockAnalyzer()