import google.generativeai as genai
import pandas as pd
from typing import Dict, List, Optional
import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

class GeminiStockAnalyzer:
    def __init__(self):
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            st.error("Gemini API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
            return
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
    
    def analyze_stock_data(self, stock_data: pd.DataFrame, stock_name: str, market: str) -> str:
        try:
            # 주식 데이터 요약 생성
            current_price = stock_data['Close'].iloc[-1]
            prev_price = stock_data['Close'].iloc[-2] if len(stock_data) > 1 else current_price
            price_change = ((current_price - prev_price) / prev_price) * 100
            
            # 최근 30일 데이터 분석
            recent_data = stock_data.tail(30)
            high_30d = recent_data['High'].max()
            low_30d = recent_data['Low'].min()
            avg_volume = recent_data['Volume'].mean()
            
            # 변동성 계산
            volatility = stock_data['Close'].pct_change().std() * 100
            
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
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"AI 분석 중 오류가 발생했습니다: {str(e)}"
    
    def compare_stocks(self, stock_data_dict: Dict[str, pd.DataFrame], market: str) -> str:
        try:
            comparison_info = []
            
            for stock_name, data in stock_data_dict.items():
                current_price = data['Close'].iloc[-1]
                prev_price = data['Close'].iloc[-2] if len(data) > 1 else current_price
                price_change = ((current_price - prev_price) / prev_price) * 100
                volatility = data['Close'].pct_change().std() * 100
                
                comparison_info.append(f"""
                {stock_name}:
                - 현재가: {current_price:.2f}
                - 변동률: {price_change:.2f}%
                - 변동성: {volatility:.2f}%
                """)
            
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
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"AI 비교 분석 중 오류가 발생했습니다: {str(e)}"
    
    def generate_market_insight(self, market: str, top_stocks: List[str]) -> str:
        try:
            market_name = '한국 (KOSPI)' if market == 'KR' else '미국 (NASDAQ)'
            stocks_list = ', '.join(top_stocks)
            
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
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"시장 인사이트 생성 중 오류가 발생했습니다: {str(e)}"
    
    def get_technical_analysis(self, stock_data: pd.DataFrame, stock_name: str) -> str:
        try:
            # 기술적 지표 계산
            data = stock_data.copy()
            data['MA5'] = data['Close'].rolling(window=5).mean()
            data['MA20'] = data['Close'].rolling(window=20).mean()
            
            # RSI 계산
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).fillna(0)
            loss = (-delta.where(delta < 0, 0)).fillna(0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            current_price = data['Close'].iloc[-1]
            ma5 = data['MA5'].iloc[-1]
            ma20 = data['MA20'].iloc[-1]
            rsi = data['RSI'].iloc[-1]
            
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
            
            response = self.model.generate_content(prompt)
            return response.text
            
        except Exception as e:
            return f"기술적 분석 중 오류가 발생했습니다: {str(e)}"