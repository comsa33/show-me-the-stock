"""
백테스트 서비스
실제 과거 주가 데이터를 사용한 투자 전략 시뮬레이션
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from pydantic import BaseModel

from app.data.stock_data import StockDataFetcher
from app.core.cache import cached

logger = logging.getLogger(__name__)


class BacktestResult(BaseModel):
    """백테스트 결과"""
    symbol: str
    company_name: str
    strategy: str
    period: str
    investment_amount: float
    final_amount: float
    total_return: float
    total_return_percent: float
    annual_return: float
    max_drawdown: float
    win_rate: float
    trades: int
    best_trade: float
    worst_trade: float
    start_date: str
    end_date: str
    start_price: float
    end_price: float
    sharpe_ratio: float  # 위험 대비 수익률
    volatility: float    # 변동성


class BacktestService:
    def __init__(self):
        self.stock_fetcher = StockDataFetcher()
    
    @cached(ttl=3600, key_prefix="backtest")
    async def run_backtest(
        self,
        symbol: str,
        market: str,
        start_date: str,
        end_date: str,
        investment_amount: float,
        strategy: str = "buy_hold"
    ) -> Optional[BacktestResult]:
        """실제 과거 데이터로 백테스트 실행"""
        
        try:
            # 1. 과거 주가 데이터 가져오기
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            # 기간 계산을 위해 더 긴 기간의 데이터 가져오기
            data_start = start_dt - timedelta(days=100)  # 이동평균 계산용
            
            # 주가 데이터 가져오기
            price_data = self._get_historical_prices(symbol, market, data_start, end_dt)
            if price_data is None or price_data.empty:
                logger.error(f"No price data for {symbol}")
                return None
            
            # 실제 백테스트 기간 데이터만 필터링
            backtest_data = price_data[price_data.index >= start_dt]
            if backtest_data.empty:
                logger.error(f"No data in backtest period for {symbol}")
                return None
            
            # 2. 전략별 백테스트 실행
            if strategy == "buy_hold":
                result = self._buy_and_hold_strategy(backtest_data, investment_amount)
            elif strategy == "technical":
                result = self._technical_strategy(price_data, backtest_data, investment_amount)
            elif strategy == "value":
                result = self._value_strategy(backtest_data, investment_amount)
            else:
                result = self._buy_and_hold_strategy(backtest_data, investment_amount)
            
            # 3. 결과 계산
            period_days = (end_dt - start_dt).days
            period_years = period_days / 365.25
            
            # 연간 수익률 계산 (CAGR)
            annual_return = (pow(result['final_value'] / investment_amount, 1/period_years) - 1) * 100 if period_years > 0 else 0
            
            # 변동성 계산
            daily_returns = backtest_data['Close'].pct_change().dropna()
            volatility = daily_returns.std() * np.sqrt(252) * 100  # 연간 변동성
            
            # 샤프 비율 계산 (무위험 수익률 2% 가정)
            risk_free_rate = 0.02
            sharpe_ratio = (annual_return/100 - risk_free_rate) / (volatility/100) if volatility > 0 else 0
            
            # 회사명 가져오기
            company_name = self._get_company_name(symbol, market)
            
            return BacktestResult(
                symbol=symbol,
                company_name=company_name,
                strategy=self._get_strategy_name(strategy),
                period=f"{period_days}일 ({round(period_years, 1)}년)",
                investment_amount=investment_amount,
                final_amount=round(result['final_value'], 2),
                total_return=round(result['total_profit'], 2),
                total_return_percent=round(result['total_return_pct'], 2),
                annual_return=round(annual_return, 2),
                max_drawdown=round(result['max_drawdown'], 2),
                win_rate=round(result['win_rate'], 2),
                trades=result['trades'],
                best_trade=round(result['best_trade'], 2),
                worst_trade=round(result['worst_trade'], 2),
                start_date=start_date,
                end_date=end_date,
                start_price=round(backtest_data['Close'].iloc[0], 2),
                end_price=round(backtest_data['Close'].iloc[-1], 2),
                sharpe_ratio=round(sharpe_ratio, 2),
                volatility=round(volatility, 2)
            )
            
        except Exception as e:
            logger.error(f"Backtest error for {symbol}: {str(e)}")
            return None
    
    def _get_historical_prices(self, symbol: str, market: str, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
        """과거 주가 데이터 가져오기"""
        try:
            # 날짜 범위 계산
            days = (end_date - start_date).days
            interval = "1d"
            
            # StockDataFetcher 사용
            data = self.stock_fetcher.get_stock_data(symbol, f"{days}d", market)
            if data is not None and not data.empty:
                # 날짜 범위 필터링
                data = data[(data.index >= start_date) & (data.index <= end_date)]
            return data
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return None
    
    def _buy_and_hold_strategy(self, data: pd.DataFrame, investment: float) -> Dict:
        """매수 후 보유 전략"""
        start_price = data['Close'].iloc[0]
        end_price = data['Close'].iloc[-1]
        
        # 주식 수 계산
        shares = investment / start_price
        final_value = shares * end_price
        
        # 수익 계산
        total_profit = final_value - investment
        total_return_pct = (total_profit / investment) * 100
        
        # 최대 낙폭 계산
        cumulative_returns = (data['Close'] / start_price - 1)
        running_max = cumulative_returns.cummax()
        drawdown = cumulative_returns - running_max
        max_drawdown = drawdown.min() * 100
        
        return {
            'final_value': final_value,
            'total_profit': total_profit,
            'total_return_pct': total_return_pct,
            'max_drawdown': max_drawdown,
            'win_rate': 100.0 if total_profit > 0 else 0.0,
            'trades': 1,
            'best_trade': total_return_pct,
            'worst_trade': total_return_pct
        }
    
    def _technical_strategy(self, full_data: pd.DataFrame, backtest_data: pd.DataFrame, investment: float) -> Dict:
        """기술적 분석 전략 (이동평균 교차)"""
        # 이동평균 계산
        full_data['MA20'] = full_data['Close'].rolling(window=20).mean()
        full_data['MA60'] = full_data['Close'].rolling(window=60).mean()
        
        # 백테스트 기간 데이터에 이동평균 추가
        backtest_data = backtest_data.copy()
        backtest_data['MA20'] = full_data.loc[backtest_data.index, 'MA20']
        backtest_data['MA60'] = full_data.loc[backtest_data.index, 'MA60']
        
        # 시그널 생성 (골든크로스/데드크로스)
        backtest_data['Signal'] = 0
        backtest_data.loc[backtest_data['MA20'] > backtest_data['MA60'], 'Signal'] = 1
        backtest_data.loc[backtest_data['MA20'] < backtest_data['MA60'], 'Signal'] = -1
        
        # 포지션 변화 감지
        backtest_data['Position'] = backtest_data['Signal'].diff()
        
        # 거래 실행
        cash = investment
        shares = 0
        trades = []
        entry_price = None
        
        for idx, row in backtest_data.iterrows():
            if row['Position'] == 2 and cash > 0:  # 매수 신호
                shares = cash / row['Close']
                cash = 0
                entry_price = row['Close']
                
            elif row['Position'] == -2 and shares > 0:  # 매도 신호
                cash = shares * row['Close']
                if entry_price:
                    trade_return = ((row['Close'] - entry_price) / entry_price) * 100
                    trades.append(trade_return)
                shares = 0
                entry_price = None
        
        # 마지막 포지션 정리
        if shares > 0:
            cash = shares * backtest_data['Close'].iloc[-1]
            if entry_price:
                trade_return = ((backtest_data['Close'].iloc[-1] - entry_price) / entry_price) * 100
                trades.append(trade_return)
        
        final_value = cash
        total_profit = final_value - investment
        total_return_pct = (total_profit / investment) * 100
        
        # 거래 통계
        if trades:
            winning_trades = [t for t in trades if t > 0]
            losing_trades = [t for t in trades if t <= 0]
            win_rate = (len(winning_trades) / len(trades)) * 100
            best_trade = max(trades)
            worst_trade = min(trades)
        else:
            win_rate = 0
            best_trade = 0
            worst_trade = 0
        
        # 최대 낙폭은 매수 후 보유와 동일한 방식으로 계산
        return {
            'final_value': final_value,
            'total_profit': total_profit,
            'total_return_pct': total_return_pct,
            'max_drawdown': self._calculate_max_drawdown(backtest_data, cash, shares, investment),
            'win_rate': win_rate,
            'trades': len(trades),
            'best_trade': best_trade,
            'worst_trade': worst_trade
        }
    
    def _value_strategy(self, data: pd.DataFrame, investment: float) -> Dict:
        """가치 투자 전략 (단순화: 하락 시 매수, 상승 시 보유)"""
        # 단순화된 가치 투자: 52주 최고가 대비 20% 이상 하락 시 매수
        data['High52W'] = data['Close'].rolling(window=252, min_periods=20).max()
        data['Discount'] = (data['High52W'] - data['Close']) / data['High52W']
        
        # 20% 이상 할인된 첫 시점에 매수
        buy_signal = data[data['Discount'] >= 0.2]
        
        if not buy_signal.empty:
            buy_price = buy_signal['Close'].iloc[0]
            buy_date = buy_signal.index[0]
            
            # 매수 시점 이후 데이터
            hold_data = data[data.index >= buy_date]
            
            shares = investment / buy_price
            final_value = shares * data['Close'].iloc[-1]
            
            total_profit = final_value - investment
            total_return_pct = (total_profit / investment) * 100
            
            # 최대 낙폭
            cumulative_returns = (hold_data['Close'] / buy_price - 1)
            running_max = cumulative_returns.cummax()
            drawdown = cumulative_returns - running_max
            max_drawdown = drawdown.min() * 100
        else:
            # 매수 신호가 없으면 현금 보유
            final_value = investment
            total_profit = 0
            total_return_pct = 0
            max_drawdown = 0
        
        return {
            'final_value': final_value,
            'total_profit': total_profit,
            'total_return_pct': total_return_pct,
            'max_drawdown': max_drawdown,
            'win_rate': 100.0 if total_profit > 0 else 0.0,
            'trades': 1 if not buy_signal.empty else 0,
            'best_trade': total_return_pct,
            'worst_trade': total_return_pct
        }
    
    def _calculate_max_drawdown(self, data: pd.DataFrame, cash: float, shares: float, investment: float) -> float:
        """최대 낙폭 계산"""
        portfolio_values = []
        for _, row in data.iterrows():
            if shares > 0:
                value = shares * row['Close']
            else:
                value = cash
            portfolio_values.append(value)
        
        portfolio_series = pd.Series(portfolio_values, index=data.index)
        cumulative_returns = (portfolio_series / investment - 1)
        running_max = cumulative_returns.cummax()
        drawdown = cumulative_returns - running_max
        return drawdown.min() * 100
    
    def _get_company_name(self, symbol: str, market: str) -> str:
        """회사명 가져오기"""
        try:
            if market == "KR":
                stocks = self.stock_fetcher.get_all_kr_stocks()
            else:
                stocks = self.stock_fetcher.get_all_us_stocks()
            
            for stock in stocks:
                if stock['symbol'] == symbol:
                    return stock['name']
            return symbol
        except:
            return symbol
    
    def _get_strategy_name(self, strategy: str) -> str:
        """전략명 한글 변환"""
        strategy_names = {
            'buy_hold': '매수 후 보유',
            'technical': '기술적 분석 (이동평균)',
            'value': '가치 투자'
        }
        return strategy_names.get(strategy, strategy)


# 서비스 인스턴스
backtest_service = BacktestService()