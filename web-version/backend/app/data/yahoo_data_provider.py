"""
Yahoo Finance 기반 데이터 제공자
한국 지수 및 재무 데이터 보완용
"""
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
import logging
import yfinance as yf

from .base_stock_data_provider import StockDataProvider

logger = logging.getLogger(__name__)


class YahooDataProvider(StockDataProvider):
    """Yahoo Finance 기반 데이터 제공자 구현"""
    
    def __init__(self):
        self._name = "YahooFinance"
        self._supported_markets = ["KR", "US"]
        
        # Yahoo Finance 심볼 매핑
        self.kr_symbol_mapping = {
            # 주요 한국 주식 (Yahoo는 .KS/.KQ 접미사 사용)
            '005930': '005930.KS',  # 삼성전자
            '000660': '000660.KS',  # SK하이닉스
            '005490': '005490.KS',  # POSCO홀딩스
            '005380': '005380.KS',  # 현대차
            '051910': '051910.KS',  # LG화학
            '000270': '000270.KS',  # 기아
            '068270': '068270.KS',  # 셀트리온
            '035420': '035420.KS',  # NAVER
            '003550': '003550.KS',  # LG
            '105560': '105560.KS',  # KB금융
        }
        
        # 지수 심볼 매핑
        self.index_mapping = {
            # 한국 지수
            '1001': '^KS11',     # KOSPI
            '2001': '^KQ11',     # KOSDAQ (Note: Limited data)
            '1028': '^KS200',    # KOSPI 200
            'KOSPI': '^KS11',
            'KOSDAQ': '^KQ11',
            'KOSPI200': '^KS200',
            # 미국 지수
            '^GSPC': '^GSPC',    # S&P 500
            '^IXIC': '^IXIC',    # NASDAQ
            '^DJI': '^DJI',      # Dow Jones
            '^RUT': '^RUT',      # Russell 2000
            '^VIX': '^VIX',      # VIX
            'S&P500': '^GSPC',
            'NASDAQ': '^IXIC',
            'DowJones': '^DJI'
        }
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def supported_markets(self) -> List[str]:
        return self._supported_markets
    
    def _convert_kr_symbol(self, symbol: str) -> str:
        """한국 종목 코드를 Yahoo Finance 형식으로 변환"""
        # 이미 매핑된 종목
        if symbol in self.kr_symbol_mapping:
            return self.kr_symbol_mapping[symbol]
        
        # 6자리 숫자인 경우 .KS 추가 (KOSPI 기본)
        if symbol.isdigit() and len(symbol) == 6:
            return f"{symbol}.KS"
        
        # 그 외는 그대로 반환
        return symbol
    
    def get_stock_list(self, market: str = "ALL", date: Optional[str] = None) -> List[Dict[str, Any]]:
        """주식 목록 조회 - Yahoo는 전체 목록 제공 안함"""
        logger.warning("Yahoo Finance does not provide full stock list. Returning predefined stocks.")
        
        result = []
        if market.upper() in ["KR", "ALL"]:
            # 사전 정의된 한국 주요 종목
            kr_stocks = [
                ('005930', '삼성전자'), ('000660', 'SK하이닉스'), 
                ('005490', 'POSCO홀딩스'), ('005380', '현대차'),
                ('051910', 'LG화학'), ('000270', '기아'),
                ('068270', '셀트리온'), ('035420', 'NAVER'),
                ('003550', 'LG'), ('105560', 'KB금융')
            ]
            
            for code, name in kr_stocks:
                result.append({
                    'symbol': code,
                    'name': name,
                    'market': 'KR',
                    'display': f"{name} ({code})"
                })
        
        if market.upper() in ["US", "ALL"]:
            # 미국 주요 종목
            us_stocks = [
                ('AAPL', 'Apple'), ('MSFT', 'Microsoft'),
                ('GOOGL', 'Alphabet'), ('AMZN', 'Amazon'),
                ('NVDA', 'NVIDIA'), ('META', 'Meta')
            ]
            
            for code, name in us_stocks:
                result.append({
                    'symbol': code,
                    'name': name,
                    'market': 'US',
                    'display': f"{name} ({code})"
                })
        
        return result
    
    def get_stock_price(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """주식 가격 데이터 조회"""
        try:
            # 한국 종목인 경우 심볼 변환
            if symbol.isdigit():
                yahoo_symbol = self._convert_kr_symbol(symbol)
            else:
                yahoo_symbol = symbol
            
            # yfinance로 데이터 가져오기
            ticker = yf.Ticker(yahoo_symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                logger.warning(f"No data found for {yahoo_symbol}")
                return pd.DataFrame()
            
            # 컬럼명 정리
            hist = hist.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # 필요한 컬럼만 선택
            return hist[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Failed to get stock price for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_stock_price_realtime(self, symbol: str) -> Dict[str, Any]:
        """실시간 주식 가격 조회"""
        try:
            # 한국 종목인 경우 심볼 변환
            if symbol.isdigit():
                yahoo_symbol = self._convert_kr_symbol(symbol)
            else:
                yahoo_symbol = symbol
            
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            
            # 최근 데이터 가져오기
            hist = ticker.history(period="5d")
            if hist.empty:
                return {}
            
            latest = hist.iloc[-1]
            
            # 전일 대비 계산
            if len(hist) >= 2:
                prev_close = hist.iloc[-2]['Close']
                change = latest['Close'] - prev_close
                change_percent = (change / prev_close * 100) if prev_close > 0 else 0
            else:
                # info에서 가져오기
                change = info.get('regularMarketChange', 0)
                change_percent = info.get('regularMarketChangePercent', 0)
            
            return {
                'symbol': symbol,
                'price': float(latest['Close']),
                'change': float(change),
                'change_percent': float(change_percent),
                'volume': int(latest['Volume']),
                'date': hist.index[-1].strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            logger.error(f"Failed to get realtime price for {symbol}: {e}")
            return {}
    
    def get_stock_fundamental(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """재무 데이터 조회"""
        try:
            # 한국 종목인 경우 심볼 변환
            if symbol.isdigit():
                yahoo_symbol = self._convert_kr_symbol(symbol)
            else:
                yahoo_symbol = symbol
            
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            
            # Yahoo는 현재 시점의 재무 데이터만 제공
            if not info:
                return pd.DataFrame()
            
            # 단일 행 DataFrame 생성
            data = {
                'per': info.get('trailingPE'),
                'pbr': info.get('priceToBook'),
                'eps': info.get('trailingEps'),
                'bps': info.get('bookValue'),
                'div': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else None
            }
            
            # 날짜는 end_date 사용
            df = pd.DataFrame([data], index=[pd.to_datetime(end_date)])
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to get fundamental data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_market_cap(self, symbol: str, date: Optional[str] = None) -> Dict[str, Any]:
        """시가총액 조회"""
        try:
            # 한국 종목인 경우 심볼 변환
            if symbol.isdigit():
                yahoo_symbol = self._convert_kr_symbol(symbol)
            else:
                yahoo_symbol = symbol
            
            ticker = yf.Ticker(yahoo_symbol)
            info = ticker.info
            
            if not info:
                return {}
            
            return {
                'market_cap': info.get('marketCap', 0),
                'shares': info.get('sharesOutstanding', 0)
            }
            
        except Exception as e:
            logger.error(f"Failed to get market cap for {symbol}: {e}")
            return {}
    
    def get_index_data(self, index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """지수 데이터 조회"""
        try:
            # 지수 코드 변환
            yahoo_symbol = self.index_mapping.get(index_code, index_code)
            
            # 지수 심볼이 ^로 시작하지 않으면 추가
            if not yahoo_symbol.startswith('^') and index_code.isdigit():
                # 숫자 코드인 경우 매핑 확인
                yahoo_symbol = self.index_mapping.get(index_code, index_code)
            
            logger.info(f"Fetching index data for {index_code} -> {yahoo_symbol}")
            
            # yfinance로 데이터 가져오기
            ticker = yf.Ticker(yahoo_symbol)
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                logger.warning(f"No index data found for {yahoo_symbol}")
                return pd.DataFrame()
            
            # 컬럼명 정리
            hist = hist.rename(columns={
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            return hist[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Failed to get index data for {index_code}: {e}")
            return pd.DataFrame()
    
    def get_market_overview(self, market: str = "KR", date: Optional[str] = None) -> pd.DataFrame:
        """시장 전체 데이터 조회"""
        try:
            stocks = self.get_stock_list(market)
            data = []
            
            for stock in stocks[:10]:  # 상위 10개만
                price_info = self.get_stock_price_realtime(stock['symbol'])
                if price_info:
                    data.append({
                        'ticker': stock['symbol'],
                        'name': stock['name'],
                        '종가': price_info['price'],
                        '등락률': price_info['change_percent'],
                        '거래량': price_info['volume']
                    })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Failed to get market overview: {e}")
            return pd.DataFrame()