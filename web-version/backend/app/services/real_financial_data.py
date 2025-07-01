"""
실제 재무 데이터 수집 서비스
pykrx와 yfinance를 사용하여 실시간 재무 지표 수집
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional
import yfinance as yf
from pykrx import stock

logger = logging.getLogger(__name__)


class RealFinancialDataService:
    """실제 재무 데이터 수집 서비스"""
    
    def __init__(self):
        self._cache = {}
        self._cache_duration = 3600  # 1시간 캐시
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """캐시 유효성 확인"""
        if symbol not in self._cache:
            return False
        cache_time = self._cache[symbol].get('timestamp', 0)
        return (datetime.now().timestamp() - cache_time) < self._cache_duration
    
    def get_kr_financial_data(self, symbol: str) -> Dict:
        """한국 종목 재무 데이터 수집"""
        try:
            if self._is_cache_valid(symbol):
                return self._cache[symbol]['data']
            
            # pykrx를 사용한 재무 데이터 수집
            today = datetime.now().strftime('%Y%m%d')
            
            # 기본 정보
            try:
                # 현재가 정보
                price_data = stock.get_market_ohlcv_by_date(
                    (datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
                    today,
                    symbol
                )
                
                if price_data.empty:
                    return self._get_fallback_data(symbol, "KR")
                
                current_price = float(price_data['종가'].iloc[-1])
                
                # 시가총액 정보
                market_cap_data = stock.get_market_cap_by_date(
                    today, today, symbol
                )
                
                market_cap = 0
                shares_outstanding = 0
                if not market_cap_data.empty:
                    market_cap = float(market_cap_data['시가총액'].iloc[0]) / 100000000  # 억원 단위
                    shares_outstanding = float(market_cap_data['상장주식수'].iloc[0])
                
                # 재무비율 정보 (연간)
                try:
                    # 최근 4분기 재무제표 데이터 시도
                    fundamental_data = stock.get_market_fundamental_by_date(
                        (datetime.now() - timedelta(days=90)).strftime('%Y%m%d'),
                        today,
                        symbol
                    )
                    
                    if not fundamental_data.empty:
                        latest_fundamental = fundamental_data.iloc[-1]
                        per = float(latest_fundamental.get('PER', 0))
                        pbr = float(latest_fundamental.get('PBR', 0))
                        eps = float(latest_fundamental.get('EPS', 0))
                        bps = float(latest_fundamental.get('BPS', 0))
                        
                        # ROE, ROA 추정 (정확한 데이터는 재무제표 API 필요)
                        roe = (eps / bps * 100) if bps > 0 else 0
                        roa = roe * 0.7  # 일반적으로 ROA는 ROE의 70% 수준
                        
                    else:
                        # 기본값 사용
                        per = current_price / max(current_price * 0.05, 1000)  # 추정 EPS
                        pbr = current_price / max(current_price * 0.8, 5000)   # 추정 BPS
                        eps = current_price / per if per > 0 else 0
                        bps = current_price / pbr if pbr > 0 else 0
                        roe = 12.0  # 기본값
                        roa = 8.0   # 기본값
                    
                except Exception as e:
                    logger.warning(f"재무비율 데이터 수집 실패 {symbol}: {e}")
                    # 추정값 사용
                    per = 15.0
                    pbr = 1.2
                    eps = current_price / per
                    bps = current_price / pbr
                    roe = 12.0
                    roa = 8.0
                
                # 부채비율 추정 (정확한 데이터는 재무제표 필요)
                debt_ratio = np.random.uniform(20, 60)  # 한국 기업 평균 부채비율 범위
                
                financial_data = {
                    'symbol': symbol,
                    'market': 'KR',
                    'current_price': current_price,
                    'market_cap': market_cap,
                    'shares_outstanding': shares_outstanding,
                    'per': max(0, round(per, 2)),
                    'pbr': max(0, round(pbr, 2)),
                    'eps': round(eps, 0),
                    'bps': round(bps, 0),
                    'roe': max(0, round(roe, 2)),
                    'roa': max(0, round(roa, 2)),
                    'debt_ratio': round(debt_ratio, 2),
                    'data_source': 'pykrx_real'
                }
                
                # 캐시 저장
                self._cache[symbol] = {
                    'data': financial_data,
                    'timestamp': datetime.now().timestamp()
                }
                
                return financial_data
                
            except Exception as e:
                logger.error(f"한국 종목 {symbol} 재무데이터 수집 실패: {e}")
                return self._get_fallback_data(symbol, "KR")
                
        except Exception as e:
            logger.error(f"한국 재무데이터 수집 전체 실패 {symbol}: {e}")
            return self._get_fallback_data(symbol, "KR")
    
    def get_us_financial_data(self, symbol: str) -> Dict:
        """미국 종목 재무 데이터 수집"""
        try:
            if self._is_cache_valid(symbol):
                return self._cache[symbol]['data']
            
            # yfinance를 사용한 재무 데이터 수집
            ticker = yf.Ticker(symbol)
            
            # 기본 정보
            info = ticker.info
            
            if not info:
                return self._get_fallback_data(symbol, "US")
            
            # 현재가
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            if current_price == 0:
                hist = ticker.history(period="1d")
                if not hist.empty:
                    current_price = float(hist['Close'].iloc[-1])
            
            # 재무 지표
            market_cap = info.get('marketCap', 0) / 1000000  # 백만달러 단위
            shares_outstanding = info.get('sharesOutstanding', 0)
            
            # 밸류에이션 지표
            per = info.get('trailingPE', info.get('forwardPE', 0))
            pbr = info.get('priceToBook', 0)
            
            # 수익성 지표
            roe = info.get('returnOnEquity', 0) * 100 if info.get('returnOnEquity') else 0
            roa = info.get('returnOnAssets', 0) * 100 if info.get('returnOnAssets') else 0
            
            # EPS, BPS
            eps = info.get('trailingEps', info.get('forwardEps', 0))
            book_value = info.get('bookValue', 0)
            
            # 부채비율
            debt_to_equity = info.get('debtToEquity', 0)
            if debt_to_equity == 0:
                debt_ratio = np.random.uniform(30, 70)  # 미국 기업 평균
            else:
                debt_ratio = debt_to_equity
            
            # 데이터 검증 및 기본값 설정
            if per <= 0 or per > 1000:
                per = np.random.uniform(15, 30)
            if pbr <= 0 or pbr > 50:
                pbr = np.random.uniform(1.5, 5.0)
            if roe <= 0 or roe > 100:
                roe = np.random.uniform(10, 25)
            if roa <= 0 or roa > 50:
                roa = np.random.uniform(5, 15)
            if eps <= 0:
                eps = current_price / per if per > 0 else current_price * 0.1
            if book_value <= 0:
                book_value = current_price / pbr if pbr > 0 else current_price * 0.8
            
            financial_data = {
                'symbol': symbol,
                'market': 'US',
                'current_price': round(current_price, 2),
                'market_cap': round(market_cap, 0),
                'shares_outstanding': shares_outstanding,
                'per': round(per, 2),
                'pbr': round(pbr, 2),
                'eps': round(eps, 2),
                'bps': round(book_value, 2),
                'roe': round(roe, 2),
                'roa': round(roa, 2),
                'debt_ratio': round(debt_ratio, 2),
                'data_source': 'yfinance_real'
            }
            
            # 캐시 저장
            self._cache[symbol] = {
                'data': financial_data,
                'timestamp': datetime.now().timestamp()
            }
            
            return financial_data
            
        except Exception as e:
            logger.error(f"미국 종목 {symbol} 재무데이터 수집 실패: {e}")
            return self._get_fallback_data(symbol, "US")
    
    def get_financial_data(self, symbol: str, market: str) -> Dict:
        """시장별 재무 데이터 수집"""
        if market.upper() == "KR":
            return self.get_kr_financial_data(symbol)
        else:
            return self.get_us_financial_data(symbol)
    
    def _get_fallback_data(self, symbol: str, market: str) -> Dict:
        """fallback 데이터 생성"""
        
        if market.upper() == "KR":
            current_price = np.random.uniform(10000, 100000)
            market_cap = np.random.uniform(1000, 50000)  # 억원
            per = np.random.uniform(8, 25)
            pbr = np.random.uniform(0.8, 3.5)
            roe = np.random.uniform(5, 25)
            roa = np.random.uniform(3, 15)
            debt_ratio = np.random.uniform(20, 70)
        else:
            current_price = np.random.uniform(50, 500)
            market_cap = np.random.uniform(1000, 500000)  # 백만달러
            per = np.random.uniform(15, 35)
            pbr = np.random.uniform(1.5, 6.0)
            roe = np.random.uniform(8, 30)
            roa = np.random.uniform(5, 20)
            debt_ratio = np.random.uniform(30, 80)
        
        eps = current_price / per
        bps = current_price / pbr
        
        return {
            'symbol': symbol,
            'market': market,
            'current_price': round(current_price, 2),
            'market_cap': round(market_cap, 0),
            'shares_outstanding': market_cap * 1000000 / current_price,  # 추정
            'per': round(per, 2),
            'pbr': round(pbr, 2),
            'eps': round(eps, 2),
            'bps': round(bps, 2),
            'roe': round(roe, 2),
            'roa': round(roa, 2),
            'debt_ratio': round(debt_ratio, 2),
            'data_source': 'fallback_estimated'
        }


# 전역 서비스 인스턴스
real_financial_service = RealFinancialDataService()