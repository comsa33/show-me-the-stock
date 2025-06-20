import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


class GeminiStockAnalyzer:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            st.error("Gemini API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
            self.client = None
            return

        self.client = genai.Client(api_key=api_key)

        # 구글 검색 도구 설정
        self.grounding_tool = types.Tool(google_search=types.GoogleSearch())

        self.grounding_config = types.GenerateContentConfig(tools=[self.grounding_tool])

        # 캐시 저장소 (세션 상태 사용)
        if "ai_cache" not in st.session_state:
            st.session_state.ai_cache = {}

    def _get_cache_key(
        self, data_hash: str, analysis_type: str, additional_info: str = ""
    ) -> str:
        """캐시 키 생성"""
        combined = f"{data_hash}_{analysis_type}_{additional_info}"
        return hashlib.md5(combined.encode()).hexdigest()

    def _get_data_hash(
        self, stock_data: pd.DataFrame, stock_name: str, market: str
    ) -> str:
        """주식 데이터의 해시 생성 (최근 데이터 기준)"""
        recent_data = stock_data.tail(5)  # 최근 5일 데이터만 사용
        data_str = f"{stock_name}_{market}_{recent_data.to_string()}"
        return hashlib.md5(data_str.encode()).hexdigest()

    def _is_cache_valid(self, cache_entry: dict, ttl_minutes: int = 10) -> bool:
        """캐시 유효성 확인"""
        if "timestamp" not in cache_entry:
            return False

        cache_time = datetime.fromisoformat(cache_entry["timestamp"])
        return datetime.now() - cache_time < timedelta(minutes=ttl_minutes)

    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """캐시에서 결과 가져오기"""
        if cache_key in st.session_state.ai_cache:
            cache_entry = st.session_state.ai_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                return cache_entry["result"]
        return None

    def _save_to_cache(self, cache_key: str, result: str):
        """결과를 캐시에 저장"""
        st.session_state.ai_cache[cache_key] = {
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }

    def analyze_stock_data(
        self, stock_data: pd.DataFrame, stock_name: str, market: str
    ) -> str:
        if not self.client:
            return "AI 분석기가 초기화되지 않았습니다."

        # 캐시 확인
        data_hash = self._get_data_hash(stock_data, stock_name, market)
        cache_key = self._get_cache_key(data_hash, "basic_analysis")

        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return f"📋 (캐시됨) {cached_result}"

        try:
            # 주식 데이터 요약 생성
            current_price = stock_data["Close"].iloc[-1]
            prev_price = (
                stock_data["Close"].iloc[-2] if len(stock_data) > 1 else current_price
            )
            price_change = ((current_price - prev_price) / prev_price) * 100

            # 최근 30일 데이터 분석
            recent_data = stock_data.tail(30)
            high_30d = recent_data["High"].max()
            low_30d = recent_data["Low"].min()
            avg_volume = recent_data["Volume"].mean()

            # 변동성 계산
            volatility = stock_data["Close"].pct_change().std() * 100

            prompt = f"""
            주식 분석 요청:
            
            주식명: {stock_name}
            시장: {'한국 (KOSPI)' if market == 'KR' else '미국 (NASDAQ)'}
            현재가: {current_price:.2f}
            전일 대비 변동률: {price_change:.2f}%
            최근 30일 최고가: {high_30d:.2f}
            최근 30일 최저가: {low_30d:.2f}
            평균 거래량: {avg_volume:,.0f}
            변동성: {volatility:.2f}%
            
            위 데이터를 바탕으로 다음 항목들에 대해 간결하고 명확한 분석을 제공해주세요:
            
            1. 현재 주가 상황 요약
            2. 기술적 분석 (추세, 지지/저항선 등)
            3. 위험 요소 및 주의사항
            4. 투자 관점에서의 간단한 의견
            
            ⚠️ 주의: 이는 투자 조언이 아닌 정보 제공 목적임을 명시해주세요.
            답변은 한국어로, 500자 이내로 작성해주세요.
            """

            response = self.client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            result = response.text if response.text else "AI 응답을 받지 못했습니다."

            # 결과를 캐시에 저장
            self._save_to_cache(cache_key, result)
            return result

        except Exception as e:
            return f"AI 분석 중 오류가 발생했습니다: {str(e)}"

    def analyze_with_real_time_info(
        self, stock_data: pd.DataFrame, stock_name: str, market: str
    ) -> str:
        """실시간 정보를 활용한 종합 분석"""
        if not self.client:
            return "AI 분석기가 초기화되지 않았습니다."

        # 캐시 확인 (실시간 분석은 더 짧은 TTL 사용)
        data_hash = self._get_data_hash(stock_data, stock_name, market)
        cache_key = self._get_cache_key(data_hash, "realtime_analysis")

        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return f"🔄 (최근 분석) {cached_result}"

        try:
            # 주식 데이터 요약
            current_price = stock_data["Close"].iloc[-1]
            prev_price = (
                stock_data["Close"].iloc[-2] if len(stock_data) > 1 else current_price
            )
            price_change = ((current_price - prev_price) / prev_price) * 100

            # 최근 30일 데이터 분석
            recent_data = stock_data.tail(30)
            high_30d = recent_data["High"].max()
            low_30d = recent_data["Low"].min()
            avg_volume = recent_data["Volume"].mean()

            market_name = "한국" if market == "KR" else "미국"

            prompt = f"""
            {stock_name} ({market_name} 시장) 주식에 대한 종합 분석을 요청합니다.
            
            📊 현재 주가 데이터:
            - 현재가: {current_price:.2f}
            - 전일 대비 변동률: {price_change:.2f}%
            - 최근 30일 최고가: {high_30d:.2f}
            - 최근 30일 최저가: {low_30d:.2f}
            - 평균 거래량: {avg_volume:,.0f}
            
            위 정보와 함께 다음 실시간 정보를 검색하여 종합 분석해주세요:
            
            1. {stock_name} 최신 뉴스 및 공시사항
            2. {market_name} 시장 전반적 동향
            3. 관련 업계 동향
            4. 최근 금리 동향이 이 주식에 미치는 영향
            
            다음 관점에서 종합 분석해주세요:
            1. 현재 주가 상황과 최신 뉴스의 연관성
            2. 시장 환경이 이 주식에 미치는 영향
            3. 단기/중기 전망
            4. 주의해야 할 리스크 요소
            
            ⚠️ 이는 투자 조언이 아닌 정보 제공 목적입니다.
            답변은 한국어로, 700자 이내로 작성해주세요.
            """

            # Google 검색 기능을 포함한 API 호출
            response = self.client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt, config=self.grounding_config
            )

            result = (
                response.text
                if response.text
                else "실시간 분석 결과를 받지 못했습니다."
            )

            # 결과를 캐시에 저장 (5분 TTL)
            self._save_to_cache(cache_key, result)
            return result

        except Exception as e:
            return f"실시간 정보 분석 중 오류가 발생했습니다: {str(e)}"

    def compare_stocks(
        self, stock_data_dict: Dict[str, pd.DataFrame], market: str
    ) -> str:
        if not self.client:
            return "AI 분석기가 초기화되지 않았습니다."

        # 캐시 확인
        stocks_hash = hashlib.md5(
            str(sorted(stock_data_dict.keys())).encode()
        ).hexdigest()
        cache_key = self._get_cache_key(stocks_hash, "compare_stocks", market)

        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return f"📋 (캐시됨) {cached_result}"

        try:
            comparison_info = []

            for stock_name, data in stock_data_dict.items():
                current_price = data["Close"].iloc[-1]
                prev_price = data["Close"].iloc[-2] if len(data) > 1 else current_price
                price_change = ((current_price - prev_price) / prev_price) * 100
                volatility = data["Close"].pct_change().std() * 100

                comparison_info.append(
                    f"""
                {stock_name}:
                - 현재가: {current_price:.2f}
                - 변동률: {price_change:.2f}%
                - 변동성: {volatility:.2f}%
                """
                )

            prompt = f"""
            다음 주식들의 비교 분석을 요청합니다:
            
            시장: {'한국 (KOSPI)' if market == 'KR' else '미국 (NASDAQ)'}
            
            {''.join(comparison_info)}
            
            위 주식들을 비교하여 다음을 분석해주세요:
            1. 각 주식의 상대적 성과
            2. 위험도 비교
            3. 포트폴리오 관점에서의 다양성
            4. 투자 시 고려사항
            
            ⚠️ 주의: 이는 투자 조언이 아닌 정보 제공 목적임을 명시해주세요.
            답변은 한국어로, 600자 이내로 작성해주세요.
            """

            response = self.client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
            result = response.text if response.text else "AI 응답을 받지 못했습니다."

            # 결과를 캐시에 저장
            self._save_to_cache(cache_key, result)
            return result

        except Exception as e:
            return f"AI 비교 분석 중 오류가 발생했습니다: {str(e)}"

    def generate_market_insight(self, market: str, top_stocks: List[str]) -> str:
        if not self.client:
            return "AI 분석기가 초기화되지 않았습니다."

        try:
            market_name = "한국 (KOSPI)" if market == "KR" else "미국 (NASDAQ)"
            stocks_list = ", ".join(top_stocks)

            prompt = f"""
            {market_name} 시장에 대한 일반적인 인사이트를 제공해주세요.
            
            주요 관심 종목: {stocks_list}
            
            다음 항목들에 대해 간단히 설명해주세요:
            1. 현재 시장 상황 개관
            2. 주요 섹터 동향
            3. 투자자들이 주목해야 할 포인트
            4. 일반적인 투자 시 주의사항
            
            ⚠️ 주의: 이는 일반적인 정보 제공 목적이며 개별 투자 조언이 아닙니다.
            답변은 한국어로, 400자 이내로 작성해주세요.
            """

            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp", contents=prompt
            )
            return response.text if response.text else "AI 응답을 받지 못했습니다."

        except Exception as e:
            return f"시장 인사이트 생성 중 오류가 발생했습니다: {str(e)}"

    def get_technical_analysis(self, stock_data: pd.DataFrame, stock_name: str) -> str:
        if not self.client:
            return "AI 분석기가 초기화되지 않았습니다."

        try:
            # 기술적 지표 계산
            data = stock_data.copy()
            data["MA5"] = data["Close"].rolling(window=5).mean()
            data["MA20"] = data["Close"].rolling(window=20).mean()

            # RSI 계산
            delta = data["Close"].diff()
            gain = delta.where(delta > 0, 0).fillna(0)
            loss = (-delta.where(delta < 0, 0)).fillna(0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            data["RSI"] = 100 - (100 / (1 + rs))

            current_price = data["Close"].iloc[-1]
            ma5 = data["MA5"].iloc[-1]
            ma20 = data["MA20"].iloc[-1]
            rsi = data["RSI"].iloc[-1]

            prompt = f"""
            {stock_name}의 기술적 분석을 요청합니다:
            
            현재가: {current_price:.2f}
            5일 이동평균: {ma5:.2f}
            20일 이동평균: {ma20:.2f}
            RSI: {rsi:.2f}
            
            위 기술적 지표들을 바탕으로 다음을 분석해주세요:
            1. 현재 추세 방향 (상승/하락/횡보)
            2. 이동평균선 분석 (골든크로스/데드크로스 등)
            3. RSI 기반 과매수/과매도 상태
            4. 단기 전망
            
            답변은 한국어로, 300자 이내로 간결하게 작성해주세요.
            ⚠️ 이는 참고용 정보이며 투자 조언이 아닙니다.
            """

            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp", contents=prompt
            )
            return response.text if response.text else "AI 응답을 받지 못했습니다."

        except Exception as e:
            return f"기술적 분석 중 오류가 발생했습니다: {str(e)}"
