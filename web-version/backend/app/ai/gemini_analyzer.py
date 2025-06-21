import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


class GeminiStockAnalyzer:
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print(
                "Warning: Gemini API 키가 설정되지 않았습니다. .env 파일을 확인해주세요."
            )
            self.model = None
            return

        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-pro")
        except Exception as e:
            print(f"Gemini 모델 초기화 실패: {str(e)}")
            self.model = None

        # 캐시 저장소 (메모리 캐시 사용)
        self.ai_cache = {}

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
        cache_time = datetime.fromisoformat(cache_entry["timestamp"])
        return datetime.now() - cache_time < timedelta(minutes=ttl_minutes)

    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """캐시에서 결과 가져오기"""
        if cache_key in self.ai_cache:
            cache_entry = self.ai_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                return cache_entry["result"]
        return None

    def _save_to_cache(self, cache_key: str, result: str):
        """결과를 캐시에 저장"""
        self.ai_cache[cache_key] = {
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }

    def analyze_stock(
        self, stock_data: pd.DataFrame, stock_name: str, market: str
    ) -> str:
        """기본 주식 분석"""
        if self.model is None:
            return "AI 분석을 사용할 수 없습니다. API 키가 설정되지 않았습니다."

        # 캐시 확인
        data_hash = self._get_data_hash(stock_data, stock_name, market)
        cache_key = self._get_cache_key(data_hash, "basic_analysis")
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        try:
            # 최근 데이터 요약
            recent_data = stock_data.tail(10)
            current_price = recent_data["Close"].iloc[-1]
            price_change = recent_data["Close"].pct_change().iloc[-1] * 100
            volume = recent_data["Volume"].iloc[-1]

            prompt = f"""
다음 주식 정보를 분석해주세요:

주식명: {stock_name}
시장: {market}
현재가: {current_price:.2f}
전일 대비 변화율: {price_change:.2f}%
거래량: {volume:,}

최근 10일 종가 데이터:
{recent_data['Close'].tolist()}

이 주식에 대한 간단한 분석과 투자 의견을 한국어로 제공해주세요.
"""

            response = self.model.generate_content(prompt)
            result = response.text

            # 캐시에 저장
            self._save_to_cache(cache_key, result)
            return result

        except Exception as e:
            return f"분석 중 오류가 발생했습니다: {str(e)}"

    def analyze_technical_indicators(
        self, stock_data: pd.DataFrame, stock_name: str, market: str
    ) -> str:
        """기술적 지표 분석"""
        if self.model is None:
            return "AI 분석을 사용할 수 없습니다. API 키가 설정되지 않았습니다."

        # 캐시 확인
        data_hash = self._get_data_hash(stock_data, stock_name, market)
        cache_key = self._get_cache_key(data_hash, "technical_analysis")
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        try:
            # 간단한 기술적 지표 계산
            stock_data["MA20"] = stock_data["Close"].rolling(20).mean()
            stock_data["MA5"] = stock_data["Close"].rolling(5).mean()

            recent_data = stock_data.tail(10)
            current_price = recent_data["Close"].iloc[-1]
            ma20 = recent_data["MA20"].iloc[-1]
            ma5 = recent_data["MA5"].iloc[-1]

            prompt = f"""
다음 주식의 기술적 지표를 분석해주세요:

주식명: {stock_name}
현재가: {current_price:.2f}
20일 이동평균: {ma20:.2f}
5일 이동평균: {ma5:.2f}

현재가와 이동평균선들의 관계를 바탕으로 기술적 분석과 단기 전망을 한국어로 제공해주세요.
"""

            response = self.model.generate_content(prompt)
            result = response.text

            # 캐시에 저장
            self._save_to_cache(cache_key, result)
            return result

        except Exception as e:
            return f"기술적 분석 중 오류가 발생했습니다: {str(e)}"

    def analyze_market_insights(
        self, stock_data: pd.DataFrame, stock_name: str, market: str
    ) -> str:
        """시장 인사이트 분석"""
        if self.model is None:
            return "AI 분석을 사용할 수 없습니다. API 키가 설정되지 않았습니다."

        # 캐시 확인
        data_hash = self._get_data_hash(stock_data, stock_name, market)
        cache_key = self._get_cache_key(data_hash, "market_insights")
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result

        try:
            # 시장 동향 분석을 위한 데이터 준비
            monthly_data = stock_data.tail(30)
            monthly_return = (
                monthly_data["Close"].iloc[-1] / monthly_data["Close"].iloc[0] - 1
            ) * 100
            volatility = monthly_data["Close"].pct_change().std() * 100

            prompt = f"""
다음 주식의 시장 인사이트를 분석해주세요:

주식명: {stock_name}
시장: {market}
최근 30일 수익률: {monthly_return:.2f}%
변동성: {volatility:.2f}%

이 주식이 속한 시장의 전반적인 상황과 산업 동향을 고려한 장기 투자 관점에서의 분석을 한국어로 제공해주세요.
"""

            response = self.model.generate_content(prompt)
            result = response.text

            # 캐시에 저장
            self._save_to_cache(cache_key, result)
            return result

        except Exception as e:
            return f"시장 인사이트 분석 중 오류가 발생했습니다: {str(e)}"

    def analyze_market_overview(
        self, market_data: Dict[str, pd.DataFrame], market: str
    ) -> str:
        """시장 전체 개요 분석"""
        if self.model is None:
            return "AI 분석을 사용할 수 없습니다. API 키가 설정되지 않았습니다."

        try:
            # 주요 주식들의 성과 요약
            summary = []
            for symbol, data in market_data.items():
                if not data.empty:
                    current_price = data["Close"].iloc[-1]
                    price_change = (
                        data["Close"].iloc[-1] / data["Close"].iloc[0] - 1
                    ) * 100
                    summary.append(f"{symbol}: {price_change:.2f}%")

            prompt = f"""
다음 {market} 시장 주요 주식들의 성과를 분석해주세요:

{chr(10).join(summary)}

이 데이터를 바탕으로 시장 전반의 동향과 투자자들이 주목해야 할 포인트를 한국어로 제공해주세요.
"""

            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            return f"시장 개요 분석 중 오류가 발생했습니다: {str(e)}"
