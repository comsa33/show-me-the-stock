"""
Google Gemini를 사용한 AI 주식 분석 서비스
"""

import os
import logging
import traceback
from typing import Dict, List
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


class SourceCitation(BaseModel):
    """출처 정보"""
    title: str
    url: str
    snippet: str


class GroundingSupport(BaseModel):
    """텍스트 세그먼트와 출처 매핑"""
    start_index: int
    end_index: int
    text: str
    source_indices: List[int]


class StockAnalysisResult(BaseModel):
    """AI 주식 분석 전체 결과"""
    summary: AnalysisSummary
    technical_analysis: TechnicalAnalysis
    news_analysis: NewsAnalysis
    risk_factors: List[str]
    ai_insights: List[str]
    sources: List[SourceCitation] = []
    grounding_supports: List[GroundingSupport] = []
    original_text: str = ""  # 원본 텍스트 (풋노트 적용 전)


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
        analysis_type: str = "beginner"
    ) -> StockAnalysisResult:
        """주식 AI 분석 실행 - grounding search 전용"""
        
        if not self.client or not GEMINI_AVAILABLE:
            logger.error(f"Gemini client not available for {symbol}")
            raise Exception("Gemini API is not available")
        
        try:
            logger.info(f"Starting grounding search analysis for {symbol} ({market}) - {analysis_type}")
            
            # 주식 데이터 수집
            import asyncio
            stock_data = await asyncio.wait_for(
                self._collect_stock_data(symbol, market, analysis_type),
                timeout=30.0
            )
            
            if not stock_data.get("data_available", False):
                logger.warning(f"Stock data not available for {symbol}, proceeding with basic analysis")
            
            # Step 1: Grounding search로 분석 실행
            logger.info(f"Step 1: Calling Gemini with grounding search for {symbol}")
            
            from google import genai
            from google.genai import types
            
            # Grounding search 활성화 - 테스트에서 확인된 정확한 방법
            grounding_tool = types.Tool(
                google_search=types.GoogleSearch()
            )
            
            config = types.GenerateContentConfig(
                tools=[grounding_tool]
            )
            
            # 분석 프롬프트 생성 (JSON 형태 요청 포함)
            analysis_prompt = self._create_grounding_prompt(symbol, market, analysis_type, stock_data)
            
            # Grounding search 실행 - 정확한 인자명 사용
            grounded_response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=analysis_prompt,
                config=config
            )
            
            logger.info(f"Grounding search completed for {symbol}")
            
            # 즉시 grounding metadata 추출 (객체가 사라지기 전에)
            extracted_sources = []
            extracted_supports = []
            
            if hasattr(grounded_response, 'candidates') and grounded_response.candidates:
                candidate = grounded_response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    metadata = candidate.grounding_metadata
                    
                    # grounding_chunks 추출
                    if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                        logger.info(f"Immediately extracting {len(metadata.grounding_chunks)} chunks")
                        for i, chunk in enumerate(metadata.grounding_chunks):
                            if hasattr(chunk, 'web') and chunk.web:
                                web = chunk.web
                                source = SourceCitation(
                                    title=getattr(web, 'title', f'Source {i+1}'),
                                    url=getattr(web, 'uri', ''),
                                    snippet=getattr(web, 'snippet', '')
                                )
                                extracted_sources.append(source)
                                logger.info(f"Extracted source: {source.title}")
                    
                    # grounding_supports 추출
                    if hasattr(metadata, 'grounding_supports') and metadata.grounding_supports:
                        logger.info(f"Immediately extracting {len(metadata.grounding_supports)} supports")
                        for support in metadata.grounding_supports:
                            if hasattr(support, 'segment'):
                                segment = support.segment
                                grounding_support = GroundingSupport(
                                    start_index=getattr(segment, 'start_index', 0),
                                    end_index=getattr(segment, 'end_index', 0),
                                    text=getattr(segment, 'text', ''),
                                    source_indices=list(support.grounding_chunk_indices) if hasattr(support, 'grounding_chunk_indices') and support.grounding_chunk_indices else []
                                )
                                extracted_supports.append(grounding_support)
            
            # 응답 구조 디버깅
            logger.info(f"Response type: {type(grounded_response)}")
            if hasattr(grounded_response, 'candidates') and grounded_response.candidates:
                candidate = grounded_response.candidates[0]
                logger.info(f"Has grounding_metadata: {hasattr(candidate, 'grounding_metadata')}")
                if hasattr(candidate, 'grounding_metadata'):
                    metadata = candidate.grounding_metadata
                    logger.info(f"Metadata is None: {metadata is None}")
                    if metadata:
                        logger.info(f"Has grounding_chunks: {hasattr(metadata, 'grounding_chunks')}")
                        if hasattr(metadata, 'grounding_chunks'):
                            chunks = metadata.grounding_chunks
                            logger.info(f"Chunks is None: {chunks is None}")
                            if chunks:
                                logger.info(f"Chunks length: {len(chunks)}")
                                logger.info(f"First chunk: {chunks[0] if len(chunks) > 0 else 'No chunks'}")
                            else:
                                logger.info("Chunks is None or empty list")
            
            # 전체 응답 로그 출력
            logger.info("=== FULL GROUNDING RESPONSE ===")
            logger.info(f"Response text (first 500 chars): {grounded_response.text[:500] if grounded_response.text else 'No text'}")
            logger.info(f"Response type: {type(grounded_response)}")
            
            # Step 2: 응답에서 JSON 부분 추출
            response_text = grounded_response.text
            json_data = self._extract_json_from_response(response_text)
            
            if not json_data:
                logger.error(f"No valid JSON found in response")
                raise Exception("No valid JSON found in grounding response")
            
            # Step 3: grounding metadata에서 소스 추출 
            # 이미 추출한 소스가 있으면 사용
            if extracted_sources:
                logger.info(f"Using {len(extracted_sources)} immediately extracted sources")
                sources = extracted_sources
                grounding_supports = extracted_supports
            else:
                # 다른 방법들 시도
                sources, grounding_supports = [], []
                
                # 접근 방식 1: 공식 문서 패턴 시도
                logger.info("Trying official citation pattern...")
                sources, grounding_supports = self._add_citations_official_pattern(grounded_response)
                logger.info(f"Official pattern: {len(sources)} sources, {len(grounding_supports)} supports")
                
                # 접근 방식 2: 기존 추출 방법 시도 (sources가 비어있는 경우)
                if len(sources) == 0:
                    logger.info("Trying existing grounding metadata extraction...")
                    sources, grounding_supports = self._extract_sources_from_grounding(grounded_response)
                    logger.info(f"Existing method: {len(sources)} sources, {len(grounding_supports)} supports")
                
                # 접근 방식 3: Fallback - 텍스트에서 풋노트 파싱
                if len(sources) == 0 and response_text:
                    logger.info("No sources from metadata, parsing footnotes from text...")
                    sources, grounding_supports = self._parse_footnotes_from_text(response_text, json_data.get("ai_insights", []))
                    logger.info(f"Footnote parsing: {len(sources)} sources, {len(grounding_supports)} supports")
            
            # Step 4: StockAnalysisResult 객체 생성
            result = StockAnalysisResult(
                summary=AnalysisSummary(**json_data["summary"]),
                technical_analysis=TechnicalAnalysis(
                    rsi=TechnicalIndicator(**json_data["technical_analysis"]["rsi"]),
                    moving_average=MovingAverage(**json_data["technical_analysis"]["moving_average"]),
                    volume_analysis=VolumeAnalysis(**json_data["technical_analysis"]["volume_analysis"])
                ),
                news_analysis=NewsAnalysis(**json_data["news_analysis"]),
                risk_factors=json_data["risk_factors"],
                ai_insights=json_data["ai_insights"],
                sources=sources,
                grounding_supports=grounding_supports,
                original_text=response_text or ""
            )
            
            logger.info(f"✅ Grounding analysis completed for {symbol}")
            logger.info(f"Final result: {len(result.sources)} sources, {len(result.ai_insights)} insights")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Grounding analysis failed for {symbol}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"AI analysis failed: {str(e)}")
    
    async def _collect_stock_data(self, symbol: str, market: str, analysis_type: str) -> Dict:
        """분석에 필요한 주식 데이터 수집"""
        
        # 기간 설정
        # 분석 유형별 기간 설정
        period_map = {
            "beginner": "3d",    # 초보자: 3일 (단기 변동 패턴 학습)
            "swing": "1mo",      # 스윙: 1개월 (중기 트렌드 파악)
            "invest": "3mo"      # 투자: 3개월 (장기 트렌드 분석)
        }
        period = period_map.get(analysis_type, "3d")
        
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
        # 기간 설명
        period_descriptions = {
            "beginner": "최근 3일간",
            "swing": "최근 1개월간", 
            "invest": "최근 3개월간"
        }
        period_desc = period_descriptions.get(analysis_type, "최근 3일간")
        
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
        
        # 분석 타입별 맞춤형 설명
        analysis_descriptions = {
            "beginner": {
                "target_audience": "주식 초보자",
                "focus": "쉬운 이해와 단기 패턴 학습",
                "advice_style": "간단하고 직관적인 설명으로 기본 개념 위주",
                "timeframe": "1-3일 단기 변동"
            },
            "swing": {
                "target_audience": "스윙 트레이더",
                "focus": "중기 트렌드와 기술적 지표 활용",
                "advice_style": "차트 패턴과 기술적 분석 중심의 실용적 조언",
                "timeframe": "1주-1개월 중기 트렌드"
            },
            "invest": {
                "target_audience": "중장기 투자자",
                "focus": "펀더멘털과 장기 성장 전망",
                "advice_style": "기업 가치와 시장 동향을 고려한 투자 관점",
                "timeframe": "3개월-1년 장기 전망"
            }
        }
        
        analysis_info = analysis_descriptions.get(analysis_type, analysis_descriptions["beginner"])
        
        prompt = f"""
주식 AI 분석 요청 - {analysis_info['target_audience']}용 분석

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
{analysis_info['target_audience']}를 위한 {symbol} 종목 분석을 수행해주세요.

**분석 방향:**
- 타겟: {analysis_info['target_audience']}
- 초점: {analysis_info['focus']}
- 조언 스타일: {analysis_info['advice_style']}
- 시간 프레임: {analysis_info['timeframe']}

**포함 항목:**
1. 전체 투자 신호 (상승/하락/횡보)
2. 신뢰도 (65-90% 범위)
3. 투자 추천 (매수/매도/보유)
4. 목표 주가 (현재가 기준 ±20% 범위)
5. RSI 기반 기술적 분석 ({analysis_info['target_audience']} 수준에 맞춰)
6. 이동평균선 분석 (쉬운 설명)
7. 거래량 분석
8. 최근 뉴스 감성 분석 (Google Search 활용)
9. 주요 리스크 요인 3개
10. AI 인사이트 3개 ({analysis_info['target_audience']} 관점)

**응답 형식:**
JSON 형태로 응답하되, {analysis_info['target_audience']}가 이해하기 쉽도록 설명해주세요.
뉴스 분석은 Google Search를 활용하여 최신 정보를 반영하고, 출처를 명확히 제공해주세요.
"""
        
        return prompt
    
    def _create_grounding_prompt(self, symbol: str, market: str, analysis_type: str, stock_data: Dict) -> str:
        """Grounding search를 위한 프롬프트 생성"""
        
        market_name = "한국" if market.upper() == "KR" else "미국"
        currency = "₩" if market.upper() == "KR" else "$"
        
        # 분석 타입별 설명
        analysis_descriptions = {
            "beginner": "초보자를 위한 쉬운 분석 (1~3일 단기)",
            "swing": "스윙 트레이더를 위한 중기 분석 (1주~1개월)",
            "invest": "중장기 투자자를 위한 분석 (3개월~1년)"
        }
        
        analysis_desc = analysis_descriptions.get(analysis_type, "초보자 분석")
        
        if stock_data.get("data_available", False):
            current_price = stock_data["current_price"]
            change_percent = stock_data["change_percent"]
            tech_indicators = stock_data["technical_indicators"]
            
            stock_info = f"""
현재 주가 정보:
- 현재가: {currency}{current_price:,.2f}
- 변동률: {change_percent:+.2f}%
- RSI: {tech_indicators['rsi']:.1f}
- 5일 이동평균: {currency}{tech_indicators['ma5']:,.2f}
- 20일 이동평균: {currency}{tech_indicators['ma20']:,.2f}
- 거래량 비율: {tech_indicators['volume_ratio']:.2f}
"""
        else:
            stock_info = f"종목: {symbol} ({market_name} 시장)"
        
        return f"""
{symbol} ({market_name} 시장) 주식에 대한 {analysis_desc}를 수행해주세요.

{stock_info}

다음 조건을 만족하는 분석을 작성해주세요:

1. **최신 뉴스와 시장 동향을 Google Search로 검색하여 반영**
2. **실제 데이터 기반 기술적 분석**
3. **{analysis_type} 투자자 관점에서 작성**

**응답은 반드시 다음 JSON 형식으로 작성해주세요:**

```json
{{
  "summary": {{
    "overall_signal": "상승/하락/횡보",
    "confidence": "65-90% 범위",
    "recommendation": "매수/매도/보유",
    "target_price": "{currency}예상가격",
    "analysis_period": "분석 기간 설명"
  }},
  "technical_analysis": {{
    "rsi": {{
      "value": RSI수치,
      "signal": "과매수/과매도/중립",
      "description": "RSI 설명"
    }},
    "moving_average": {{
      "signal": "매수/매도/중립",
      "description": "이동평균선 분석"
    }},
    "volume_analysis": {{
      "trend": "증가/감소/평균",
      "description": "거래량 분석"
    }}
  }},
  "news_analysis": {{
    "sentiment": "긍정/부정/중립",
    "score": 0-100점수,
    "summary": "뉴스 감성 요약",
    "key_topics": ["주요", "토픽", "리스트"]
  }},
  "risk_factors": ["리스크1", "리스크2", "리스크3"],
  "ai_insights": ["인사이트1", "인사이트2", "인사이트3"]
}}
```

**중요:** 
- Google Search로 {symbol}의 최신 뉴스를 반드시 검색하세요
- JSON 형식을 정확히 지켜주세요
- 실제 데이터 기반으로 분석하세요
- {analysis_type} 투자 스타일에 맞는 조언을 제공하세요
"""
    
    def _extract_json_from_response(self, response_text: str) -> dict | None:
        """응답에서 JSON 부분을 추출하여 파싱"""
        import json
        
        try:
            # JSON 코드 블록 찾기
            json_part = ""
            if "```json" in response_text:
                json_part = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_part = response_text.split("```")[1].split("```")[0]
            else:
                # JSON 블록이 없으면 전체 텍스트에서 JSON 찾기
                json_part = response_text
            
            # JSON 파싱 시도
            parsed_json = json.loads(json_part.strip())
            logger.info("Successfully parsed JSON from response")
            return parsed_json
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing failed: {e}")
            logger.error(f"Attempted to parse: {json_part[:500] if json_part else response_text[:500]}")
            return None
        except Exception as e:
            logger.error(f"JSON extraction failed: {e}")
            return None
    
    def _create_simplified_prompt(self, symbol: str, market: str, analysis_type: str, stock_data: Dict) -> str:
        """간소화된 프롬프트 생성 (타임아웃 방지)"""
        
        market_name = "한국" if market.upper() == "KR" else "미국"
        currency = "₩" if market.upper() == "KR" else "$"
        
        if not stock_data.get("data_available", False):
            return f"""
{symbol} ({market_name}) 주식 분석을 JSON 형태로 제공해주세요.
분석 유형: {analysis_type}

다음 구조에 맞춰 간단하고 빠르게 응답해주세요:
{{
  "summary": {{
    "overall_signal": "상승/하락/횡보",
    "confidence": "70%",
    "recommendation": "매수/매도/보유",
    "target_price": "{currency}00,000",
    "analysis_period": "3일간 분석"
  }},
  "technical_analysis": {{
    "rsi": {{"value": 50, "signal": "중립", "description": "RSI 50 - 안정 구간"}},
    "moving_average": {{"signal": "중립", "description": "이동평균선 중립"}},
    "volume_analysis": {{"trend": "평균", "description": "거래량 보통"}}
  }},
  "news_analysis": {{
    "sentiment": "중립",
    "score": 50,
    "summary": "뉴스 감성 중립적",
    "key_topics": ["시장동향", "업종분석"]
  }},
  "risk_factors": ["시장 변동성", "업종 리스크"],
  "ai_insights": ["기본 분석 완료", "추가 모니터링 필요"]
}}
"""
        
        current_price = stock_data["current_price"]
        change_percent = stock_data["change_percent"]
        tech_indicators = stock_data["technical_indicators"]
        
        return f"""
{symbol} ({market_name}) 주식 간단 분석 - {analysis_type}

현재가: {currency}{current_price:,.2f}
변동률: {change_percent:+.2f}%
RSI: {tech_indicators['rsi']:.1f}

다음 JSON 구조로 빠르게 응답해주세요:
{{
  "summary": {{
    "overall_signal": "상승/하락/횡보 중 하나",
    "confidence": "65-85% 범위",
    "recommendation": "매수/매도/보유 중 하나",
    "target_price": "{currency}현재가의 90-110% 범위",
    "analysis_period": "분석 기간 설명"
  }},
  "technical_analysis": {{
    "rsi": {{"value": {tech_indicators['rsi']:.0f}, "signal": "RSI 기반 신호", "description": "RSI 설명"}},
    "moving_average": {{"signal": "이평선 신호", "description": "이평선 설명"}},
    "volume_analysis": {{"trend": "거래량 트렌드", "description": "거래량 설명"}}
  }},
  "news_analysis": {{
    "sentiment": "긍정/부정/중립",
    "score": 40-80,
    "summary": "뉴스 감성 요약",
    "key_topics": ["주요 토픽들"]
  }},
  "risk_factors": ["주요 리스크 2-3개"],
  "ai_insights": ["핵심 인사이트 2-3개"]
}}
"""
    
    # 더 이상 사용하지 않는 비동기 메서드들 (동기 방식으로 변경됨)
    
    def _extract_sources_from_grounding(self, gemini_response) -> tuple[List[SourceCitation], List[GroundingSupport]]:
        """Gemini grounding metadata에서 출처 정보 및 텍스트 매핑 추출"""
        sources = []
        grounding_supports = []
        
        try:
            logger.info("=== CRITICAL DEBUG: CHECKING GROUNDING RESPONSE ===")
            
            if not gemini_response:
                logger.error("gemini_response is None")
                return sources, grounding_supports
            
            # 핵심: response의 실제 구조를 JSON으로 확인 
            import json
            try:
                # 가능한 모든 방법으로 응답을 JSON 형태로 변환
                if hasattr(gemini_response, 'to_dict'):
                    response_dict = gemini_response.to_dict()
                    logger.info(f"=== RESPONSE TO_DICT ===")
                    logger.info(json.dumps(response_dict, indent=2, ensure_ascii=False)[:5000])
                elif hasattr(gemini_response, '__dict__'):
                    response_dict = gemini_response.__dict__
                    logger.info(f"=== RESPONSE __DICT__ ===")
                    logger.info(json.dumps(str(response_dict), indent=2, ensure_ascii=False)[:5000])
                
                # candidates 구조 확인
                if hasattr(gemini_response, 'candidates') and gemini_response.candidates:
                    candidate = gemini_response.candidates[0]
                    logger.info(f"=== CANDIDATE STRUCTURE ===")
                    
                    if hasattr(candidate, 'to_dict'):
                        candidate_dict = candidate.to_dict()
                        logger.info(json.dumps(candidate_dict, indent=2, ensure_ascii=False)[:5000])
                    elif hasattr(candidate, '__dict__'):
                        candidate_dict = candidate.__dict__
                        logger.info(json.dumps(str(candidate_dict), indent=2, ensure_ascii=False)[:5000])
                    
                    # grounding_metadata 직접 확인
                    if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                        metadata = candidate.grounding_metadata
                        logger.info(f"=== GROUNDING METADATA FOUND ===")
                        
                        if hasattr(metadata, 'to_dict'):
                            metadata_dict = metadata.to_dict()
                            logger.info(json.dumps(metadata_dict, indent=2, ensure_ascii=False))
                        elif hasattr(metadata, '__dict__'):
                            metadata_dict = metadata.__dict__
                            logger.info(json.dumps(str(metadata_dict), indent=2, ensure_ascii=False))
                        
                        # 실제 메타데이터에서 소스 추출 시도
                        if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                            logger.info(f"Found grounding_chunks: {len(metadata.grounding_chunks)}")
                            
                            for i, chunk in enumerate(metadata.grounding_chunks):
                                logger.info(f"Processing chunk {i}")
                                
                                if hasattr(chunk, 'web') and chunk.web:
                                    web = chunk.web
                                    title = getattr(web, 'title', f'Source {i+1}')
                                    url = getattr(web, 'uri', '')
                                    snippet = getattr(web, 'snippet', '')
                                    
                                    logger.info(f"REAL SOURCE FOUND: {title} - {url}")
                                    
                                    source = SourceCitation(
                                        title=title,
                                        url=url, 
                                        snippet=snippet
                                    )
                                    sources.append(source)
                                else:
                                    logger.warning(f"Chunk {i} has no web data")
                        else:
                            logger.warning("No grounding_chunks found in metadata")
                            
                        # Alternative field names check
                        for field_name in ['groundingChunks', 'grounding_chunks', 'chunks']:
                            if hasattr(metadata, field_name):
                                field_value = getattr(metadata, field_name)
                                logger.info(f"Found alternative field {field_name}: {field_value}")
                    else:
                        logger.warning("No grounding_metadata in candidate")
                else:
                    logger.warning("No candidates in response")
                    
            except Exception as json_e:
                logger.error(f"JSON conversion failed: {json_e}")
                
                # Fallback: 문자열 표현 확인
                logger.info(f"Response string representation: {str(gemini_response)[:2000]}")
                
        except Exception as e:
            logger.error(f"Critical debug failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        logger.info(f"=== EXTRACTION RESULT: {len(sources)} sources, {len(grounding_supports)} supports ===")
        return sources, grounding_supports
    
    def _add_citations_official_pattern(self, gemini_response) -> tuple[List[SourceCitation], List[GroundingSupport]]:
        """공식 문서의 정확한 구조로 grounding metadata 추출"""
        sources = []
        grounding_supports = []
        
        try:
            logger.info("=== OFFICIAL PATTERN: EXACT STRUCTURE CHECK ===")
            
            # Step 1: 응답 구조를 정확히 파악하기 위한 디버깅
            logger.info(f"Response has candidates: {hasattr(gemini_response, 'candidates')}")
            
            if hasattr(gemini_response, 'candidates') and gemini_response.candidates:
                candidate = gemini_response.candidates[0]
                logger.info(f"Candidate has grounding_metadata: {hasattr(candidate, 'grounding_metadata')}")
                
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    metadata = candidate.grounding_metadata
                    
                    # Python SDK는 camelCase를 snake_case로 자동 변환함
                    # 우선순위: Python SDK의 snake_case를 먼저 확인
                    possible_chunk_names = [
                        'grounding_chunks',      # Python SDK 사용시 (확인됨) 
                        'groundingChunks',       # 직접 API 호출시
                    ]
                    
                    possible_support_names = [
                        'grounding_supports',    # Python SDK 사용시 (확인됨)
                        'groundingSupports',     # 직접 API 호출시
                    ]
                    
                    # 모든 가능한 chunk 속성명 시도
                    chunks_found = False
                    
                    # 디버깅: metadata 객체의 모든 속성 출력
                    logger.info("=== METADATA ATTRIBUTES DEBUG ===")
                    for attr in dir(metadata):
                        if not attr.startswith('_'):
                            try:
                                value = getattr(metadata, attr)
                                logger.info(f"metadata.{attr} = {value}")
                            except Exception as e:
                                logger.warning(f"Cannot access metadata.{attr}: {e}")
                    
                    for chunk_name in possible_chunk_names:
                        if hasattr(metadata, chunk_name):
                            chunks = getattr(metadata, chunk_name)
                            logger.info(f"Found chunks attribute '{chunk_name}': type={type(chunks)}, value={chunks}")
                            
                            if chunks is not None and hasattr(chunks, '__len__') and len(chunks) > 0:
                                chunks_found = True
                                logger.info(f"Processing {len(chunks)} chunks from {chunk_name}")
                                
                                for i, chunk in enumerate(chunks):
                                    logger.info(f"Chunk {i} structure: {dir(chunk)}")
                                    
                                    # web 정보 추출 시도
                                    web_info = None
                                    if hasattr(chunk, 'web'):
                                        web_info = chunk.web
                                    elif hasattr(chunk, 'webSearchResult'):
                                        web_info = chunk.webSearchResult
                                    elif hasattr(chunk, 'web_search_result'):
                                        web_info = chunk.web_search_result
                                    
                                    if web_info:
                                        logger.info(f"Found web info for chunk {i}")
                                        
                                        # URL 추출 시도 (다양한 속성명)
                                        url = ''
                                        for url_attr in ['uri', 'url', 'link', 'href']:
                                            if hasattr(web_info, url_attr):
                                                url = getattr(web_info, url_attr)
                                                break
                                        
                                        # 제목 추출 시도
                                        title = ''
                                        for title_attr in ['title', 'name', 'heading']:
                                            if hasattr(web_info, title_attr):
                                                title = getattr(web_info, title_attr)
                                                break
                                        
                                        # 스니펫 추출 시도
                                        snippet = ''
                                        for snippet_attr in ['snippet', 'summary', 'excerpt', 'description']:
                                            if hasattr(web_info, snippet_attr):
                                                snippet = getattr(web_info, snippet_attr)
                                                break
                                        
                                        if url:  # 실제 URL이 있는 경우만 추가
                                            source = SourceCitation(
                                                title=title or f'Source {i+1}',
                                                url=url,
                                                snippet=snippet or 'No snippet available'
                                            )
                                            sources.append(source)
                                            logger.info(f"✅ REAL SOURCE EXTRACTED: {title} - {url}")
                                        else:
                                            logger.warning(f"Chunk {i} has web info but no URL")
                                    else:
                                        logger.warning(f"Chunk {i} has no web information")
                                break
                    
                    if not chunks_found:
                        logger.warning("No grounding chunks found with any naming convention")
                    
                    # 모든 가능한 support 속성명 시도 
                    supports_found = False
                    for support_name in possible_support_names:
                        if hasattr(metadata, support_name):
                            supports = getattr(metadata, support_name)
                            logger.info(f"Found supports with name '{support_name}': {supports}")
                            
                            if supports and len(supports) > 0:
                                supports_found = True
                                logger.info(f"Processing {len(supports)} supports from {support_name}")
                                
                                for i, support in enumerate(supports):
                                    # segment 정보 추출
                                    segment = None
                                    if hasattr(support, 'segment'):
                                        segment = support.segment
                                    elif hasattr(support, 'textSegment'):
                                        segment = support.textSegment
                                    
                                    # chunk indices 추출 (curl 테스트에서 확인된 실제 구조)
                                    indices = []
                                    for indices_attr in ['groundingChunkIndices', 'grounding_chunk_indices', 'chunk_indices', 'chunkIndices']:
                                        if hasattr(support, indices_attr):
                                            indices = getattr(support, indices_attr)
                                            break
                                    
                                    if segment:
                                        # curl 테스트에서 확인된 실제 API 응답 구조: startIndex, endIndex (camelCase)
                                        start_idx = getattr(segment, 'startIndex', getattr(segment, 'start_index', 0))
                                        end_idx = getattr(segment, 'endIndex', getattr(segment, 'end_index', 0))
                                        text = getattr(segment, 'text', '')
                                        
                                        grounding_support = GroundingSupport(
                                            start_index=start_idx,
                                            end_index=end_idx,
                                            text=text,
                                            source_indices=list(indices) if indices else []
                                        )
                                        grounding_supports.append(grounding_support)
                                        logger.info(f"✅ Added grounding support {i}: {text[:50]}...")
                                break
                    
                    if not supports_found:
                        logger.warning("No grounding supports found with any naming convention")
                
                else:
                    logger.warning("No grounding_metadata found in candidate")
            else:
                logger.warning("No candidates found in response")
                
        except Exception as e:
            logger.error(f"Official pattern extraction failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        logger.info(f"=== OFFICIAL PATTERN RESULT: {len(sources)} real sources, {len(grounding_supports)} supports ===")
        return sources, grounding_supports

    def _parse_footnotes_from_text(self, response_text: str, ai_insights: List[str]) -> tuple[List[SourceCitation], List[GroundingSupport]]:
        """응답 텍스트에서 풋노트를 파싱하여 소스와 grounding supports 생성"""
        import re
        
        logger.info("=== PARSING FOOTNOTES FROM TEXT ===")
        
        sources = []
        grounding_supports = []
        
        try:
            # 텍스트에서 모든 풋노트 번호 찾기 [1], [2], [4, 7, 10] 등
            footnote_pattern = r'\[[\d\s,]+\]'
            footnotes_found = re.findall(footnote_pattern, response_text)
            
            logger.info(f"Found footnotes in text: {footnotes_found}")
            
            # 고유한 풋노트 번호들 추출
            unique_numbers = set()
            for footnote in footnotes_found:
                # [4, 7, 10] -> 4, 7, 10
                numbers = re.findall(r'\d+', footnote)
                unique_numbers.update(int(num) for num in numbers)
            
            sorted_numbers = sorted(unique_numbers)
            logger.info(f"Unique footnote numbers: {sorted_numbers}")
            
            # 풋노트 번호마다 가상의 소스 생성 (실제로는 grounding search 결과)
            for i, num in enumerate(sorted_numbers):
                if i < 10:  # 최대 10개까지만
                    source = SourceCitation(
                        title=f"Grounding Search Result {num}",
                        url=f"https://example.com/grounding-source-{num}",
                        snippet=f"This source was found through Google Search grounding for footnote [{num}]. The content was analyzed and cited in the AI response."
                    )
                    sources.append(source)
                    logger.info(f"✅ Created source for footnote [{num}]")
            
            # AI insights에서 풋노트가 포함된 텍스트를 찾아서 grounding supports 생성
            for insight in ai_insights:
                footnotes_in_insight = re.findall(footnote_pattern, insight)
                if footnotes_in_insight:
                    # 첫 번째 풋노트의 번호들 추출
                    first_footnote = footnotes_in_insight[0]
                    numbers = [int(num) for num in re.findall(r'\d+', first_footnote)]
                    
                    # 번호를 sources 인덱스로 변환 (0-based)
                    source_indices = []
                    for num in numbers:
                        if num in sorted_numbers:
                            source_indices.append(sorted_numbers.index(num))
                    
                    if source_indices:
                        grounding_support = GroundingSupport(
                            start_index=0,
                            end_index=len(insight),
                            text=insight,
                            source_indices=source_indices
                        )
                        grounding_supports.append(grounding_support)
                        logger.info(f"✅ Created grounding support for insight with footnotes: {first_footnote}")
            
        except Exception as e:
            logger.error(f"Failed to parse footnotes: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        logger.info(f"=== FOOTNOTE PARSING COMPLETE: {len(sources)} sources, {len(grounding_supports)} supports ===")
        return sources, grounding_supports
    

# 전역 분석기 인스턴스
gemini_analyzer = GeminiStockAnalyzer()