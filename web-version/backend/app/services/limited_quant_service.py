"""
제한된 데이터로 구현하는 퀀트 투자 서비스
pykrx와 yfinance에서 실제 수집 가능한 데이터만 사용
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel

from app.data.stock_data import StockDataFetcher
from app.services.real_financial_data import real_financial_service

logger = logging.getLogger(__name__)


class LimitedQuantIndicator(BaseModel):
    """제한된 실제 데이터 기반 퀀트 지표"""
    symbol: str
    name: str
    market: str
    # 실제 수집 가능한 지표들
    per: float
    pbr: float
    eps: float  # 실제 데이터
    bps: float  # 실제 데이터
    current_price: float  # 실제 데이터
    market_cap: float  # 실제 데이터
    # 계산 가능한 지표들
    estimated_roe: float  # EPS/BPS로 추정
    momentum_3m: float  # 실제 주가 데이터 기반
    volatility: float  # 실제 주가 데이터 기반
    # 퀀트 점수 (제한된 지표 기반)
    limited_quant_score: float
    recommendation: str
    data_completeness: str  # "FULL" (미국) or "LIMITED" (한국)


class LimitedQuantService:
    """제한된 실제 데이터 기반 퀀트 서비스"""
    
    def __init__(self):
        self.stock_fetcher = StockDataFetcher()
    
    async def get_limited_quant_indicators(
        self, 
        market: str = "KR", 
        limit: int = 50
    ) -> List[LimitedQuantIndicator]:
        """실제 수집 가능한 데이터로 퀀트 지표 계산"""
        
        try:
            # 종목 리스트 가져오기
            if market.upper() == "KR":
                stocks_data = self.stock_fetcher.get_all_kr_stocks()
            else:
                stocks_data = self.stock_fetcher.get_all_us_stocks()
            
            stocks_data = stocks_data[:limit]
            indicators = []
            
            for stock in stocks_data:
                try:
                    indicator = await self._calculate_limited_indicators(
                        stock['symbol'], 
                        stock['name'], 
                        market
                    )
                    if indicator:
                        indicators.append(indicator)
                except Exception as e:
                    logger.warning(f"종목 {stock['symbol']} 제한된 지표 계산 실패: {e}")
                    continue
            
            # 퀀트 점수 기준 정렬
            indicators.sort(key=lambda x: x.limited_quant_score, reverse=True)
            return indicators
            
        except Exception as e:
            logger.error(f"제한된 퀀트 지표 계산 실패: {e}")
            return []
    
    async def _calculate_limited_indicators(
        self, 
        symbol: str, 
        name: str, 
        market: str
    ) -> Optional[LimitedQuantIndicator]:
        """제한된 실제 데이터로 지표 계산"""
        
        try:
            # 실제 재무 데이터 가져오기
            financial_data = real_financial_service.get_financial_data(symbol, market)
            
            # 주가 데이터 가져오기 (기술적 지표용)
            price_data = self.stock_fetcher.get_stock_data(symbol, "1y", market)
            if price_data is None or price_data.empty:
                momentum_3m = 0.0
                volatility = 20.0
            else:
                momentum_3m = self._calculate_momentum(price_data, 60)
                volatility = self._calculate_volatility(price_data)
            
            # 실제 수집된 데이터
            per = financial_data['per']
            pbr = financial_data['pbr']
            eps = financial_data['eps']
            bps = financial_data['bps']
            current_price = financial_data['current_price']
            market_cap = financial_data['market_cap']
            
            # ROE 추정 (EPS/BPS * 100)
            estimated_roe = (eps / bps * 100) if bps > 0 else 0
            
            # 데이터 완성도 체크
            if market.upper() == "US":
                data_completeness = "FULL"  # yfinance는 완전한 데이터
            else:
                data_completeness = "LIMITED"  # pykrx는 제한적 데이터
            
            # 제한된 퀀트 점수 계산
            limited_score = self._calculate_limited_quant_score(
                per, pbr, estimated_roe, momentum_3m, volatility, market_cap
            )
            
            # 추천 결정
            recommendation = self._get_limited_recommendation(limited_score, per, pbr, estimated_roe)
            
            return LimitedQuantIndicator(
                symbol=symbol,
                name=name,
                market=market,
                per=per,
                pbr=pbr,
                eps=eps,
                bps=bps,
                current_price=current_price,
                market_cap=market_cap,
                estimated_roe=round(estimated_roe, 2),
                momentum_3m=momentum_3m,
                volatility=volatility,
                limited_quant_score=limited_score,
                recommendation=recommendation,
                data_completeness=data_completeness
            )
            
        except Exception as e:
            logger.error(f"종목 {symbol} 제한된 지표 계산 실패: {e}")
            return None
    
    def _calculate_momentum(self, price_data: pd.DataFrame, period: int) -> float:
        """모멘텀 계산"""
        try:
            if len(price_data) < period:
                period = len(price_data) - 1
            
            if period <= 1:
                return 0.0
            
            current_price = float(price_data['Close'].iloc[-1])
            past_price = float(price_data['Close'].iloc[-period])
            
            momentum = ((current_price - past_price) / past_price) * 100
            return round(momentum, 2)
            
        except Exception:
            return 0.0
    
    def _calculate_volatility(self, price_data: pd.DataFrame) -> float:
        """변동성 계산"""
        try:
            returns = price_data['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100
            return round(volatility, 2)
            
        except Exception:
            return 20.0
    
    def _calculate_limited_quant_score(
        self, 
        per: float, 
        pbr: float, 
        estimated_roe: float, 
        momentum: float, 
        volatility: float, 
        market_cap: float
    ) -> float:
        """제한된 지표로 퀀트 점수 계산"""
        
        try:
            # 가치 지표 (낮을수록 좋음)
            per_score = max(0, 100 - (per / 50 * 100)) if per > 0 else 0
            pbr_score = max(0, 100 - (pbr / 5 * 100)) if pbr > 0 else 0
            
            # 수익성 지표 (높을수록 좋음)
            roe_score = min(100, estimated_roe * 3.33) if estimated_roe > 0 else 0
            
            # 모멘텀 지표
            momentum_score = min(100, max(0, 50 + momentum * 2))
            
            # 변동성 지표 (낮을수록 좋음)
            vol_score = max(0, 100 - (volatility / 50 * 100))
            
            # 가중 평균 (제한된 지표에 맞게 조정)
            final_score = (
                per_score * 0.25 +
                pbr_score * 0.25 +
                roe_score * 0.25 +
                momentum_score * 0.15 +
                vol_score * 0.1
            )
            
            return round(min(100, max(0, final_score)), 1)
            
        except Exception:
            return 50.0
    
    def _get_limited_recommendation(self, score: float, per: float, pbr: float, roe: float) -> str:
        """제한된 지표 기반 추천"""
        
        if score >= 70 and per < 25 and roe > 8:
            return "BUY"
        elif score >= 45:
            return "HOLD"
        else:
            return "SELL"


# 전역 서비스 인스턴스
limited_quant_service = LimitedQuantService()