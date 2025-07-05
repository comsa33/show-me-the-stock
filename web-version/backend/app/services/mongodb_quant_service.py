"""
MongoDB-based Quant Service
Calculates quant indicators using data from MongoDB
"""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel

from ..database.mongodb_client import get_mongodb_client
from ..core.cache import cached

logger = logging.getLogger(__name__)


class MongoDBQuantIndicator(BaseModel):
    """MongoDB 기반 퀀트 지표"""
    symbol: str
    name: str
    market: str
    # 재무 지표
    per: Optional[float]
    pbr: Optional[float]
    eps: Optional[float]
    bps: Optional[float]
    roe: Optional[float]
    roa: Optional[float]
    dividend_yield: Optional[float]
    # 시장 데이터
    current_price: float
    market_cap: Optional[float]
    # 기술적 지표
    momentum_1m: float  # 1개월 모멘텀
    momentum_3m: float  # 3개월 모멘텀
    momentum_6m: float  # 6개월 모멘텀
    volatility: float   # 변동성
    rsi: float         # RSI
    # 거래량 지표
    volume_ratio: float  # 거래량 비율 (현재/평균)
    # 퀀트 점수
    quant_score: float
    value_score: float    # 가치 점수
    growth_score: float   # 성장 점수
    quality_score: float  # 품질 점수
    momentum_score: float # 모멘텀 점수
    recommendation: str


class MongoDBQuantService:
    """MongoDB 데이터 기반 퀀트 서비스"""
    
    def __init__(self):
        self.db = get_mongodb_client()
    
    @cached(ttl=1800, key_prefix="mongodb_quant_indicators")  # 30분 캐시
    async def get_quant_indicators(
        self, 
        market: str = "KR", 
        limit: int = 50,
        min_market_cap: Optional[float] = None
    ) -> List[MongoDBQuantIndicator]:
        """MongoDB에서 퀀트 지표 계산"""
        try:
            # 활성 종목 리스트 가져오기
            stocks = self.db.get_stock_list(market=market, is_active=True)
            
            indicators = []
            for stock in stocks:
                try:
                    indicator = await self._calculate_indicators(stock)
                    if indicator:
                        # 시가총액 필터
                        if min_market_cap and indicator.market_cap:
                            if indicator.market_cap < min_market_cap:
                                continue
                        indicators.append(indicator)
                except Exception as e:
                    logger.warning(f"Failed to calculate indicators for {stock['symbol']}: {e}")
                    continue
            
            # 퀀트 점수 기준 정렬
            indicators.sort(key=lambda x: x.quant_score, reverse=True)
            return indicators[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get quant indicators: {e}")
            return []
    
    async def _calculate_indicators(self, stock: Dict) -> Optional[MongoDBQuantIndicator]:
        """개별 종목의 지표 계산"""
        try:
            symbol = stock["symbol"]
            
            # 최신 가격 데이터
            latest_price = self.db.get_latest_price(symbol)
            if not latest_price:
                return None
            
            # 최신 재무 데이터
            financial = self.db.get_stock_financial(symbol)
            
            # 가격 히스토리 (기술적 지표용)
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            price_history = self.db.get_stock_price_history(
                symbol, start_date=start_date, end_date=end_date
            )
            
            if len(price_history) < 1:  # 최소 1일 데이터 요구
                return None
            
            # 가격 데이터를 DataFrame으로 변환
            df = pd.DataFrame(price_history)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # 기술적 지표 계산
            tech_indicators = self._calculate_technical_indicators(df)
            
            # 재무 지표 정리
            current_price = float(latest_price["close"])
            
            # 퀀트 점수 계산
            scores = self._calculate_quant_scores(
                financial=financial,
                tech_indicators=tech_indicators,
                current_price=current_price
            )
            
            # 추천 생성
            recommendation = self._generate_recommendation(scores["total"])
            
            return MongoDBQuantIndicator(
                symbol=symbol,
                name=stock["name"],
                market=stock["market"],
                # 재무 지표
                per=financial.get("per") if financial else None,
                pbr=financial.get("pbr") if financial else None,
                eps=financial.get("eps") if financial else None,
                bps=financial.get("bps") if financial else None,
                roe=financial.get("roe") if financial else None,
                roa=financial.get("roa") if financial else None,
                dividend_yield=financial.get("dividend_yield") if financial else None,
                # 시장 데이터
                current_price=current_price,
                market_cap=financial.get("market_cap") if financial else None,
                # 기술적 지표
                momentum_1m=tech_indicators["momentum_1m"],
                momentum_3m=tech_indicators["momentum_3m"],
                momentum_6m=tech_indicators["momentum_6m"],
                volatility=tech_indicators["volatility"],
                rsi=tech_indicators["rsi"],
                volume_ratio=tech_indicators["volume_ratio"],
                # 퀀트 점수
                quant_score=scores["total"],
                value_score=scores["value"],
                growth_score=scores["growth"],
                quality_score=scores["quality"],
                momentum_score=scores["momentum"],
                recommendation=recommendation
            )
            
        except Exception as e:
            logger.error(f"Failed to calculate indicators for {stock['symbol']}: {e}")
            return None
    
    def _calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """기술적 지표 계산"""
        try:
            # 현재 가격
            current_price = df.iloc[-1]['close']
            data_length = len(df)
            
            # 모멘텀 계산 (데이터가 있는 만큼만 계산)
            momentum_1m = 0.0
            momentum_3m = 0.0
            momentum_6m = 0.0
            
            # 1개월 모멘텀 (20일 또는 가능한 만큼)
            if data_length >= 2:
                days_1m = min(20, data_length - 1)
                price_1m_ago = df.iloc[-days_1m-1]['close']
                momentum_1m = (current_price - price_1m_ago) / price_1m_ago * 100
            
            # 3개월 모멘텀 (60일 또는 가능한 만큼)
            if data_length >= 2:
                days_3m = min(60, data_length - 1)
                price_3m_ago = df.iloc[-days_3m-1]['close']
                momentum_3m = (current_price - price_3m_ago) / price_3m_ago * 100
            
            # 6개월 모멘텀 (120일 또는 가능한 만큼)
            if data_length >= 2:
                days_6m = min(120, data_length - 1)
                price_6m_ago = df.iloc[-days_6m-1]['close']
                momentum_6m = (current_price - price_6m_ago) / price_6m_ago * 100
            
            # 변동성 (가능한 데이터로 계산)
            volatility = 20.0  # 기본값
            if data_length >= 2:
                returns = df['close'].pct_change().dropna()
                if len(returns) > 0:
                    # 최대 20일치 데이터 사용
                    volatility = returns.tail(min(20, len(returns))).std() * np.sqrt(252) * 100
                    if pd.isna(volatility) or volatility == 0:
                        volatility = 20.0
            
            # RSI 계산 (최소 14일 필요, 없으면 중립값)
            rsi = 50.0
            if data_length >= 14:
                rsi = self._calculate_rsi(df['close'], period=min(14, data_length-1))
            
            # 거래량 비율 (가능한 데이터로 계산)
            volume_ratio = 1.0
            if data_length >= 2:
                avg_days = min(20, data_length)
                avg_volume = df.tail(avg_days)['volume'].mean()
                current_volume = df.iloc[-1]['volume']
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
            
            return {
                "momentum_1m": momentum_1m,
                "momentum_3m": momentum_3m,
                "momentum_6m": momentum_6m,
                "volatility": volatility,
                "rsi": rsi,
                "volume_ratio": volume_ratio
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate technical indicators: {e}")
            return {
                "momentum_1m": 0.0,
                "momentum_3m": 0.0,
                "momentum_6m": 0.0,
                "volatility": 20.0,
                "rsi": 50.0,
                "volume_ratio": 1.0
            }
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """RSI 계산"""
        try:
            if len(prices) < period + 1:
                return 50.0  # 데이터 부족시 중립값
                
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            # Avoid division by zero
            loss = loss.replace(0, 0.00001)
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
        except Exception as e:
            logger.debug(f"RSI calculation failed: {e}")
            return 50.0
    
    def _calculate_quant_scores(
        self, 
        financial: Optional[Dict],
        tech_indicators: Dict[str, float],
        current_price: float
    ) -> Dict[str, float]:
        """퀀트 점수 계산"""
        
        # 가치 점수 (낮은 PER, PBR이 좋음)
        value_score = 50.0
        if financial:
            per = financial.get("per")
            pbr = financial.get("pbr")
            
            if per and 0 < per < 100:
                # PER이 낮을수록 높은 점수
                per_score = max(0, min(100, 100 - per * 2))
                value_score = per_score * 0.5
            
            if pbr and 0 < pbr < 10:
                # PBR이 낮을수록 높은 점수
                pbr_score = max(0, min(100, 100 - pbr * 10))
                value_score += pbr_score * 0.5
        
        # 성장 점수 (모멘텀 기반)
        growth_score = 50.0
        momentum_avg = (
            tech_indicators["momentum_1m"] * 0.5 +
            tech_indicators["momentum_3m"] * 0.3 +
            tech_indicators["momentum_6m"] * 0.2
        )
        if -50 < momentum_avg < 100:
            growth_score = min(100, max(0, 50 + momentum_avg))
        
        # 품질 점수 (ROE, 변동성 기반)
        quality_score = 50.0
        if financial:
            roe = financial.get("roe")
            if roe and 0 < roe < 50:
                # ROE가 높을수록 좋음 (15% 이상이면 좋음)
                quality_score = min(100, roe * 3.33)
        
        # 변동성이 낮을수록 품질 점수 증가
        volatility_penalty = min(30, tech_indicators["volatility"] / 2)
        quality_score = max(0, quality_score - volatility_penalty)
        
        # 모멘텀 점수 (RSI, 거래량 기반)
        momentum_score = 50.0
        
        # RSI 점수 (30-70 범위가 정상)
        rsi = tech_indicators["rsi"]
        if 30 <= rsi <= 70:
            momentum_score = 50 + (rsi - 50) * 0.5
        elif rsi < 30:
            momentum_score = 30 + rsi * 0.67  # 과매도
        else:
            momentum_score = 70 + (100 - rsi) * 0.33  # 과매수
        
        # 거래량 가중치
        volume_bonus = min(20, (tech_indicators["volume_ratio"] - 1) * 10)
        momentum_score = min(100, momentum_score + volume_bonus)
        
        # 종합 점수 계산
        total_score = (
            value_score * 0.3 +
            growth_score * 0.2 +
            quality_score * 0.3 +
            momentum_score * 0.2
        )
        
        return {
            "value": value_score,
            "growth": growth_score,
            "quality": quality_score,
            "momentum": momentum_score,
            "total": total_score
        }
    
    def _generate_recommendation(self, quant_score: float) -> str:
        """퀀트 점수 기반 추천"""
        if quant_score >= 80:
            return "STRONG_BUY"
        elif quant_score >= 65:
            return "BUY"
        elif quant_score >= 50:
            return "HOLD"
        elif quant_score >= 35:
            return "SELL"
        else:
            return "STRONG_SELL"
    
    async def get_market_summary(self, market: str = "KR") -> Dict:
        """시장 전체 퀀트 지표 요약"""
        try:
            indicators = await self.get_quant_indicators(market, limit=200)
            
            if not indicators:
                return {
                    "market": market,
                    "total_stocks": 0,
                    "avg_per": 0,
                    "avg_pbr": 0,
                    "avg_quant_score": 0,
                    "top_value_stocks": [],
                    "top_growth_stocks": [],
                    "top_quality_stocks": []
                }
            
            # 평균 계산
            valid_per = [i.per for i in indicators if i.per and i.per > 0]
            valid_pbr = [i.pbr for i in indicators if i.pbr and i.pbr > 0]
            
            # Top 종목 선정
            top_value = sorted(indicators, key=lambda x: x.value_score, reverse=True)[:5]
            top_growth = sorted(indicators, key=lambda x: x.growth_score, reverse=True)[:5]
            top_quality = sorted(indicators, key=lambda x: x.quality_score, reverse=True)[:5]
            
            return {
                "market": market,
                "total_stocks": len(indicators),
                "avg_per": sum(valid_per) / len(valid_per) if valid_per else 0,
                "avg_pbr": sum(valid_pbr) / len(valid_pbr) if valid_pbr else 0,
                "avg_quant_score": sum(i.quant_score for i in indicators) / len(indicators),
                "top_value_stocks": [
                    {"symbol": s.symbol, "name": s.name, "score": s.value_score}
                    for s in top_value
                ],
                "top_growth_stocks": [
                    {"symbol": s.symbol, "name": s.name, "score": s.growth_score}
                    for s in top_growth
                ],
                "top_quality_stocks": [
                    {"symbol": s.symbol, "name": s.name, "score": s.quality_score}
                    for s in top_quality
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get market summary: {e}")
            return {}


# Singleton instance
_mongodb_quant_service = None


def get_mongodb_quant_service() -> MongoDBQuantService:
    """Get MongoDB quant service singleton"""
    global _mongodb_quant_service
    if _mongodb_quant_service is None:
        _mongodb_quant_service = MongoDBQuantService()
    return _mongodb_quant_service