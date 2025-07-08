"""
Stock Data Collector V3
새로운 데이터 제공자를 사용하는 주식 데이터 수집기
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time
import pytz
import pandas as pd
from ..database.mongodb_client import get_mongodb_client
from ..data.stock_data_provider_factory import StockDataProviderFactory
from ..services.real_financial_data import real_financial_service
from .us_stock_list import USStockListFetcher

logger = logging.getLogger(__name__)


class StockDataCollectorV3:
    """새로운 데이터 제공자를 사용하는 주식 데이터 수집기"""
    
    def __init__(self):
        self.db = get_mongodb_client()
        self.kr_provider = StockDataProviderFactory.get_provider('fdr')
        self.us_provider = StockDataProviderFactory.get_provider('yahoo')
        self.hybrid_provider = StockDataProviderFactory.get_provider('hybrid')
        self.kr_tz = pytz.timezone('Asia/Seoul')
        self.us_tz = pytz.timezone('America/New_York')
        
        # Rate limiting 설정
        self.rate_limit_delay = 0.5  # 0.5초 딜레이
        
    def collect_kr_stock_list(self):
        """한국 주식 목록 수집 및 MongoDB 업데이트"""
        logger.info("Collecting Korean stock list using new provider...")
        
        try:
            # MongoDB에서 기존 목록 가져오기 (이미 2,740개가 있음)
            existing_stocks = list(self.db.db.stock_list.find({"market": "KR"}))
            logger.info(f"Found {len(existing_stocks)} existing Korean stocks in MongoDB")
            
            # 기존 데이터가 충분하면 그대로 사용
            if len(existing_stocks) > 2000:
                logger.info("Using existing Korean stock list from MongoDB")
                return
            
            # 새로운 목록 가져오기 시도
            try:
                kr_stocks = self.kr_provider.get_stock_list(market="KR")
                logger.info(f"Retrieved {len(kr_stocks)} Korean stocks from provider")
                
                # MongoDB에 업데이트
                for stock in kr_stocks:
                    stock_doc = {
                        "_id": stock['symbol'],
                        "symbol": stock['symbol'],
                        "name": stock['name'],
                        "market": "KR",
                        "exchange": "KRX",  # KOSPI/KOSDAQ 구분은 추후 개선
                        "is_active": True,
                        "updated_at": datetime.now().isoformat()
                    }
                    self.db.db.stock_list.update_one(
                        {"_id": stock['symbol']},
                        {"$set": stock_doc},
                        upsert=True
                    )
                
            except Exception as e:
                logger.error(f"Failed to get stock list from provider: {e}")
                # MongoDB의 기존 데이터 사용
                
        except Exception as e:
            logger.error(f"Error in collect_kr_stock_list: {e}")
    
    def collect_us_stock_list(self, symbols: Optional[List[str]] = None):
        """미국 주식 목록 수집"""
        if not symbols:
            logger.info("Fetching comprehensive US stock list...")
            stocks = USStockListFetcher.get_all_us_stocks()
            symbols = [stock['symbol'] for stock in stocks]
            logger.info(f"Found {len(symbols)} US stocks to collect")
        else:
            logger.info(f"Collecting US stock list for {len(symbols)} provided symbols...")
        
        # Get stock info in batches
        stock_info_dict = USStockListFetcher.get_stock_info_batch(symbols)
        
        for symbol in symbols:
            try:
                if symbol in stock_info_dict:
                    info = stock_info_dict[symbol]
                    stock_doc = {
                        "_id": symbol,
                        "symbol": symbol,
                        "name": info['name'],
                        "market": "US",
                        "exchange": info['exchange'],
                        "sector": info['sector'],
                        "industry": info['industry'],
                        "is_active": True,
                        "updated_at": datetime.now().isoformat()
                    }
                    self.db.db.stock_list.update_one(
                        {"_id": symbol},
                        {"$set": stock_doc},
                        upsert=True
                    )
            except Exception as e:
                logger.error(f"Error collecting US stock {symbol}: {e}")
        
        logger.info(f"Collected {len(symbols)} US stocks")
    
    def collect_historical_prices(self, symbol: str, start_date: str, end_date: str, market: str = "KR"):
        """특정 종목의 과거 가격 데이터 수집"""
        try:
            provider = self.hybrid_provider if market == "KR" else self.us_provider
            
            # 데이터 가져오기
            df = provider.get_stock_price(symbol, start_date, end_date)
            
            if df.empty:
                logger.warning(f"No price data for {symbol} from {start_date} to {end_date}")
                return 0
            
            # MongoDB에 저장
            count = 0
            for date, row in df.iterrows():
                try:
                    # 날짜 포맷 맞추기
                    date_str = date.strftime('%Y-%m-%d')
                    
                    price_doc = {
                        "_id": f"{symbol}_{date_str}",
                        "symbol": symbol,
                        "date": date_str,
                        "open": float(row.get('open', 0)),
                        "high": float(row.get('high', 0)),
                        "low": float(row.get('low', 0)),
                        "close": float(row.get('close', 0)),
                        "volume": int(row.get('volume', 0)),
                        "market": market,
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    # 전일 대비 계산
                    if count > 0:
                        prev_close = float(df.iloc[count-1]['close'])
                        price_doc['change'] = price_doc['close'] - prev_close
                        price_doc['change_percent'] = (price_doc['change'] / prev_close * 100) if prev_close > 0 else 0
                    
                    self.db.db.stock_price_daily.update_one(
                        {"_id": price_doc["_id"]},
                        {"$set": price_doc},
                        upsert=True
                    )
                    count += 1
                    
                except Exception as e:
                    logger.error(f"Error saving price data for {symbol} on {date}: {e}")
            
            # Rate limiting
            time.sleep(self.rate_limit_delay)
            
            logger.info(f"Collected {count} price records for {symbol}")
            return count
            
        except Exception as e:
            logger.error(f"Error collecting historical prices for {symbol}: {e}")
            return 0
    
    def collect_all_historical_prices(self, market: str = "KR", start_date: str = None, end_date: str = None, limit: int = None):
        """모든 종목의 과거 가격 데이터 수집"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Collecting historical prices for {market} market from {start_date} to {end_date}")
        
        # 종목 목록 가져오기
        stocks = list(self.db.db.stock_list.find({"market": market, "is_active": True}))
        if limit:
            stocks = stocks[:limit]
        
        logger.info(f"Found {len(stocks)} stocks to collect")
        
        total_count = 0
        for idx, stock in enumerate(stocks):
            symbol = stock['symbol']
            logger.info(f"[{idx+1}/{len(stocks)}] Collecting {symbol} - {stock.get('name', '')}")
            
            count = self.collect_historical_prices(symbol, start_date, end_date, market)
            total_count += count
            
            # Progress logging
            if (idx + 1) % 10 == 0:
                logger.info(f"Progress: {idx+1}/{len(stocks)} stocks processed, {total_count} records collected")
        
        logger.info(f"Completed collecting historical prices. Total records: {total_count}")
        return total_count
    
    def collect_financial_data(self, symbol: str, market: str = "KR"):
        """재무 데이터 수집"""
        try:
            # real_financial_service 사용
            financial_data = real_financial_service.get_financial_data(symbol, market)
            
            if financial_data:
                # MongoDB에 저장
                financial_doc = {
                    "_id": f"{symbol}_{datetime.now().strftime('%Y-%m-%d')}",
                    "symbol": symbol,
                    "date": datetime.now().strftime('%Y-%m-%d'),
                    "market": market,
                    "market_cap": financial_data.get('market_cap'),
                    "shares": financial_data.get('shares_outstanding'),
                    "per": financial_data.get('per'),
                    "pbr": financial_data.get('pbr'),
                    "eps": financial_data.get('eps'),
                    "bps": financial_data.get('bps'),
                    "roe": financial_data.get('roe'),
                    "roa": financial_data.get('roa'),
                    "debt_ratio": financial_data.get('debt_ratio'),
                    "data_source": financial_data.get('data_source'),
                    "updated_at": datetime.now().isoformat()
                }
                
                self.db.db.stock_financial.update_one(
                    {"_id": financial_doc["_id"]},
                    {"$set": financial_doc},
                    upsert=True
                )
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                
                logger.info(f"Collected financial data for {symbol}")
                return True
            
        except Exception as e:
            logger.error(f"Error collecting financial data for {symbol}: {e}")
            return False
    
    def collect_all_financial_data(self, market: str = "KR", limit: int = None):
        """모든 종목의 재무 데이터 수집"""
        logger.info(f"Collecting financial data for {market} market")
        
        # 종목 목록 가져오기
        stocks = list(self.db.db.stock_list.find({"market": market, "is_active": True}))
        if limit:
            stocks = stocks[:limit]
        
        logger.info(f"Found {len(stocks)} stocks to collect")
        
        success_count = 0
        for idx, stock in enumerate(stocks):
            symbol = stock['symbol']
            logger.info(f"[{idx+1}/{len(stocks)}] Collecting financial data for {symbol} - {stock.get('name', '')}")
            
            if self.collect_financial_data(symbol, market):
                success_count += 1
            
            # Progress logging
            if (idx + 1) % 10 == 0:
                logger.info(f"Progress: {idx+1}/{len(stocks)} stocks processed, {success_count} successful")
        
        logger.info(f"Completed collecting financial data. Success: {success_count}/{len(stocks)}")
        return success_count
    
    def collect_daily_data(self, market: str = "KR"):
        """일일 데이터 수집 (가격, 재무)"""
        today = datetime.now()
        
        # 주말/공휴일 체크
        if market == "KR" and today.weekday() in [5, 6]:  # 토요일, 일요일
            logger.info("Weekend - skipping Korean market data collection")
            return
        elif market == "US" and today.weekday() in [5, 6]:
            logger.info("Weekend - skipping US market data collection")
            return
        
        logger.info(f"Starting daily data collection for {market} market")
        
        # 종목 목록 가져오기
        stocks = list(self.db.db.stock_list.find({"market": market, "is_active": True}))
        logger.info(f"Found {len(stocks)} stocks to update")
        
        date_str = today.strftime('%Y-%m-%d')
        price_count = 0
        financial_count = 0
        
        for idx, stock in enumerate(stocks):
            symbol = stock['symbol']
            
            try:
                # 가격 데이터 수집
                provider = self.hybrid_provider if market == "KR" else self.us_provider
                realtime_data = provider.get_stock_price_realtime(symbol)
                
                if realtime_data and 'price' in realtime_data:
                    price_doc = {
                        "_id": f"{symbol}_{date_str}",
                        "symbol": symbol,
                        "date": date_str,
                        "close": realtime_data['price'],
                        "change": realtime_data.get('change', 0),
                        "change_percent": realtime_data.get('change_percent', 0),
                        "volume": realtime_data.get('volume', 0),
                        "market": market,
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    self.db.db.stock_price_daily.update_one(
                        {"_id": price_doc["_id"]},
                        {"$set": price_doc},
                        upsert=True
                    )
                    price_count += 1
                
                # 재무 데이터는 주 1회 정도만 업데이트
                if today.weekday() == 0:  # 월요일
                    if self.collect_financial_data(symbol, market):
                        financial_count += 1
                
                # Progress logging
                if (idx + 1) % 100 == 0:
                    logger.info(f"Progress: {idx+1}/{len(stocks)} stocks processed")
                    
                # Rate limiting
                time.sleep(0.1)  # 더 짧은 딜레이
                
            except Exception as e:
                logger.error(f"Error collecting daily data for {symbol}: {e}")
        
        logger.info(f"Daily collection completed. Prices: {price_count}, Financial: {financial_count}")
        return {"prices": price_count, "financial": financial_count}


# 전역 인스턴스
collector_v3 = StockDataCollectorV3()