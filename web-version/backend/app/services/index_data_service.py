"""
주요 지수 데이터 수집 서비스
한국 및 미국 주요 지수 실시간 데이터 제공
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import yfinance as yf
from ..database.mongodb_client import get_mongodb_client
from ..data.stock_data_provider_factory import StockDataProviderFactory

logger = logging.getLogger(__name__)


class IndexDataService:
    """주요 지수 데이터 서비스"""
    
    def __init__(self):
        self._cache = {}
        self._cache_duration = 300  # 5분 캐시
        self.db = None
        
        # MongoDB 연결 시도
        try:
            self.db = get_mongodb_client()
        except Exception as e:
            logger.warning(f"MongoDB connection failed: {e}")
        
        # 데이터 제공자 초기화 (Hybrid provider 사용)
        self.data_provider = StockDataProviderFactory.get_provider('hybrid')
        
        # 지수 매핑
        self.kr_indices = {
            'KOSPI': '1001',
            'KOSDAQ': '2001',
            'KOSPI200': '1028',  # Fixed from 1002 to 1028
            'KRX100': '1003'
        }
        
        self.us_indices = {
            'S&P500': '^GSPC',
            'NASDAQ': '^IXIC',
            'DowJones': '^DJI',
            'Russell2000': '^RUT',
            'VIX': '^VIX'
        }
    
    def _is_cache_valid(self, key: str) -> bool:
        """캐시 유효성 확인"""
        if key not in self._cache:
            return False
        cache_time = self._cache[key].get('timestamp', 0)
        return (datetime.now().timestamp() - cache_time) < self._cache_duration
    
    def get_korean_indices(self) -> List[Dict]:
        """한국 주요 지수 데이터 수집"""
        
        cache_key = 'kr_indices'
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]['data']
        
        try:
            indices_data = []
            today = datetime.now().strftime('%Y-%m-%d')
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            for name, code in self.kr_indices.items():
                try:
                    # 새로운 data provider 사용하여 지수 데이터 가져오기
                    data = self.data_provider.get_index_data(code, week_ago, today)
                    
                    if not data.empty:
                        # 최신 데이터
                        current_value = float(data['close'].iloc[-1])
                        current_open = float(data['open'].iloc[-1])
                        
                        # 전일 대비 계산
                        if len(data) > 1:
                            prev_close = float(data['close'].iloc[-2])
                        else:
                            prev_close = current_open
                        
                        change = current_value - prev_close
                        change_percent = (change / prev_close * 100) if prev_close > 0 else 0
                        
                        # 거래량 정보
                        volume = int(data['volume'].iloc[-1]) if 'volume' in data.columns else 0
                        
                        index_info = {
                            'name': name,
                            'code': code,
                            'value': round(current_value, 2),
                            'change': round(change, 2),
                            'change_percent': round(change_percent, 2),
                            'volume': volume,
                            'market': 'KR',
                            'currency': 'KRW',
                            'timestamp': datetime.now().isoformat(),
                            'data_source': self.data_provider.name
                        }
                        
                        indices_data.append(index_info)
                        logger.info(f"한국 지수 {name} 데이터 수집 성공: {current_value:,.2f}")
                        
                    else:
                        logger.warning(f"한국 지수 {name} ({code}) 데이터 없음")
                        
                except Exception as e:
                    logger.error(f"한국 지수 {name} ({code}) 수집 실패: {e}")
                    continue
            
            # 캐시 저장
            self._cache[cache_key] = {
                'data': indices_data,
                'timestamp': datetime.now().timestamp()
            }
            
            logger.info(f"한국 지수 {len(indices_data)}개 수집 완료")
            return indices_data
            
        except Exception as e:
            logger.error(f"한국 지수 데이터 수집 전체 실패: {e}")
            # 실패 시 MongoDB에서 데이터 조회 시도
            mongodb_data = self._get_indices_from_mongodb('KR')
            if mongodb_data:
                self._cache[cache_key] = {
                    'data': mongodb_data,
                    'timestamp': datetime.now().timestamp()
                }
                logger.info(f"Fallback: MongoDB에서 한국 지수 {len(mongodb_data)}개 로드")
                return mongodb_data
            return []
    
    def _get_indices_from_mongodb(self, market: str) -> List[Dict]:
        """MongoDB에서 지수 데이터 가져오기"""
        if not self.db:
            return []
            
        try:
            # MongoDB에서 최신 지수 데이터 조회
            indices_data = []
            
            if market == 'US':
                indices_map = self.us_indices
            else:
                indices_map = self.kr_indices
                
            for name, code in indices_map.items():
                # 가장 최신 데이터 1개만 조회
                index_data = self.db.db.market_indices.find_one(
                    {'code': code},
                    sort=[('date', -1)]
                )
                
                if index_data:
                    indices_data.append({
                        'name': name,
                        'code': code,
                        'symbol': code,  # Add symbol field for compatibility
                        'value': round(index_data.get('close', 0), 2),
                        'change': round(index_data.get('change', 0), 2),
                        'change_percent': round(index_data.get('change_percent', 0), 2),
                        'volume': index_data.get('volume', 0),
                        'market': market,
                        'currency': 'USD' if market == 'US' else 'KRW',
                        'timestamp': index_data.get('date', ''),
                        'data_source': 'mongodb',
                        'data_date': index_data.get('date', '').split('T')[0] if index_data.get('date') else ''
                    })
            
            return indices_data
            
        except Exception as e:
            logger.error(f"MongoDB에서 {market} 지수 데이터 조회 실패: {e}")
            return []
    
    def get_us_indices(self) -> List[Dict]:
        """미국 주요 지수 데이터 수집"""
        
        cache_key = 'us_indices'
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]['data']
        
        try:
            indices_data = []
            
            for name, symbol in self.us_indices.items():
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period='2d')  # 2일 데이터로 전일 대비 계산
                    
                    if not hist.empty:
                        current_value = float(hist['Close'].iloc[-1])
                        
                        # 전일 대비 계산
                        if len(hist) > 1:
                            prev_close = float(hist['Close'].iloc[-2])
                        else:
                            prev_close = float(hist['Open'].iloc[-1])
                        
                        change = current_value - prev_close
                        change_percent = (change / prev_close * 100) if prev_close > 0 else 0
                        
                        # 거래량
                        volume = int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else 0
                        
                        index_info = {
                            'name': name,
                            'code': symbol,
                            'value': round(current_value, 2),
                            'change': round(change, 2),
                            'change_percent': round(change_percent, 2),
                            'volume': volume,
                            'market': 'US',
                            'currency': 'USD',
                            'timestamp': datetime.now().isoformat(),
                            'data_source': 'yfinance'
                        }
                        
                        indices_data.append(index_info)
                        logger.info(f"미국 지수 {name} 데이터 수집 성공: {current_value:,.2f}")
                        
                    else:
                        logger.warning(f"미국 지수 {name} ({symbol}) 데이터 없음")
                        
                except Exception as e:
                    logger.error(f"미국 지수 {name} ({symbol}) 수집 실패: {e}")
                    continue
            
            # 캐시 저장
            self._cache[cache_key] = {
                'data': indices_data,
                'timestamp': datetime.now().timestamp()
            }
            
            logger.info(f"미국 지수 {len(indices_data)}개 수집 완료")
            return indices_data
            
        except Exception as e:
            logger.error(f"미국 지수 데이터 수집 전체 실패: {e}")
            # 실패 시 MongoDB에서 데이터 조회 시도
            mongodb_data = self._get_indices_from_mongodb('US')
            if mongodb_data:
                self._cache[cache_key] = {
                    'data': mongodb_data,
                    'timestamp': datetime.now().timestamp()
                }
                logger.info(f"Fallback: MongoDB에서 미국 지수 {len(mongodb_data)}개 로드")
                return mongodb_data
            return []
    
    def get_all_indices(self) -> Dict[str, List[Dict]]:
        """전체 지수 데이터 수집"""
        
        try:
            kr_indices = self.get_korean_indices()
            us_indices = self.get_us_indices()
            
            return {
                'korean_indices': kr_indices,
                'us_indices': us_indices,
                'total_count': len(kr_indices) + len(us_indices),
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"전체 지수 데이터 수집 실패: {e}")
            return {
                'korean_indices': [],
                'us_indices': [],
                'total_count': 0,
                'last_updated': datetime.now().isoformat(),
                'error': 'Failed to fetch index data'
            }
    
    def get_index_data(self, symbol: str, market: str = 'auto') -> Optional[Dict]:
        """개별 지수 데이터 조회"""
        
        try:
            if market.upper() == 'KR' or symbol in self.kr_indices.values():
                indices = self.get_korean_indices()
                for index in indices:
                    if index['code'] == symbol or index['name'] == symbol:
                        return index
            else:
                indices = self.get_us_indices()
                for index in indices:
                    if index['code'] == symbol or index['name'] == symbol:
                        return index
            
            return None
            
        except Exception as e:
            logger.error(f"지수 {symbol} 데이터 조회 실패: {e}")
            return None
    


# 전역 서비스 인스턴스
index_service = IndexDataService()