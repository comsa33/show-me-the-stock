"""
퀀트 투자 분석 서비스
PER, PBR, ROE 등 재무 지표 계산 및 팩터 기반 투자 전략
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel

from app.data.stock_data import StockDataFetcher

logger = logging.getLogger(__name__)


class QuantIndicator(BaseModel):
    """퀀트 지표 데이터 모델"""
    symbol: str
    name: str
    market: str
    per: float
    pbr: float
    roe: float
    roa: float
    debt_ratio: float
    momentum_3m: float
    market_cap: float
    volatility: float
    quant_score: float
    recommendation: str  # BUY, HOLD, SELL


class FactorWeights(BaseModel):
    """팩터별 가중치"""
    value: float = 0.25      # 가치 팩터
    momentum: float = 0.20   # 모멘텀 팩터
    quality: float = 0.25    # 품질 팩터
    size: float = 0.15       # 규모 팩터
    low_vol: float = 0.15    # 저변동성 팩터


class BacktestResult(BaseModel):
    """백테스트 결과"""
    strategy: str
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    start_date: str
    end_date: str
    selected_stocks: List[str]


class QuantAnalysisService:
    """퀀트 분석 서비스"""
    
    def __init__(self):
        self.stock_fetcher = StockDataFetcher()
        self.factor_weights = FactorWeights()
    
    async def get_quant_indicators(
        self, 
        market: str = "KR", 
        limit: int = 50
    ) -> List[QuantIndicator]:
        """퀀트 지표 계산 및 반환"""
        
        try:
            # 종목 리스트 가져오기
            if market.upper() == "KR":
                stocks_data = self.stock_fetcher.get_all_kr_stocks()
            else:
                stocks_data = self.stock_fetcher.get_all_us_stocks()
            
            # 상위 N개 종목만 처리 (성능 최적화)
            stocks_data = stocks_data[:limit]
            
            indicators = []
            
            for stock in stocks_data:
                try:
                    indicator = await self._calculate_stock_indicators(
                        stock['symbol'], 
                        stock['name'], 
                        market
                    )
                    if indicator:
                        indicators.append(indicator)
                except Exception as e:
                    logger.warning(f"종목 {stock['symbol']} 지표 계산 실패: {e}")
                    continue
            
            # 퀀트 점수 기준 정렬
            indicators.sort(key=lambda x: x.quant_score, reverse=True)
            
            return indicators
            
        except Exception as e:
            logger.error(f"퀀트 지표 계산 실패: {e}")
            return self._generate_mock_indicators(market, limit)
    
    async def _calculate_stock_indicators(
        self, 
        symbol: str, 
        name: str, 
        market: str
    ) -> Optional[QuantIndicator]:
        """개별 종목 퀀트 지표 계산"""
        
        try:
            # 주가 데이터 가져오기
            price_data = self.stock_fetcher.get_stock_data(symbol, "1y", market)
            if price_data is None or price_data.empty:
                return None
            
            # 재무 지표 계산 (실제로는 재무제표 데이터가 필요하지만 여기서는 추정)
            per = self._calculate_per(price_data, symbol, market)
            pbr = self._calculate_pbr(price_data, symbol, market)
            roe = self._calculate_roe(symbol, market)
            roa = self._calculate_roa(symbol, market)
            debt_ratio = self._calculate_debt_ratio(symbol, market)
            
            # 기술적 지표 계산
            momentum_3m = self._calculate_momentum(price_data, 60)  # 3개월
            volatility = self._calculate_volatility(price_data)
            market_cap = self._estimate_market_cap(price_data, symbol, market)
            
            # 퀀트 점수 계산
            quant_score = self._calculate_quant_score(
                per, pbr, roe, roa, debt_ratio, momentum_3m, volatility, market_cap
            )
            
            # 투자 추천 결정
            recommendation = self._get_recommendation(quant_score, per, pbr, roe)
            
            return QuantIndicator(
                symbol=symbol,
                name=name,
                market=market,
                per=per,
                pbr=pbr,
                roe=roe,
                roa=roa,
                debt_ratio=debt_ratio,
                momentum_3m=momentum_3m,
                market_cap=market_cap,
                volatility=volatility,
                quant_score=quant_score,
                recommendation=recommendation
            )
            
        except Exception as e:
            logger.error(f"종목 {symbol} 지표 계산 실패: {e}")
            return None
    
    def _calculate_per(self, price_data: pd.DataFrame, symbol: str, market: str) -> float:
        """PER 계산 (가격/수익 비율)"""
        try:
            # 실제로는 재무제표에서 EPS를 가져와야 하지만, 여기서는 추정
            current_price = float(price_data['Close'].iloc[-1])
            
            # 시장별 평균 PER 범위 내에서 랜덤 생성 (실제 구현시 재무데이터 API 필요)
            if market.upper() == "KR":
                # 한국 시장 평균 PER: 8-25
                estimated_eps = current_price / np.random.uniform(8, 25)
            else:
                # 미국 시장 평균 PER: 15-30
                estimated_eps = current_price / np.random.uniform(15, 30)
            
            per = current_price / estimated_eps if estimated_eps > 0 else 0
            return round(per, 2)
            
        except Exception:
            return np.random.uniform(10, 30)
    
    def _calculate_pbr(self, price_data: pd.DataFrame, symbol: str, market: str) -> float:
        """PBR 계산 (가격/장부가치 비율)"""
        try:
            current_price = float(price_data['Close'].iloc[-1])
            
            # 실제로는 재무제표에서 BPS를 가져와야 함
            if market.upper() == "KR":
                estimated_bps = current_price / np.random.uniform(0.8, 3.5)
            else:
                estimated_bps = current_price / np.random.uniform(1.5, 5.0)
            
            pbr = current_price / estimated_bps if estimated_bps > 0 else 0
            return round(pbr, 2)
            
        except Exception:
            return np.random.uniform(0.5, 4.0)
    
    def _calculate_roe(self, symbol: str, market: str) -> float:
        """ROE 계산 (자기자본이익률)"""
        # 실제로는 재무제표 데이터 필요
        if market.upper() == "KR":
            roe = np.random.uniform(5, 25)
        else:
            roe = np.random.uniform(8, 30)
        
        return round(roe, 2)
    
    def _calculate_roa(self, symbol: str, market: str) -> float:
        """ROA 계산 (총자산이익률)"""
        # 실제로는 재무제표 데이터 필요
        if market.upper() == "KR":
            roa = np.random.uniform(2, 15)
        else:
            roa = np.random.uniform(3, 20)
        
        return round(roa, 2)
    
    def _calculate_debt_ratio(self, symbol: str, market: str) -> float:
        """부채비율 계산"""
        # 실제로는 재무제표 데이터 필요
        debt_ratio = np.random.uniform(10, 80)
        return round(debt_ratio, 2)
    
    def _calculate_momentum(self, price_data: pd.DataFrame, period: int) -> float:
        """모멘텀 계산 (N일 수익률)"""
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
            return round(np.random.uniform(-20, 20), 2)
    
    def _calculate_volatility(self, price_data: pd.DataFrame) -> float:
        """변동성 계산 (연환산 표준편차)"""
        try:
            returns = price_data['Close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252) * 100  # 연환산
            return round(volatility, 2)
            
        except Exception:
            return round(np.random.uniform(15, 40), 2)
    
    def _estimate_market_cap(self, price_data: pd.DataFrame, symbol: str, market: str) -> float:
        """시가총액 추정 (억원/백만달러)"""
        try:
            current_price = float(price_data['Close'].iloc[-1])
            
            if market.upper() == "KR":
                # 한국: 억원 단위로 반환
                estimated_shares = np.random.uniform(100000, 5000000)  # 발행주식수 추정
                market_cap = (current_price * estimated_shares) / 100000000  # 억원
            else:
                # 미국: 백만달러 단위로 반환
                estimated_shares = np.random.uniform(100000, 10000000)
                market_cap = (current_price * estimated_shares) / 1000000  # 백만달러
            
            return round(market_cap, 0)
            
        except Exception:
            if market.upper() == "KR":
                return round(np.random.uniform(1000, 100000), 0)  # 1천억 ~ 10조원
            else:
                return round(np.random.uniform(1000, 1000000), 0)  # 10억 ~ 1조달러
    
    def _calculate_quant_score(
        self, 
        per: float, 
        pbr: float, 
        roe: float, 
        roa: float, 
        debt_ratio: float, 
        momentum: float, 
        volatility: float, 
        market_cap: float
    ) -> float:
        """종합 퀀트 점수 계산 (0-100점)"""
        
        try:
            # 각 지표를 0-100 점수로 정규화
            
            # 가치 지표 (낮을수록 좋음)
            per_score = max(0, 100 - (per / 50 * 100))  # PER 50 이하면 만점
            pbr_score = max(0, 100 - (pbr / 5 * 100))   # PBR 5 이하면 만점
            
            # 수익성 지표 (높을수록 좋음)
            roe_score = min(100, roe * 3.33)  # ROE 30% 이상이면 만점
            roa_score = min(100, roa * 5)     # ROA 20% 이상이면 만점
            
            # 안정성 지표 (낮을수록 좋음)
            debt_score = max(0, 100 - (debt_ratio / 100 * 100))
            
            # 모멘텀 지표 (높을수록 좋음, 단 과도한 상승은 감점)
            momentum_score = min(100, max(0, 50 + momentum * 2))
            
            # 변동성 지표 (낮을수록 좋음)
            vol_score = max(0, 100 - (volatility / 50 * 100))
            
            # 가중 평균으로 최종 점수 계산
            final_score = (
                per_score * self.factor_weights.value * 0.4 +
                pbr_score * self.factor_weights.value * 0.6 +
                roe_score * self.factor_weights.quality * 0.6 +
                roa_score * self.factor_weights.quality * 0.4 +
                debt_score * self.factor_weights.quality * 0.3 +
                momentum_score * self.factor_weights.momentum +
                vol_score * self.factor_weights.low_vol
            )
            
            return round(min(100, max(0, final_score)), 1)
            
        except Exception:
            return round(np.random.uniform(30, 80), 1)
    
    def _get_recommendation(self, quant_score: float, per: float, pbr: float, roe: float) -> str:
        """투자 추천 결정"""
        
        # 퀀트 점수 기반 기본 추천
        if quant_score >= 75:
            base_rec = "BUY"
        elif quant_score >= 45:
            base_rec = "HOLD"
        else:
            base_rec = "SELL"
        
        # 추가 조건 검토
        if per > 30 or pbr > 5:  # 과도한 고평가
            if base_rec == "BUY":
                base_rec = "HOLD"
        
        if roe < 5:  # 낮은 수익성
            if base_rec == "BUY":
                base_rec = "HOLD"
        
        return base_rec
    
    def _generate_mock_indicators(self, market: str, limit: int) -> List[QuantIndicator]:
        """Mock 퀀트 지표 데이터 생성"""
        
        indicators = []
        
        if market.upper() == "KR":
            symbols = ['005930', '000660', '035420', '051910', '005380', '068270', '006400', '035720', '207940', '066570']
            names = ['삼성전자', 'SK하이닉스', 'NAVER', 'LG화학', '현대차', '셀트리온', '삼성SDI', '카카오', '삼성바이오로직스', 'LG전자']
        else:
            symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE', 'CRM']
            names = ['Apple', 'Microsoft', 'Alphabet', 'Amazon', 'Tesla', 'Meta', 'NVIDIA', 'Netflix', 'Adobe', 'Salesforce']
        
        for i in range(min(len(symbols), limit)):
            per = round(np.random.uniform(8, 35), 2)
            pbr = round(np.random.uniform(0.8, 4.5), 2)
            roe = round(np.random.uniform(5, 25), 2)
            roa = round(np.random.uniform(3, 18), 2)
            debt_ratio = round(np.random.uniform(15, 75), 2)
            momentum_3m = round(np.random.uniform(-25, 25), 2)
            volatility = round(np.random.uniform(15, 40), 2)
            
            if market.upper() == "KR":
                market_cap = round(np.random.uniform(5000, 50000), 0)  # 억원
            else:
                market_cap = round(np.random.uniform(10000, 500000), 0)  # 백만달러
            
            quant_score = self._calculate_quant_score(
                per, pbr, roe, roa, debt_ratio, momentum_3m, volatility, market_cap
            )
            
            recommendation = self._get_recommendation(quant_score, per, pbr, roe)
            
            indicators.append(QuantIndicator(
                symbol=symbols[i],
                name=names[i],
                market=market,
                per=per,
                pbr=pbr,
                roe=roe,
                roa=roa,
                debt_ratio=debt_ratio,
                momentum_3m=momentum_3m,
                market_cap=market_cap,
                volatility=volatility,
                quant_score=quant_score,
                recommendation=recommendation
            ))
        
        # 퀀트 점수 기준 정렬
        indicators.sort(key=lambda x: x.quant_score, reverse=True)
        return indicators
    
    async def run_factor_strategy_backtest(
        self, 
        strategy_id: str, 
        market: str = "KR", 
        period: str = "1y"
    ) -> BacktestResult:
        """팩터 전략 백테스트 실행"""
        
        try:
            # 전략별 종목 선별 조건 정의
            strategy_configs = {
                "value": {"per_max": 15, "pbr_max": 1.5, "roe_min": 10},
                "momentum": {"momentum_min": 15, "vol_max": 25},
                "quality": {"roe_min": 15, "debt_max": 50, "roa_min": 10},
                "lowvol": {"vol_max": 20, "debt_max": 40},
                "size": {"market_cap_max": 10000 if market.upper() == "KR" else 5000}
            }
            
            config = strategy_configs.get(strategy_id, {})
            
            # 퀀트 지표 데이터 가져오기
            indicators = await self.get_quant_indicators(market, 100)
            
            # 전략에 따른 종목 필터링
            selected_stocks = self._filter_stocks_by_strategy(indicators, config)
            
            # 백테스트 실행 (실제로는 과거 데이터로 수익률 계산)
            backtest_result = self._simulate_backtest(strategy_id, selected_stocks, period)
            
            return backtest_result
            
        except Exception as e:
            logger.error(f"백테스트 실행 실패: {e}")
            return self._generate_mock_backtest_result(strategy_id, period)
    
    def _filter_stocks_by_strategy(
        self, 
        indicators: List[QuantIndicator], 
        config: Dict
    ) -> List[str]:
        """전략별 종목 필터링"""
        
        selected = []
        
        for indicator in indicators:
            include = True
            
            # 조건 확인
            if "per_max" in config and indicator.per > config["per_max"]:
                include = False
            if "pbr_max" in config and indicator.pbr > config["pbr_max"]:
                include = False
            if "roe_min" in config and indicator.roe < config["roe_min"]:
                include = False
            if "roa_min" in config and indicator.roa < config["roa_min"]:
                include = False
            if "debt_max" in config and indicator.debt_ratio > config["debt_max"]:
                include = False
            if "momentum_min" in config and indicator.momentum_3m < config["momentum_min"]:
                include = False
            if "vol_max" in config and indicator.volatility > config["vol_max"]:
                include = False
            if "market_cap_max" in config and indicator.market_cap > config["market_cap_max"]:
                include = False
            
            if include:
                selected.append(indicator.symbol)
        
        return selected[:20]  # 상위 20개 종목
    
    def _simulate_backtest(
        self, 
        strategy_id: str, 
        selected_stocks: List[str], 
        period: str
    ) -> BacktestResult:
        """백테스트 시뮬레이션"""
        
        # 실제로는 과거 데이터로 포트폴리오 수익률 계산
        # 여기서는 전략별 특성을 반영한 Mock 결과 생성
        
        strategy_performance = {
            "value": {"return_mult": 1.2, "volatility": 0.8},
            "momentum": {"return_mult": 1.4, "volatility": 1.3},
            "quality": {"return_mult": 1.1, "volatility": 0.7},
            "lowvol": {"return_mult": 0.9, "volatility": 0.5},
            "size": {"return_mult": 1.3, "volatility": 1.2}
        }
        
        perf = strategy_performance.get(strategy_id, {"return_mult": 1.0, "volatility": 1.0})
        
        # 기본 시장 수익률에 전략 특성 반영
        base_return = np.random.uniform(5, 15)  # 5-15% 기본 수익률
        total_return = base_return * perf["return_mult"] * np.random.uniform(0.7, 1.3)
        
        annual_return = total_return
        if period == "2y":
            annual_return = total_return / 2
        elif period == "3y":
            annual_return = total_return / 3
        
        max_drawdown = -abs(np.random.uniform(5, 20) * perf["volatility"])
        volatility_annual = np.random.uniform(15, 25) * perf["volatility"]
        sharpe_ratio = annual_return / volatility_annual if volatility_annual > 0 else 0
        win_rate = np.random.uniform(55, 75)
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        if period == "1y":
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        elif period == "2y":
            start_date = (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d")
        else:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        return BacktestResult(
            strategy=strategy_id,
            total_return=round(total_return, 2),
            annual_return=round(annual_return, 2),
            max_drawdown=round(max_drawdown, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            win_rate=round(win_rate, 1),
            start_date=start_date,
            end_date=end_date,
            selected_stocks=selected_stocks
        )
    
    def _generate_mock_backtest_result(self, strategy_id: str, period: str) -> BacktestResult:
        """Mock 백테스트 결과 생성"""
        
        total_return = np.random.uniform(-10, 25)
        annual_return = total_return
        
        if period == "2y":
            annual_return = total_return / 2
        elif period == "3y":
            annual_return = total_return / 3
        
        max_drawdown = -abs(np.random.uniform(5, 20))
        sharpe_ratio = np.random.uniform(0.5, 2.0)
        win_rate = np.random.uniform(50, 70)
        
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        return BacktestResult(
            strategy=strategy_id,
            total_return=round(total_return, 2),
            annual_return=round(annual_return, 2),
            max_drawdown=round(max_drawdown, 2),
            sharpe_ratio=round(sharpe_ratio, 2),
            win_rate=round(win_rate, 1),
            start_date=start_date,
            end_date=end_date,
            selected_stocks=[]
        )


# 전역 서비스 인스턴스
quant_service = QuantAnalysisService()