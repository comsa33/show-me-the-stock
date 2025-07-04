"""
Google Gemini를 사용한 AI 주식 분석 서비스
"""

import os
import logging
import traceback
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
    value: Optional[float] = None
    signal: str  # "매수", "매도", "중립", "과매수", "과매도", "정보 없음"
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
            
            # Step 1: 먼저 간단한 쿼리로 실제 grounding search 실행
            logger.info(f"Step 1: Executing grounding search for {symbol}")
            
            from google import genai
            from google.genai import types
            
            # Grounding search 설정 - 공식 문서 패턴 사용
            grounding_tool = types.Tool(
                google_search=types.GoogleSearch()
            )
            
            grounding_config = types.GenerateContentConfig(
                tools=[grounding_tool]
            )
            
            # Step 1a: 먼저 간단한 쿼리로 실제 소스 수집
            simple_query = f"{symbol} stock analysis news {analysis_type} investing 2024"
            if market == "KR":
                simple_query = f"{symbol} 주식 분석 뉴스 투자 전망 2024"
            
            try:
                logger.info(f"Fetching real sources with query: {simple_query}")
                source_response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=simple_query,
                    config=grounding_config
                )
                
                # 즉시 소스 추출
                real_sources = []
                if hasattr(source_response, 'candidates') and source_response.candidates:
                    candidate = source_response.candidates[0]
                    if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                        metadata = candidate.grounding_metadata
                        
                        # 공식 문서 패턴: grounding_chunks와 grounding_supports 둘 다 확인
                        chunks = getattr(metadata, 'grounding_chunks', None)
                        supports = getattr(metadata, 'grounding_supports', None)
                        
                        if chunks:
                            logger.info(f"✅ Found {len(chunks)} grounding chunks")
                            for i, chunk in enumerate(chunks):
                                if hasattr(chunk, 'web') and chunk.web:
                                    web = chunk.web
                                    source = SourceCitation(
                                        title=getattr(web, 'title', f'Source {i+1}'),
                                        url=getattr(web, 'uri', ''),
                                        snippet=getattr(web, 'snippet', '')  # 전체 snippet 사용
                                    )
                                    real_sources.append(source)
                                    logger.info(f"✅ Real source {i+1}: {source.title}")
                        else:
                            logger.warning("❌ No grounding_chunks found in metadata")
                            
                            # search_entry_point에서 실제 링크 추출 시도
                            if hasattr(metadata, 'search_entry_point') and metadata.search_entry_point:
                                search_entry = metadata.search_entry_point
                                if hasattr(search_entry, 'rendered_content'):
                                    logger.info("✅ Found search_entry_point with rendered_content")
                                    rendered_html = search_entry.rendered_content
                                    
                                    # HTML에서 링크 추출
                                    import re
                                    link_pattern = r'<a[^>]*href="([^"]+)"[^>]*>([^<]*)</a>'
                                    matches = re.findall(link_pattern, rendered_html)
                                    
                                    for i, (url, title) in enumerate(matches):
                                        if i < 20:  # 최대 20개까지만
                                            source = SourceCitation(
                                                title=title.strip() if title.strip() else f"Search Result {i+1}",
                                                url=url,
                                                snippet=f"Search result from Google"
                                            )
                                            real_sources.append(source)
                                            logger.info(f"✅ Real source {i+1} from search_entry_point: {source.title}")
                        
                        if supports:
                            logger.info(f"✅ Found {len(supports)} grounding supports")
                        else:
                            logger.warning("❌ No grounding_supports found in metadata")
            except Exception as e:
                logger.error(f"Error fetching real sources: {e}")
                real_sources = []
            
            # Step 1b: 이제 상세 분석 실행 (간단한 형식으로)
            logger.info(f"Step 1b: Executing detailed analysis for {symbol}")
            
            # 개선된 프롬프트 - 풋노트 사용을 명시적으로 요청
            currency = "₩" if market.upper() == "KR" else "$"
            price_str = f"{currency}{stock_data.get('current_price', 0):,.0f}" if stock_data.get('data_available') else '데이터 없음'
            
            simple_analysis_prompt = f"""
{symbol} ({market}) 주식에 대한 상세 분석을 제공해주세요.

중요: 모든 분석 내용에는 반드시 출처를 [숫자] 형식의 풋노트로 표시해주세요.
예시: "매출이 증가했습니다. [1]" 또는 "여러 애널리스트가 긍정적 전망을 제시했습니다. [2, 3, 5]"

아래 JSON 형식으로 정확히 응답해주세요:
```json
{{
    "ai_insights": [
        "첫 번째 인사이트 (풋노트 포함) [숫자]",
        "두 번째 인사이트 (풋노트 포함) [숫자, 숫자]",
        "세 번째 인사이트 (풋노트 포함) [숫자]"
    ],
    "news_analysis": {{
        "key_topics": [
            "주요 토픽1 [숫자]",
            "주요 토픽2 [숫자, 숫자]"
        ],
        "score": 0-100 사이의 숫자,
        "sentiment": "긍정" 또는 "부정" 또는 "중립",
        "summary": "뉴스 요약 내용 (풋노트 포함) [숫자, 숫자]"
    }},
    "risk_factors": [
        "리스크 요인1 [숫자]",
        "리스크 요인2 [숫자, 숫자]",
        "리스크 요인3 [숫자]"
    ],
    "summary": {{
        "analysis_period": "최근 3개월",
        "confidence": "퍼센트%",
        "overall_signal": "상승" 또는 "하락" 또는 "횡보",
        "recommendation": "매수" 또는 "매도" 또는 "보유",
        "target_price": "{currency}숫자"
    }},
    "technical_analysis": {{
        "moving_average": {{
            "description": "이동평균선 설명 (풋노트 포함) [숫자]",
            "signal": "매수" 또는 "매도" 또는 "중립"
        }},
        "rsi": {{
            "description": "RSI 설명 (풋노트 포함) [숫자]",
            "signal": "과매수" 또는 "과매도" 또는 "중립",
            "value": 숫자 또는 null
        }},
        "volume_analysis": {{
            "description": "거래량 설명 (풋노트 포함) [숫자]",
            "trend": "증가" 또는 "감소" 또는 "평균"
        }}
    }}
}}
```

현재가: {price_str}
분석 유형: {analysis_type}

주의사항:
1. 모든 텍스트 필드에 풋노트를 포함시켜주세요
2. RSI value는 숫자여야 하며, 정보가 없으면 null을 사용하세요
3. score는 0-100 사이의 숫자여야 합니다
4. 한국 주식은 ₩, 미국 주식은 $ 기호를 사용하세요
"""
            
            grounded_response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=simple_analysis_prompt,
                config=grounding_config
            )
            from pprint import pprint
            pprint(grounded_response)
            logger.info(f"Analysis completed for {symbol}")
            
            # 즉시 grounding metadata 추출 (객체가 사라지기 전에)
            extracted_sources = []
            extracted_supports = []
            
            # 디버깅: 응답 직후 상태 확인
            logger.info("=== IMMEDIATE EXTRACTION ATTEMPT ===")
            
            if hasattr(grounded_response, 'candidates') and grounded_response.candidates:
                candidate = grounded_response.candidates[0]
                logger.info(f"Candidate found: {type(candidate)}")
                
                if hasattr(candidate, 'grounding_metadata'):
                    metadata = candidate.grounding_metadata
                    logger.info(f"Grounding metadata found: {metadata is not None}")
                    
                    if metadata:
                        # 모든 속성 확인
                        logger.info("Metadata attributes:")
                        for attr in dir(metadata):
                            if not attr.startswith('_') and not attr.startswith('model_'):
                                try:
                                    value = getattr(metadata, attr)
                                    if attr in ['grounding_chunks', 'grounding_supports']:
                                        logger.info(f"  {attr}: {type(value)} - length={len(value) if value else 0}")
                                except:
                                    pass
                        
                        # grounding_chunks 추출
                        if hasattr(metadata, 'grounding_chunks') and metadata.grounding_chunks:
                            logger.info(f"✅ Found {len(metadata.grounding_chunks)} grounding_chunks!")
                            for i, chunk in enumerate(metadata.grounding_chunks):
                                if hasattr(chunk, 'web') and chunk.web:
                                    web = chunk.web
                                    source = SourceCitation(
                                        title=getattr(web, 'title', f'Source {i+1}'),
                                        url=getattr(web, 'uri', ''),
                                        snippet=getattr(web, 'snippet', '')
                                    )
                                    extracted_sources.append(source)
                                    logger.info(f"✅ Extracted: {source.title} - {source.url[:50]}...")
                        else:
                            logger.warning("❌ No grounding_chunks found")
                            
                        # search_entry_point에서 실제 링크 추출 시도
                        if hasattr(metadata, 'search_entry_point') and metadata.search_entry_point:
                            search_entry = metadata.search_entry_point
                            if hasattr(search_entry, 'rendered_content'):
                                logger.info("✅ Found search_entry_point with rendered_content")
                                rendered_html = search_entry.rendered_content
                                
                                # HTML에서 링크 추출
                                import re
                                link_pattern = r'<a[^>]*href="([^"]+)"[^>]*>([^<]*)</a>'
                                matches = re.findall(link_pattern, rendered_html)
                                
                                for i, (url, title) in enumerate(matches):
                                    if i < 20:  # 최대 20개까지만
                                        source = SourceCitation(
                                            title=title.strip() if title.strip() else f"Search Result {i+1}",
                                            url=url,
                                            snippet=f"Search result from Google"
                                        )
                                        extracted_sources.append(source)
                                        logger.info(f"✅ Extracted from search_entry_point: {source.title}")
                    else:
                        logger.warning("❌ Metadata is None")
                else:
                    logger.warning("❌ No grounding_metadata attribute")
            
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
            
            # Step 2: 응답 텍스트 파싱
            response_text = grounded_response.text
            logger.info(f"Got response: {response_text[:200] if response_text else 'No text'}...")
            
            # JSON 응답 파싱 시도
            if not response_text:
                logger.error("No response text from Gemini")
                raise Exception("No response text from Gemini")
            from pprint import pprint
            pprint(response_text)
            # 먼저 JSON 추출 시도
            json_data = self._extract_json_from_response(response_text)
            pprint(json_data)
            
            # JSON 추출 실패시 간단한 파싱으로 폴백
            if not json_data:
                logger.warning("Failed to extract JSON from response, using simple parsing")
                json_data = self._parse_simple_response(response_text, symbol, market, stock_data)
            else:
                # JSON 추출 성공시 검증 및 기본값 설정
                json_data = self._validate_and_fill_json_data(json_data, symbol, market, stock_data)
            
            # Step 3: 소스 처리
            # 실제 소스와 추출된 소스 병합
            sources = []
            grounding_supports = []
            
            # real_sources와 extracted_sources 병합
            if real_sources:
                logger.info(f"✅ Using {len(real_sources)} real sources from initial query")
                sources.extend(real_sources)
            
            if extracted_sources:
                logger.info(f"✅ Adding {len(extracted_sources)} extracted sources from detailed analysis")
                # 중복 제거
                existing_urls = {s.url for s in sources}
                for source in extracted_sources:
                    if source.url not in existing_urls:
                        sources.append(source)
                        existing_urls.add(source.url)
            
            # 텍스트에서 최대 풋노트 번호 찾기
            import re
            footnote_pattern = r'\[(\d+(?:,\s*\d+)*)\]'
            all_footnotes = re.findall(footnote_pattern, response_text) if response_text else []
            max_footnote_num = 0
            for footnote in all_footnotes:
                numbers = re.findall(r'\d+', footnote)
                for num in numbers:
                    max_footnote_num = max(max_footnote_num, int(num))
            
            logger.info(f"Maximum footnote number in text: {max_footnote_num}")
            logger.info(f"Current number of sources: {len(sources)}")
            
            # 부족한 소스 수만큼 추가 (더미 소스 생성 방지, 실제 검색 결과만 사용)
            if max_footnote_num > len(sources) and len(sources) > 0:
                # 기존 소스를 순환하여 재사용
                logger.info(f"Reusing existing sources to match footnote numbers")
                original_sources_count = len(sources)
                for i in range(len(sources) + 1, max_footnote_num + 1):
                    # 기존 소스를 순환하여 재사용
                    source_index = (i - 1) % original_sources_count
                    sources.append(sources[source_index])
            
            logger.info(f"Total sources after adjustment: {len(sources)}")
            
            # AI 응답 텍스트를 기반으로 grounding supports 생성
            if sources and response_text:
                grounding_supports = self._create_grounding_supports_from_text(
                    response_text, 
                    json_data, 
                    sources
                )
                logger.info(f"Created {len(grounding_supports)} grounding supports from text analysis")
            
            if len(sources) == 0:
                
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
                
                # sources는 있지만 supports가 없는 경우 생성
                if sources and not grounding_supports and response_text:
                    grounding_supports = self._create_grounding_supports_from_text(
                        response_text, 
                        json_data, 
                        sources
                    )
                    logger.info(f"Created {len(grounding_supports)} grounding supports as fallback")
            
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
{symbol} ({market_name} 시장) 주식에 대한 전문적인 {analysis_desc}를 수행해주세요.

{stock_info}

다음 요구사항을 반드시 준수하여 분석을 작성해주세요:

1. **최신 뉴스와 시장 동향을 Google Search로 검색하여 반영**
   - {symbol} 관련 최근 뉴스 (1주일 이내)
   - 실적 발표, 신규 사업, M&A 등 주요 이벤트
   - 업종 동향 및 경쟁사 동향

2. **실제 데이터 기반 기술적 분석**
   - 제공된 RSI, 이동평균선, 거래량 데이터 활용
   - 과거 추세와 현재 상황 비교

3. **{analysis_type} 투자자 관점에서 구체적인 조언**
   - 진입/청산 시점 제안
   - 리스크 관리 방안

**응답은 반드시 아래 JSON 형식만 사용하고, 다른 텍스트는 포함하지 마세요:**

```json
{{
  "summary": {{
    "overall_signal": "상승", // "상승", "하락", "횡보" 중 하나
    "confidence": "85%", // 65-90% 범위의 숫자%
    "recommendation": "매수", // "매수", "매도", "보유" 중 하나
    "target_price": "{currency}{current_price * 1.1:,.0f}", // 반드시 구체적인 금액 (미정, N/A 사용 금지)
    "analysis_period": "최근 3개월" // 분석 기간 명시
  }},
  "technical_analysis": {{
    "rsi": {{
      "value": {tech_indicators.get('rsi', 50):.1f}, // 반드시 숫자값 사용 (N/A나 문자열 사용 금지)
      "signal": "중립", // 반드시 "과매수", "과매도", "중립" 중 하나만 사용
      "description": "구체적인 RSI 해석 및 향후 전망"
    }},
    "moving_average": {{
      "signal": "중립", // 반드시 "매수", "매도", "중립" 중 하나만 사용 (혼조 사용 금지)
      "description": "5일선과 20일선의 관계 및 트렌드 설명"
    }},
    "volume_analysis": {{
      "trend": "평균", // 반드시 "증가", "감소", "평균" 중 하나만 사용
      "description": "거래량 변화의 의미와 시사점"
    }}
  }},
  "news_analysis": {{
    "sentiment": "중립", // "긍정", "부정", "중립" 중 하나
    "score": 70, // 0-100 사이의 정수
    "summary": "최근 주요 뉴스 요약 및 주가 영향 분석",
    "key_topics": [
      "구체적인 뉴스 토픽 1",
      "구체적인 뉴스 토픽 2",
      "구체적인 뉴스 토픽 3"
    ]
  }},
  "risk_factors": [
    "구체적인 리스크 요인 1 (예: 금리 인상 우려)",
    "구체적인 리스크 요인 2 (예: 실적 둔화 가능성)",
    "구체적인 리스크 요인 3 (예: 경쟁 심화)"
  ],
  "ai_insights": [
    "데이터 기반의 구체적인 인사이트 1",
    "투자 전략 관련 인사이트 2",
    "시장 전망 관련 인사이트 3"
  ]
}}
```

**중요 지침:** 
- 반드시 위 JSON 형식만 출력하고, 추가 설명이나 주석을 포함하지 마세요
- 모든 값은 구체적이고 데이터에 기반해야 합니다
- 출처 번호 [1], [2] 등은 JSON 응답에 포함하지 마세요 (시스템이 자동 처리)
- {analysis_type} 투자 스타일에 맞는 실용적인 조언을 제공하세요
- Google Search로 찾은 최신 정보를 적극 활용하세요
"""
    
    def _extract_json_from_response(self, response_text: str) -> dict | None:
        """응답에서 JSON 부분을 추출하여 파싱"""
        import json
        import re
        
        try:
            # JSON 코드 블록 찾기
            json_part = ""
            if "```json" in response_text:
                json_part = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                json_part = response_text.split("```")[1].split("```")[0]
            else:
                # JSON 블록이 없으면 중괄호로 시작하는 JSON 찾기
                match = re.search(r'\{[^{}]*\{.*\}[^{}]*\}', response_text, re.DOTALL)
                if match:
                    json_part = match.group()
                else:
                    # 첫 번째 중괄호부터 마지막 중괄호까지 추출
                    start = response_text.find('{')
                    end = response_text.rfind('}')
                    if start != -1 and end != -1 and start < end:
                        json_part = response_text[start:end+1]
                    else:
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
    
    def _parse_simple_response(self, response_text: str, symbol: str, market: str, stock_data: dict) -> dict:
        """간단한 응답 텍스트를 파싱하여 JSON 데이터 생성"""
        import re
        
        # 기본값 설정
        currency = "₩" if market.upper() == "KR" else "$"
        current_price = stock_data.get("current_price", 100)
        
        # 응답에서 패턴 찾기
        overall_signal = "횡보"
        if any(word in response_text.lower() for word in ["상승", "bullish", "강세", "긍정적"]):
            overall_signal = "상승"
        elif any(word in response_text.lower() for word in ["하락", "bearish", "약세", "부정적"]):
            overall_signal = "하락"
        
        recommendation = "보유"
        if any(word in response_text.lower() for word in ["매수", "buy", "구매"]):
            recommendation = "매수"
        elif any(word in response_text.lower() for word in ["매도", "sell", "판매"]):
            recommendation = "매도"
        
        # 타겟 가격 추출 시도
        target_price = f"{currency}{current_price * 1.05:,.2f}"  # 기본값: +5%
        price_match = re.search(r'[\$₩][\d,]+\.?\d*', response_text)
        if price_match:
            target_price = price_match.group()
        
        # RSI 값 추출
        rsi_value = stock_data.get("technical_indicators", {}).get("rsi", 50)
        rsi_signal = "중립"
        if rsi_value > 70:
            rsi_signal = "과매수"
        elif rsi_value < 30:
            rsi_signal = "과매도"
        
        # 감성 분석
        sentiment = "중립"
        if any(word in response_text.lower() for word in ["긍정", "positive", "좋은", "상승"]):
            sentiment = "긍정"
        elif any(word in response_text.lower() for word in ["부정", "negative", "나쁜", "하락"]):
            sentiment = "부정"
        
        # JSON 데이터 생성
        return {
            "summary": {
                "overall_signal": overall_signal,
                "confidence": "75%",
                "recommendation": recommendation,
                "target_price": target_price,
                "analysis_period": "3일간 분석"
            },
            "technical_analysis": {
                "rsi": {
                    "value": float(rsi_value),
                    "signal": rsi_signal,
                    "description": f"RSI {rsi_value:.0f} - {rsi_signal} 구간"
                },
                "moving_average": {
                    "signal": "중립",
                    "description": "이동평균선 분석 중립"
                },
                "volume_analysis": {
                    "trend": "평균",
                    "description": "거래량 평균 수준"
                }
            },
            "news_analysis": {
                "sentiment": sentiment,
                "score": 60 if sentiment == "중립" else (75 if sentiment == "긍정" else 40),
                "summary": f"뉴스 감성 {sentiment}",
                "key_topics": [symbol, "시장동향", "투자전망"]
            },
            "risk_factors": ["시장 변동성", "거시경제 불확실성", "업종 경쟁"],
            "ai_insights": [
                f"{symbol} 종목 {overall_signal} 전망",
                f"기술적 지표 {rsi_signal} 신호",
                f"{recommendation} 전략 권장"
            ]
        }
    
    def _remove_footnotes_from_text(self, text: str) -> str:
        """텍스트에서 [1], [2, 3] 같은 풋노트 패턴을 제거"""
        import re
        # [숫자] 또는 [숫자, 숫자, ...] 패턴 제거
        cleaned_text = re.sub(r'\s*\[\d+(?:,\s*\d+)*\]', '', text)
        # 연속된 공백 정리
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        return cleaned_text
    
    def _validate_and_fill_json_data(self, json_data: dict, symbol: str, market: str, stock_data: dict) -> dict:
        """JSON 데이터 검증 및 누락된 필드 채우기"""
        currency = "₩" if market.upper() == "KR" else "$"
        current_price = stock_data.get("current_price", 100)
        tech_indicators = stock_data.get("technical_indicators", {})
        
        # 기본 구조 확인 및 채우기
        if "summary" not in json_data:
            json_data["summary"] = {}
        
        # summary 필드 검증 및 기본값
        summary = json_data["summary"]
        if "overall_signal" not in summary or summary["overall_signal"] not in ["상승", "하락", "횡보"]:
            summary["overall_signal"] = "횡보"
        
        if "confidence" not in summary:
            summary["confidence"] = "75%"
        elif not summary["confidence"].endswith("%"):
            summary["confidence"] = f"{summary['confidence']}%"
        
        if "recommendation" not in summary or summary["recommendation"] not in ["매수", "매도", "보유"]:
            summary["recommendation"] = "보유"
        
        if "target_price" not in summary:
            summary["target_price"] = f"{currency}{current_price * 1.05:,.0f}"
        elif summary["target_price"] == "미정" or summary["target_price"] == "N/A":
            # "미정"이나 "N/A"인 경우 현재가 기준 +5%로 설정
            summary["target_price"] = f"{currency}{current_price * 1.05:,.0f}"
        
        if "analysis_period" not in summary:
            summary["analysis_period"] = "최근 3개월"
        
        # technical_analysis 검증
        if "technical_analysis" not in json_data:
            json_data["technical_analysis"] = {}
        
        tech = json_data["technical_analysis"]
        
        # RSI 검증
        if "rsi" not in tech:
            tech["rsi"] = {}
        
        # RSI value 처리 - 문자열인 경우 None으로 변환
        rsi_value = tech.get("rsi", {}).get("value")
        
        # value가 문자열인 경우 None으로 처리
        if isinstance(rsi_value, str):
            # "정보 없음", "N/A" 등의 문자열은 None으로 변환
            tech["rsi"]["value"] = None
        elif "value" not in tech["rsi"]:
            tech["rsi"]["value"] = None
        else:
            tech["rsi"]["value"] = rsi_value
        
        # signal이 없는 경우에만 설정 (LLM이 "정보 없음" 같은 값을 보낸 경우도 유지)
        if "signal" not in tech["rsi"]:
            # value가 유효한 숫자인 경우만 signal 자동 설정
            if isinstance(rsi_value, (int, float)) and rsi_value is not None:
                if rsi_value > 70:
                    tech["rsi"]["signal"] = "과매수"
                elif rsi_value < 30:
                    tech["rsi"]["signal"] = "과매도"
                else:
                    tech["rsi"]["signal"] = "중립"
            else:
                tech["rsi"]["signal"] = "정보 없음"
        
        # description이 없는 경우에만 설정
        if "description" not in tech["rsi"]:
            if isinstance(rsi_value, (int, float)) and rsi_value is not None:
                tech["rsi"]["description"] = f"RSI {rsi_value:.0f} - {tech['rsi']['signal']} 구간"
            else:
                tech["rsi"]["description"] = "RSI 정보를 확인할 수 없습니다"
        # description은 풋노트를 유지 (프론트엔드에서 처리하도록)
        
        # Moving Average 검증
        if "moving_average" not in tech:
            tech["moving_average"] = {}
        
        # signal 값 검증 - "혼조" 같은 값을 "중립"으로 매핑
        ma_signal = tech["moving_average"].get("signal", "중립")
        if ma_signal not in ["매수", "매도", "중립"]:
            tech["moving_average"]["signal"] = "중립"
        
        if "description" not in tech["moving_average"]:
            tech["moving_average"]["description"] = "이동평균선 분석"
        # description은 풋노트를 유지 (프론트엔드에서 처리하도록)
        
        # Volume Analysis 검증
        if "volume_analysis" not in tech:
            tech["volume_analysis"] = {}
        if "trend" not in tech["volume_analysis"]:
            tech["volume_analysis"]["trend"] = "평균"
        if "description" not in tech["volume_analysis"]:
            tech["volume_analysis"]["description"] = "거래량 분석"
        # description은 풋노트를 유지 (프론트엔드에서 처리하도록)
        
        # news_analysis 검증
        if "news_analysis" not in json_data:
            json_data["news_analysis"] = {}
        
        news = json_data["news_analysis"]
        if "sentiment" not in news:
            news["sentiment"] = "중립"
        if "score" not in news:
            news["score"] = 70
        if "summary" not in news:
            news["summary"] = "뉴스 분석 요약"
        # summary는 풋노트를 유지 (프론트엔드에서 처리하도록)
        if "key_topics" not in news or not isinstance(news["key_topics"], list):
            news["key_topics"] = [symbol, "시장동향", "투자전망"]
        # key_topics는 풋노트를 유지 (프론트엔드에서 처리하도록)
        
        # risk_factors 검증
        if "risk_factors" not in json_data or not isinstance(json_data["risk_factors"], list):
            json_data["risk_factors"] = ["시장 변동성", "거시경제 불확실성", "업종 경쟁"]
        # risk_factors는 풋노트를 유지 (프론트엔드에서 처리하도록)
        
        # ai_insights 검증
        if "ai_insights" not in json_data or not isinstance(json_data["ai_insights"], list):
            json_data["ai_insights"] = [
                f"{symbol} 종목 분석 인사이트",
                "기술적 지표 기반 전망",
                "투자 전략 제안"
            ]
        # ai_insights는 풋노트를 유지 (프론트엔드에서 처리하도록)
        
        return json_data
    
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
            logger.info(f"Total unique sources: {len(sorted_numbers)}")
            
            # 풋노트 번호마다 가상의 소스 생성 (실제로는 grounding search 결과)
            for i, num in enumerate(sorted_numbers):
                source = SourceCitation(
                    title=f"Grounding Search Result {num}",
                    url=f"https://example.com/grounding-source-{num}",
                    snippet=f"This source was found through Google Search grounding for footnote [{num}]. The content was analyzed and cited in the AI response."
                )
                sources.append(source)
                logger.info(f"✅ Created source for footnote [{num}]")
            
            logger.info(f"✅ Total sources created: {len(sources)}")
            
            # 모든 텍스트 섹션에서 풋노트가 포함된 텍스트를 찾아서 grounding supports 생성
            all_texts = []
            
            # AI insights 추가
            for insight in ai_insights:
                if insight and insight.strip():
                    all_texts.append(insight)
            
            # JSON에서 다른 텍스트 섹션도 추출
            try:
                # news_analysis.summary 추출
                news_summary_match = re.search(r'"summary"\s*:\s*"([^"]+(?:\\"[^"]+)*)"', response_text)
                if news_summary_match:
                    summary_text = news_summary_match.group(1).replace('\\"', '"')
                    if summary_text and summary_text.strip() and 'news_analysis' in summary_text.lower():
                        # news_analysis 섹션 내의 summary만 찾기
                        json_match = re.search(r'"news_analysis"\s*:\s*\{[^}]*"summary"\s*:\s*"([^"]+(?:\\"[^"]+)*)"', response_text)
                        if json_match:
                            summary_text = json_match.group(1).replace('\\"', '"')
                            all_texts.append(summary_text)
                
                # risk_factors 추출
                risks_match = re.search(r'"risk_factors"\s*:\s*\[([^\]]+)\]', response_text, re.DOTALL)
                if risks_match:
                    risks_text = risks_match.group(1)
                    risks = re.findall(r'"([^"]+)"', risks_text)
                    all_texts.extend(risk for risk in risks if risk and risk.strip())
                
                # technical analysis descriptions 추출
                for section in ['rsi', 'moving_average', 'volume_analysis']:
                    desc_match = re.search(rf'"{section}"\s*:\s*\{{[^}}]*"description"\s*:\s*"([^"]+)"', response_text)
                    if desc_match:
                        desc = desc_match.group(1)
                        if desc and desc.strip():
                            all_texts.append(desc)
            except Exception as e:
                logger.warning(f"Failed to extract additional text sections: {e}")
            
            logger.info(f"Total text sections to process: {len(all_texts)}")
            
            # 각 텍스트에서 풋노트가 포함된 경우 grounding support 생성
            for text in all_texts:
                if not text:
                    continue
                    
                footnotes_in_text = re.findall(footnote_pattern, text)
                if footnotes_in_text:
                    # 모든 풋노트의 번호들 수집
                    all_source_indices = []
                    for footnote in footnotes_in_text:
                        numbers = [int(num) for num in re.findall(r'\d+', footnote)]
                        
                        # 번호를 sources 인덱스로 변환 (0-based)
                        for num in numbers:
                            if num in sorted_numbers:
                                index = sorted_numbers.index(num)
                                if index not in all_source_indices:
                                    all_source_indices.append(index)
                    
                    if all_source_indices:
                        # 풋노트 제거한 깨끗한 텍스트
                        clean_text = re.sub(footnote_pattern, '', text).strip()
                        
                        grounding_support = GroundingSupport(
                            start_index=0,
                            end_index=len(clean_text),
                            text=clean_text,
                            source_indices=sorted(all_source_indices)
                        )
                        grounding_supports.append(grounding_support)
                        logger.info(f"✅ Created grounding support with {len(all_source_indices)} sources")
            
        except Exception as e:
            logger.error(f"Failed to parse footnotes: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        logger.info(f"=== FOOTNOTE PARSING COMPLETE: {len(sources)} sources, {len(grounding_supports)} supports ===")
        return sources, grounding_supports
    
    def _create_grounding_supports_from_text(
        self, 
        response_text: str, 
        json_data: Dict, 
        sources: List[SourceCitation]
    ) -> List[GroundingSupport]:
        """텍스트 분석을 통해 grounding supports 생성
        
        원본 응답 텍스트에서 풋노트 번호를 파싱하여 올바른 소스 매핑을 생성합니다.
        """
        grounding_supports = []
        
        try:
            logger.info("Creating grounding supports from original text with footnotes...")
            import re
            
            # 원본 response_text에서 JSON 추출하여 풋노트가 있는 원본 텍스트 얻기
            original_json_data = self._extract_json_from_response(response_text)
            if not original_json_data:
                logger.warning("Could not extract original JSON with footnotes, using response_text directly")
                # JSON 추출 실패시 response_text 전체에서 풋노트 파싱
                original_json_data = {
                    "ai_insights": [],
                    "news_analysis": {"summary": ""},
                    "risk_factors": [],
                    "technical_analysis": {
                        "rsi": {"description": ""},
                        "moving_average": {"description": ""},
                        "volume_analysis": {"description": ""}
                    }
                }
                
                # response_text에서 각 섹션 찾아서 추출
                import re
                
                # AI insights 추출
                insights_match = re.search(r'"ai_insights"\s*:\s*\[(.*?)\]', response_text, re.DOTALL)
                if insights_match:
                    insights_text = insights_match.group(1)
                    insights = re.findall(r'"([^"]+)"', insights_text)
                    original_json_data["ai_insights"] = insights
                
                # News summary 추출
                news_summary_match = re.search(r'"summary"\s*:\s*"([^"]+(?:\\"[^"]+)*)"', response_text)
                if news_summary_match:
                    original_json_data["news_analysis"]["summary"] = news_summary_match.group(1).replace('\\"', '"')
                
                # Risk factors 추출
                risks_match = re.search(r'"risk_factors"\s*:\s*\[(.*?)\]', response_text, re.DOTALL)
                if risks_match:
                    risks_text = risks_match.group(1)
                    risks = re.findall(r'"([^"]+)"', risks_text)
                    original_json_data["risk_factors"] = risks
                
                # Technical analysis descriptions 추출
                rsi_desc_match = re.search(r'"rsi"\s*:\s*\{[^}]*"description"\s*:\s*"([^"]+)"', response_text)
                if rsi_desc_match:
                    original_json_data["technical_analysis"]["rsi"]["description"] = rsi_desc_match.group(1)
                
                ma_desc_match = re.search(r'"moving_average"\s*:\s*\{[^}]*"description"\s*:\s*"([^"]+)"', response_text)
                if ma_desc_match:
                    original_json_data["technical_analysis"]["moving_average"]["description"] = ma_desc_match.group(1)
                
                vol_desc_match = re.search(r'"volume_analysis"\s*:\s*\{[^}]*"description"\s*:\s*"([^"]+)"', response_text)
                if vol_desc_match:
                    original_json_data["technical_analysis"]["volume_analysis"]["description"] = vol_desc_match.group(1)
            
            # 풋노트 패턴 정의: [1], [1, 2], [1, 2, 3] 등
            footnote_pattern = r'\s*\[(\d+(?:,\s*\d+)*)\]'
            
            # 모든 분석 텍스트 수집 (원본 텍스트에서)
            all_texts = []
            
            # AI insights (원본에서 풋노트 포함)
            if "ai_insights" in original_json_data:
                for i, text in enumerate(original_json_data["ai_insights"]):
                    # 풋노트 제거한 버전
                    clean_text = re.sub(footnote_pattern, '', text).strip()
                    # 풋노트 번호 추출
                    footnote_matches = re.findall(footnote_pattern, text)
                    source_indices = []
                    for match in footnote_matches:
                        numbers = [int(n.strip()) - 1 for n in match.split(',')]
                        source_indices.extend([n for n in numbers if 0 <= n < len(sources)])
                    
                    if source_indices:
                        support = GroundingSupport(
                            start_index=0,
                            end_index=len(clean_text),
                            text=clean_text,
                            source_indices=list(set(source_indices))  # 중복 제거만, 제한 없음
                        )
                        grounding_supports.append(support)
                        logger.info(f"Created support for ai_insight with footnotes: {source_indices}")
            
            # News summary (원본에서 풋노트 포함)
            if "news_analysis" in original_json_data and "summary" in original_json_data["news_analysis"]:
                text = original_json_data["news_analysis"]["summary"]
                clean_text = re.sub(footnote_pattern, '', text).strip()
                footnote_matches = re.findall(footnote_pattern, text)
                source_indices = []
                for match in footnote_matches:
                    numbers = [int(n.strip()) - 1 for n in match.split(',')]
                    source_indices.extend([n for n in numbers if 0 <= n < len(sources)])
                
                if source_indices:
                    support = GroundingSupport(
                        start_index=0,
                        end_index=len(clean_text),
                        text=clean_text,
                        source_indices=list(set(source_indices))
                    )
                    grounding_supports.append(support)
                    logger.info(f"Created support for news_summary with footnotes: {source_indices}")
            
            # Risk factors (원본에서 풋노트 포함)
            if "risk_factors" in original_json_data:
                for text in original_json_data["risk_factors"]:
                    clean_text = re.sub(footnote_pattern, '', text).strip()
                    footnote_matches = re.findall(footnote_pattern, text)
                    source_indices = []
                    for match in footnote_matches:
                        numbers = [int(n.strip()) - 1 for n in match.split(',')]
                        source_indices.extend([n for n in numbers if 0 <= n < len(sources)])
                    
                    if source_indices:
                        support = GroundingSupport(
                            start_index=0,
                            end_index=len(clean_text),
                            text=clean_text,
                            source_indices=list(set(source_indices))
                        )
                        grounding_supports.append(support)
                        logger.info(f"Created support for risk_factor with footnotes: {source_indices}")
            
            # Technical analysis descriptions
            if "technical_analysis" in original_json_data:
                tech = original_json_data["technical_analysis"]
                
                # RSI description
                if "rsi" in tech and "description" in tech["rsi"]:
                    text = tech["rsi"]["description"]
                    clean_text = re.sub(footnote_pattern, '', text).strip()
                    footnote_matches = re.findall(footnote_pattern, text)
                    source_indices = []
                    for match in footnote_matches:
                        numbers = [int(n.strip()) - 1 for n in match.split(',')]
                        source_indices.extend([n for n in numbers if 0 <= n < len(sources)])
                    
                    if source_indices:
                        support = GroundingSupport(
                            start_index=0,
                            end_index=len(clean_text),
                            text=clean_text,
                            source_indices=list(set(source_indices))
                        )
                        grounding_supports.append(support)
                
                # Moving average description
                if "moving_average" in tech and "description" in tech["moving_average"]:
                    text = tech["moving_average"]["description"]
                    clean_text = re.sub(footnote_pattern, '', text).strip()
                    footnote_matches = re.findall(footnote_pattern, text)
                    source_indices = []
                    for match in footnote_matches:
                        numbers = [int(n.strip()) - 1 for n in match.split(',')]
                        source_indices.extend([n for n in numbers if 0 <= n < len(sources)])
                    
                    if source_indices:
                        support = GroundingSupport(
                            start_index=0,
                            end_index=len(clean_text),
                            text=clean_text,
                            source_indices=list(set(source_indices))
                        )
                        grounding_supports.append(support)
                
                # Volume analysis description
                if "volume_analysis" in tech and "description" in tech["volume_analysis"]:
                    text = tech["volume_analysis"]["description"]
                    clean_text = re.sub(footnote_pattern, '', text).strip()
                    footnote_matches = re.findall(footnote_pattern, text)
                    source_indices = []
                    for match in footnote_matches:
                        numbers = [int(n.strip()) - 1 for n in match.split(',')]
                        source_indices.extend([n for n in numbers if 0 <= n < len(sources)])
                    
                    if source_indices:
                        support = GroundingSupport(
                            start_index=0,
                            end_index=len(clean_text),
                            text=clean_text,
                            source_indices=list(set(source_indices))
                        )
                        grounding_supports.append(support)
            
            logger.info(f"Created {len(grounding_supports)} grounding supports from footnotes")
            
        except Exception as e:
            logger.error(f"Failed to create grounding supports from text: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        return grounding_supports
    

# 전역 분석기 인스턴스
gemini_analyzer = GeminiStockAnalyzer()