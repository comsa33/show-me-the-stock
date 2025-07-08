"""
FinanceDataReader 기반 데이터 제공자
pykrx를 대체할 주요 데이터 소스
"""
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta
import logging
import FinanceDataReader as fdr
import json
import os

from .base_stock_data_provider import StockDataProvider

logger = logging.getLogger(__name__)


class FDRDataProvider(StockDataProvider):
    """FinanceDataReader 기반 데이터 제공자 구현"""
    
    def __init__(self):
        self._name = "FinanceDataReader"
        self._supported_markets = ["KR", "US"]
        
        # 한국 주식 목록 캐시 (파일 기반)
        self.kr_stock_cache_file = "kr_stocks_cache.json"
        self.kr_stocks_cache = None
        self.cache_date = None
        
        # 지수 코드 매핑
        self.index_mapping = {
            # 한국 지수
            "1001": "KS11",    # KOSPI
            "2001": "KQ11",    # KOSDAQ
            "1028": "KS200",   # KOSPI200
            # 미국 지수
            "^GSPC": "^GSPC",  # S&P 500
            "^IXIC": "^IXIC",  # NASDAQ
            "^DJI": "^DJI",    # Dow Jones
            "^RUT": "^RUT",    # Russell 2000
            "^VIX": "^VIX"     # VIX
        }
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def supported_markets(self) -> List[str]:
        return self._supported_markets
    
    def _load_kr_stock_cache(self):
        """한국 주식 목록 캐시 로드"""
        try:
            if os.path.exists(self.kr_stock_cache_file):
                with open(self.kr_stock_cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cache_date = datetime.strptime(data['date'], '%Y-%m-%d')
                    # 캐시가 7일 이상 오래되면 무시
                    if (datetime.now() - cache_date).days < 7:
                        self.kr_stocks_cache = data['stocks']
                        self.cache_date = cache_date
                        logger.info(f"Loaded KR stock cache from {data['date']}")
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
    
    def _save_kr_stock_cache(self, stocks: List[Dict]):
        """한국 주식 목록 캐시 저장"""
        try:
            data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'stocks': stocks
            }
            with open(self.kr_stock_cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info("Saved KR stock cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def get_stock_list(self, market: str = "ALL", date: Optional[str] = None) -> List[Dict[str, Any]]:
        """주식 목록 조회"""
        result = []
        
        try:
            if market.upper() in ["KR", "ALL"]:
                # 캐시 확인
                if not self.kr_stocks_cache:
                    self._load_kr_stock_cache()
                
                # 캐시가 없으면 새로 가져오기
                if not self.kr_stocks_cache:
                    try:
                        # KRX 전체 종목 리스트
                        df = fdr.StockListing('KRX')
                        kr_stocks = []
                        
                        for _, row in df.iterrows():
                            stock = {
                                'symbol': row['Code'],
                                'name': row['Name'],
                                'market': 'KR',
                                'display': f"{row['Name']} ({row['Code']})"
                            }
                            kr_stocks.append(stock)
                        
                        self.kr_stocks_cache = kr_stocks
                        self._save_kr_stock_cache(kr_stocks)
                        
                    except Exception as e:
                        logger.error(f"Failed to get KR stock list from FDR: {e}")
                        # 백업: 주요 종목만이라도 반환
                        kr_stocks = self._get_major_kr_stocks()
                        self.kr_stocks_cache = kr_stocks
                
                if self.kr_stocks_cache:
                    result.extend(self.kr_stocks_cache)
            
            if market.upper() in ["US", "ALL"]:
                # 미국 주요 종목 (S&P 500)
                us_stocks = self._get_major_us_stocks()
                result.extend(us_stocks)
                
        except Exception as e:
            logger.error(f"Failed to get stock list: {e}")
        
        return result
    
    def _get_major_kr_stocks(self) -> List[Dict[str, Any]]:
        """한국 주요 종목 반환 (백업용)"""
        major_stocks = [
            ('005930', '삼성전자'), ('000660', 'SK하이닉스'), ('005490', 'POSCO홀딩스'),
            ('005380', '현대차'), ('051910', 'LG화학'), ('000270', '기아'),
            ('068270', '셀트리온'), ('035420', 'NAVER'), ('003550', 'LG'),
            ('105560', 'KB금융'), ('055550', '신한지주'), ('035720', '카카오'),
            ('006400', '삼성SDI'), ('207940', '삼성바이오로직스'), ('036570', 'NCsoft'),
            ('000810', '삼성화재'), ('066970', '엘앤티'), ('009150', '삼성전기'),
            ('000100', '유한양행'), ('090430', '아모레퍼시픽')
        ]
        
        return [
            {
                'symbol': code,
                'name': name,
                'market': 'KR',
                'display': f"{name} ({code})"
            }
            for code, name in major_stocks
        ]
    
    def _get_major_us_stocks(self) -> List[Dict[str, Any]]:
        """미국 주요 종목 반환"""
        major_stocks = [
            ('AAPL', 'Apple'), ('MSFT', 'Microsoft'), ('GOOGL', 'Alphabet'),
            ('AMZN', 'Amazon'), ('NVDA', 'NVIDIA'), ('META', 'Meta'),
            ('TSLA', 'Tesla'), ('BRK-B', 'Berkshire Hathaway'), ('JPM', 'JPMorgan'),
            ('JNJ', 'Johnson & Johnson'), ('V', 'Visa'), ('PG', 'Procter & Gamble'),
            ('MA', 'Mastercard'), ('UNH', 'UnitedHealth'), ('HD', 'Home Depot'),
            ('DIS', 'Disney'), ('PYPL', 'PayPal'), ('BAC', 'Bank of America'),
            ('NFLX', 'Netflix'), ('INTC', 'Intel')
        ]
        
        return [
            {
                'symbol': code,
                'name': name,
                'market': 'US',
                'display': f"{name} ({code})"
            }
            for code, name in major_stocks
        ]
    
    def get_stock_price(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """주식 가격 데이터 조회"""
        try:
            # FinanceDataReader로 데이터 가져오기
            df = fdr.DataReader(symbol, start_date, end_date)
            
            if df.empty:
                return pd.DataFrame()
            
            # 컬럼명 정리 (FDR은 이미 영문)
            df.columns = [col.lower() for col in df.columns]
            
            # 필요한 컬럼만 선택
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            available_cols = [col for col in required_cols if col in df.columns]
            
            return df[available_cols]
            
        except Exception as e:
            logger.error(f"Failed to get stock price for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_stock_price_realtime(self, symbol: str) -> Dict[str, Any]:
        """실시간 주식 가격 조회"""
        try:
            # 최근 5일 데이터 가져오기
            end_date = datetime.now()
            start_date = end_date - timedelta(days=10)
            
            df = self.get_stock_price(symbol, 
                                    start_date.strftime('%Y-%m-%d'),
                                    end_date.strftime('%Y-%m-%d'))
            
            if df.empty:
                return {}
            
            # 최신 데이터
            latest = df.iloc[-1]
            
            # 전일 데이터 (있는 경우)
            if len(df) >= 2:
                prev = df.iloc[-2]
                change = latest['close'] - prev['close']
                change_percent = (change / prev['close'] * 100) if prev['close'] > 0 else 0
            else:
                change = 0
                change_percent = 0
            
            return {
                'symbol': symbol,
                'price': float(latest['close']),
                'change': float(change),
                'change_percent': float(change_percent),
                'volume': int(latest.get('volume', 0)),
                'date': df.index[-1].strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            logger.error(f"Failed to get realtime price for {symbol}: {e}")
            return {}
    
    def get_stock_fundamental(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """재무 데이터 조회"""
        try:
            # FinanceDataReader는 일부 재무 데이터를 제공하지 않음
            # yfinance 또는 다른 소스로 보완 필요
            logger.warning(f"Fundamental data not fully supported by FDR for {symbol}")
            
            # 빈 DataFrame 반환 (추후 구현)
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Failed to get fundamental data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_market_cap(self, symbol: str, date: Optional[str] = None) -> Dict[str, Any]:
        """시가총액 조회"""
        try:
            # 현재가 조회
            price_data = self.get_stock_price_realtime(symbol)
            if not price_data:
                return {}
            
            # 주식수는 별도 데이터 소스 필요
            # 임시로 추정값 반환
            return {
                'market_cap': 0,  # 추후 구현
                'shares': 0       # 추후 구현
            }
            
        except Exception as e:
            logger.error(f"Failed to get market cap for {symbol}: {e}")
            return {}
    
    def get_index_data(self, index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """지수 데이터 조회"""
        try:
            # 지수 코드 변환
            fdr_code = self.index_mapping.get(index_code, index_code)
            
            # FinanceDataReader로 데이터 가져오기
            df = fdr.DataReader(fdr_code, start_date, end_date)
            
            if df.empty:
                return pd.DataFrame()
            
            # 컬럼명 정리
            df.columns = [col.lower() for col in df.columns]
            
            # 필요한 컬럼만 선택
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            available_cols = [col for col in required_cols if col in df.columns]
            
            return df[available_cols]
            
        except Exception as e:
            logger.error(f"Failed to get index data for {index_code}: {e}")
            return pd.DataFrame()
    
    def get_market_overview(self, market: str = "KR", date: Optional[str] = None) -> pd.DataFrame:
        """시장 전체 데이터 조회"""
        try:
            # 주요 종목들의 현재가 정보 수집
            stocks = self.get_stock_list(market)[:50]  # 상위 50개만
            
            data = []
            for stock in stocks:
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