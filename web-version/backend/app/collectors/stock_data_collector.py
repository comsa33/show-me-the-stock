"""
Stock Data Collector
Collects stock data from external sources and stores in MongoDB
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pytz
from pykrx import stock as pykrx_stock
from pykrx import stock
import yfinance as yf
import pandas as pd
from ..database.mongodb_client import get_mongodb_client
from ..services.real_financial_data import RealFinancialDataService
from .us_stock_list import USStockListFetcher

logger = logging.getLogger(__name__)


class StockDataCollector:
    """Collects stock data from various sources and stores in MongoDB"""
    
    def __init__(self):
        self.db = get_mongodb_client()
        self.financial_service = RealFinancialDataService()
        self.kr_tz = pytz.timezone('Asia/Seoul')
        self.us_tz = pytz.timezone('America/New_York')
    
    def collect_kr_stock_list(self):
        """Collect Korean stock list and update in MongoDB"""
        logger.info("Collecting Korean stock list...")
        
        # Collect KOSPI stocks
        kospi_tickers = pykrx_stock.get_market_ticker_list(market="KOSPI")
        for ticker in kospi_tickers:
            name = pykrx_stock.get_market_ticker_name(ticker)
            stock_doc = {
                "_id": ticker,
                "symbol": ticker,
                "name": name,
                "market": "KR",
                "exchange": "KOSPI",
                "is_active": True,
                "updated_at": datetime.now().isoformat()
            }
            self.db.db.stock_list.update_one(
                {"_id": ticker},
                {"$set": stock_doc},
                upsert=True
            )
        
        # Collect KOSDAQ stocks
        kosdaq_tickers = pykrx_stock.get_market_ticker_list(market="KOSDAQ")
        for ticker in kosdaq_tickers:
            name = pykrx_stock.get_market_ticker_name(ticker)
            stock_doc = {
                "_id": ticker,
                "symbol": ticker,
                "name": name,
                "market": "KR",
                "exchange": "KOSDAQ",
                "is_active": True,
                "updated_at": datetime.now().isoformat()
            }
            self.db.db.stock_list.update_one(
                {"_id": ticker},
                {"$set": stock_doc},
                upsert=True
            )
        
        logger.info(f"Collected {len(kospi_tickers)} KOSPI and {len(kosdaq_tickers)} KOSDAQ stocks")
    
    def collect_us_stock_list(self, symbols: Optional[List[str]] = None):
        """Collect US stock list - if no symbols provided, fetch comprehensive list"""
        if not symbols:
            logger.info("No symbols provided, fetching comprehensive US stock list...")
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
                else:
                    # Fallback for symbols not in batch info
                    stock_doc = {
                        "_id": symbol,
                        "symbol": symbol,
                        "name": symbol,
                        "market": "US",
                        "exchange": "NASDAQ",
                        "sector": "",
                        "industry": "",
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
        
        logger.info(f"Completed collecting {len(symbols)} US stocks")
    
    def collect_kr_daily_prices(self, date: Optional[str] = None):
        """Collect Korean stock daily prices"""
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        else:
            date = date.replace("-", "")
        
        logger.info(f"Collecting Korean stock prices for {date}")
        
        # Get all Korean stocks
        kr_stocks = self.db.get_stock_list(market="KR")
        
        for stock in kr_stocks:
            try:
                symbol = stock["symbol"]
                # Get OHLCV data
                df = pykrx_stock.get_market_ohlcv_by_date(date, date, symbol)
                if df.empty:
                    continue
                
                row = df.iloc[0]
                formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                
                # Calculate change
                prev_close = row.get('시가', row['종가'])
                change = row['종가'] - prev_close
                change_percent = (change / prev_close * 100) if prev_close != 0 else 0
                
                price_doc = {
                    "_id": f"{symbol}_{formatted_date}",
                    "symbol": symbol,
                    "date": formatted_date,
                    "open": float(row['시가']),
                    "high": float(row['고가']),
                    "low": float(row['저가']),
                    "close": float(row['종가']),
                    "volume": int(row['거래량']),
                    "change": float(change),
                    "change_percent": float(change_percent),
                    "market": "KR",
                    "updated_at": datetime.now().isoformat()
                }
                
                self.db.db.stock_price_daily.update_one(
                    {"_id": price_doc["_id"]},
                    {"$set": price_doc},
                    upsert=True
                )
                
                # Update realtime snapshot
                realtime_doc = {
                    "_id": symbol,
                    "symbol": symbol,
                    "name": stock["name"],
                    "market": "KR",
                    "exchange": stock["exchange"],
                    "current_price": float(row['종가']),
                    "prev_close": float(prev_close),
                    "open": float(row['시가']),
                    "high": float(row['고가']),
                    "low": float(row['저가']),
                    "volume": int(row['거래량']),
                    "change": float(change),
                    "change_percent": float(change_percent),
                    "last_updated": datetime.now().isoformat(),
                    "trading_status": "closed"
                }
                
                # Add financial metrics
                financial = self.financial_service.get_financial_data(symbol, "KR")
                if financial:
                    realtime_doc.update({
                        "market_cap": financial.get("market_cap", 0),
                        "per": financial.get("per"),
                        "pbr": financial.get("pbr"),
                        "dividend_yield": financial.get("dividend_yield")
                    })
                
                self.db.db.stock_realtime.update_one(
                    {"_id": symbol},
                    {"$set": realtime_doc},
                    upsert=True
                )
                
            except Exception as e:
                logger.error(f"Error collecting KR price for {symbol}: {e}")
        
        logger.info("Korean daily price collection completed")
    
    def collect_us_daily_prices(self, symbols: List[str], date: Optional[str] = None):
        """Collect US stock daily prices"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Collecting US stock prices for {date}")
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                # Get 2 days of data to ensure we get the date we want
                hist = ticker.history(period="2d")
                
                if hist.empty:
                    continue
                
                # Get data for specific date
                if date in hist.index.strftime("%Y-%m-%d"):
                    idx = hist.index.strftime("%Y-%m-%d") == date
                    row = hist[idx].iloc[0]
                else:
                    # Use most recent data
                    row = hist.iloc[-1]
                    date = hist.index[-1].strftime("%Y-%m-%d")
                
                # Calculate change
                if len(hist) > 1:
                    prev_close = hist.iloc[-2]['Close']
                else:
                    prev_close = row['Open']
                
                change = row['Close'] - prev_close
                change_percent = (change / prev_close * 100) if prev_close != 0 else 0
                
                price_doc = {
                    "_id": f"{symbol}_{date}",
                    "symbol": symbol,
                    "date": date,
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume']),
                    "change": float(change),
                    "change_percent": float(change_percent),
                    "market": "US",
                    "updated_at": datetime.now().isoformat()
                }
                
                self.db.db.stock_price_daily.update_one(
                    {"_id": price_doc["_id"]},
                    {"$set": price_doc},
                    upsert=True
                )
                
                # Get stock info for realtime
                info = ticker.info
                
                # Update realtime snapshot
                realtime_doc = {
                    "_id": symbol,
                    "symbol": symbol,
                    "name": info.get("longName", info.get("shortName", symbol)),
                    "market": "US",
                    "exchange": info.get("exchange", "NASDAQ"),
                    "current_price": float(row['Close']),
                    "prev_close": float(prev_close),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "volume": int(row['Volume']),
                    "change": float(change),
                    "change_percent": float(change_percent),
                    "market_cap": info.get("marketCap", 0),
                    "per": info.get("trailingPE"),
                    "pbr": info.get("priceToBook"),
                    "dividend_yield": info.get("dividendYield"),
                    "last_updated": datetime.now().isoformat(),
                    "trading_status": "closed"
                }
                
                self.db.db.stock_realtime.update_one(
                    {"_id": symbol},
                    {"$set": realtime_doc},
                    upsert=True
                )
                
                # Also collect financial data for this date
                self._collect_us_financial_for_date(symbol, ticker, date)
                
            except Exception as e:
                logger.error(f"Error collecting US price for {symbol}: {e}")
        
        logger.info("US daily price collection completed")
    
    def collect_kr_financial_data(self, date: Optional[str] = None):
        """Collect Korean stock financial data"""
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        else:
            date = date.replace("-", "")
        
        logger.info(f"Collecting Korean financial data for {date}")
        
        kr_stocks = self.db.get_stock_list(market="KR")
        
        for stock in kr_stocks:
            try:
                symbol = stock["symbol"]
                financial = self.financial_service.get_financial_data(symbol, "KR")
                
                if financial:
                    formatted_date = f"{date[:4]}-{date[4:6]}-{date[6:]}"
                    
                    financial_doc = {
                        "_id": f"{symbol}_{formatted_date}",
                        "symbol": symbol,
                        "date": formatted_date,
                        "market_cap": financial.get("market_cap", 0),
                        "shares_outstanding": financial.get("shares_outstanding", 0),
                        "per": financial.get("per"),
                        "pbr": financial.get("pbr"),
                        "eps": financial.get("eps"),
                        "bps": financial.get("bps"),
                        "roe": financial.get("roe"),
                        "roa": financial.get("roa"),
                        "dividend_yield": financial.get("dividend_yield"),
                        "market": "KR",
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    self.db.db.stock_financial.update_one(
                        {"_id": financial_doc["_id"]},
                        {"$set": financial_doc},
                        upsert=True
                    )
                
            except Exception as e:
                logger.error(f"Error collecting financial data for {symbol}: {e}")
        
        logger.info("Korean financial data collection completed")
    
    def collect_us_financial_data(self, symbols: Optional[List[str]] = None, date: Optional[str] = None):
        """Collect US stock financial data"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Collecting US financial data for {date}")
        
        # If no symbols provided, get from database
        if not symbols:
            us_stocks = self.db.get_stock_list(market="US")
            symbols = [stock["symbol"] for stock in us_stocks]
            
            if not symbols:
                logger.warning("No US stocks found in database")
                return
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                # Get quarterly financials for more accurate data
                quarterly_financials = ticker.quarterly_financials
                quarterly_balance_sheet = ticker.quarterly_balance_sheet
                
                # Calculate financial metrics
                market_cap = info.get("marketCap", 0)
                shares_outstanding = info.get("sharesOutstanding", 0)
                
                # Get trailing 12 months data
                per = info.get("trailingPE")
                forward_per = info.get("forwardPE")
                pbr = info.get("priceToBook")
                eps = info.get("trailingEps")
                
                # Calculate BPS (Book Value Per Share)
                bps = None
                if shares_outstanding and not quarterly_balance_sheet.empty:
                    try:
                        total_equity = quarterly_balance_sheet.loc["Total Stockholder Equity"].iloc[0]
                        bps = float(total_equity / shares_outstanding)
                    except:
                        pass
                
                # Get profitability metrics
                roe = info.get("returnOnEquity")
                if roe:
                    roe = roe * 100  # Convert to percentage
                
                roa = info.get("returnOnAssets")
                if roa:
                    roa = roa * 100  # Convert to percentage
                
                # Get dividend data
                dividend_yield = info.get("dividendYield")
                if dividend_yield:
                    dividend_yield = dividend_yield * 100  # Convert to percentage
                
                # Additional metrics
                gross_margin = info.get("grossMargins")
                if gross_margin:
                    gross_margin = gross_margin * 100
                
                operating_margin = info.get("operatingMargins")
                if operating_margin:
                    operating_margin = operating_margin * 100
                
                profit_margin = info.get("profitMargins")
                if profit_margin:
                    profit_margin = profit_margin * 100
                
                financial_doc = {
                    "_id": f"{symbol}_{date}",
                    "symbol": symbol,
                    "date": date,
                    "market_cap": int(market_cap) if market_cap else 0,
                    "shares_outstanding": int(shares_outstanding) if shares_outstanding else 0,
                    "per": float(per) if per else None,
                    "forward_per": float(forward_per) if forward_per else None,
                    "pbr": float(pbr) if pbr else None,
                    "eps": float(eps) if eps else None,
                    "bps": float(bps) if bps else None,
                    "roe": float(roe) if roe else None,
                    "roa": float(roa) if roa else None,
                    "dividend_yield": float(dividend_yield) if dividend_yield else None,
                    "gross_margin": float(gross_margin) if gross_margin else None,
                    "operating_margin": float(operating_margin) if operating_margin else None,
                    "profit_margin": float(profit_margin) if profit_margin else None,
                    "market": "US",
                    "updated_at": datetime.now().isoformat()
                }
                
                self.db.db.stock_financial.update_one(
                    {"_id": financial_doc["_id"]},
                    {"$set": financial_doc},
                    upsert=True
                )
                
            except Exception as e:
                logger.error(f"Error collecting financial data for {symbol}: {e}")
        
        logger.info("US financial data collection completed")
    
    def collect_us_financial_data_range(self, symbols: List[str], start_date: str, end_date: str, 
                                      interval_days: int = 30):
        """
        Collect US financial data for a date range with intervals
        Since yfinance doesn't provide historical fundamentals, we store data at intervals
        This is more efficient than storing identical data for every single day
        
        Args:
            symbols: List of stock symbols
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval_days: Days between financial data points (default: 30)
        """
        logger.info(f"Collecting US financial data for {len(symbols)} symbols from {start_date} to {end_date} with {interval_days} day intervals")
        
        # Generate dates at intervals
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        current_date = start
        
        dates = []
        while current_date <= end:
            dates.append(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=interval_days)
        
        # Always include the end date
        if dates[-1] != end_date:
            dates.append(end_date)
        
        logger.info(f"Will store financial data for {len(dates)} dates: {dates}")
        
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                if not info:
                    logger.warning(f"No info available for {symbol}")
                    continue
                
                # Collect financial data for each interval date
                for date in dates:
                    self._collect_us_financial_for_date(symbol, ticker, date)
                    
            except Exception as e:
                logger.error(f"Error collecting financial data range for {symbol}: {e}")
        
        logger.info(f"US financial data range collection completed for {len(symbols)} symbols")
    
    def _collect_us_financial_for_date(self, symbol: str, ticker: yf.Ticker, date: str):
        """Helper method to collect US financial data for a specific date"""
        try:
            info = ticker.info
            
            # For historical data, we use the current financial metrics
            # as yfinance doesn't provide historical fundamental data easily
            financial_doc = {
                "_id": f"{symbol}_{date}",
                "symbol": symbol,
                "date": date,
                "market_cap": info.get("marketCap", 0),
                "shares_outstanding": info.get("sharesOutstanding", 0),
                "per": info.get("trailingPE"),
                "pbr": info.get("priceToBook"),
                "eps": info.get("trailingEps"),
                "bps": None,  # Will calculate if possible
                "roe": info.get("returnOnEquity", 0) * 100 if info.get("returnOnEquity") else None,
                "roa": info.get("returnOnAssets", 0) * 100 if info.get("returnOnAssets") else None,
                "dividend_yield": info.get("dividendYield", 0) * 100 if info.get("dividendYield") else None,
                "market": "US",
                "updated_at": datetime.now().isoformat()
            }
            
            self.db.db.stock_financial.update_one(
                {"_id": financial_doc["_id"]},
                {"$set": financial_doc},
                upsert=True
            )
            
        except Exception as e:
            logger.debug(f"Could not collect financial data for {symbol} on {date}: {e}")
    
    def collect_indices_data(self, date: Optional[str] = None):
        """Collect market indices data"""
        if not date:
            date_kr = datetime.now().strftime("%Y%m%d")
            date_us = datetime.now().strftime("%Y-%m-%d")
        else:
            date_kr = date.replace("-", "")
            date_us = date
        
        logger.info(f"Collecting indices data for {date}")
        
        # Korean indices
        kr_indices = {
            "KOSPI": "1001",
            "KOSDAQ": "2001",
            "KOSPI200": "1028",
            "KRX100": "1035"
        }
        
        for name, code in kr_indices.items():
            try:
                df = pykrx_stock.get_index_ohlcv_by_date(date_kr, date_kr, code)
                if not df.empty:
                    row = df.iloc[0]
                    formatted_date = f"{date_kr[:4]}-{date_kr[4:6]}-{date_kr[6:]}"
                    
                    # Calculate change
                    prev_close = row.get('시가', row['종가'])
                    change = row['종가'] - prev_close
                    change_percent = (change / prev_close * 100) if prev_close != 0 else 0
                    
                    index_doc = {
                        "_id": f"{code}_{formatted_date}",
                        "code": code,
                        "name": name,
                        "date": formatted_date,
                        "open": float(row['시가']),
                        "high": float(row['고가']),
                        "low": float(row['저가']),
                        "close": float(row['종가']),
                        "volume": int(row.get('거래량', 0)),
                        "change": float(change),
                        "change_percent": float(change_percent),
                        "market": "KR",
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    self.db.db.market_indices.update_one(
                        {"_id": index_doc["_id"]},
                        {"$set": index_doc},
                        upsert=True
                    )
                    
            except Exception as e:
                logger.error(f"Error collecting Korean index {name}: {e}")
        
        # US indices
        us_indices = {
            "S&P500": "^GSPC",
            "NASDAQ": "^IXIC",
            "DowJones": "^DJI",
            "Russell2000": "^RUT",
            "VIX": "^VIX"
        }
        
        for name, code in us_indices.items():
            try:
                ticker = yf.Ticker(code)
                hist = ticker.history(period="2d")
                
                if not hist.empty:
                    row = hist.iloc[-1]
                    date_str = hist.index[-1].strftime("%Y-%m-%d")
                    
                    # Calculate change
                    if len(hist) > 1:
                        prev_close = hist.iloc[-2]['Close']
                    else:
                        prev_close = row['Open']
                    
                    change = row['Close'] - prev_close
                    change_percent = (change / prev_close * 100) if prev_close != 0 else 0
                    
                    index_doc = {
                        "_id": f"{code}_{date_str}",
                        "code": code,
                        "name": name,
                        "date": date_str,
                        "open": float(row['Open']),
                        "high": float(row['High']),
                        "low": float(row['Low']),
                        "close": float(row['Close']),
                        "volume": int(row['Volume']),
                        "change": float(change),
                        "change_percent": float(change_percent),
                        "market": "US",
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    self.db.db.market_indices.update_one(
                        {"_id": index_doc["_id"]},
                        {"$set": index_doc},
                        upsert=True
                    )
                    
            except Exception as e:
                logger.error(f"Error collecting US index {name}: {e}")
        
        logger.info("Indices data collection completed")
    
    def collect_historical_data(self, symbol: str, market: str, 
                              start_date: str, end_date: str):
        """Collect historical data for a single stock"""
        logger.info(f"Collecting historical data for {symbol} from {start_date} to {end_date}")
        
        try:
            if market == "KR":
                # Convert dates to pykrx format
                start = start_date.replace("-", "")
                end = end_date.replace("-", "")
                
                # Get price data
                df = pykrx_stock.get_market_ohlcv_by_date(start, end, symbol)
                
                for date_idx, row in df.iterrows():
                    date_str = date_idx.strftime("%Y-%m-%d")
                    
                    # Calculate change
                    # pykrx columns may vary, so check what's available
                    close_price = float(row['종가'])
                    open_price = float(row['시가'])
                    
                    # Calculate change from previous close (we'll update this later)
                    change = close_price - open_price  # Simplified for now
                    change_percent = (change / open_price * 100) if open_price > 0 else 0
                    
                    # Try to get actual change data if available
                    if '변동폭' in row.index:
                        change = float(row['변동폭'])
                    elif '전일비' in row.index:
                        change = float(row['전일비'])
                    
                    if '등락률' in row.index:
                        change_percent = float(row['등락률'])
                    elif '변동률' in row.index:
                        change_percent = float(row['변동률'])
                    
                    price_doc = {
                        "_id": f"{symbol}_{date_str}",
                        "symbol": symbol,
                        "date": date_str,
                        "open": float(row['시가']),
                        "high": float(row['고가']),
                        "low": float(row['저가']),
                        "close": float(row['종가']),
                        "volume": int(row['거래량']),
                        "change": change,
                        "change_percent": change_percent,
                        "market": "KR",
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    self.db.db.stock_price_daily.update_one(
                        {"_id": price_doc["_id"]},
                        {"$set": price_doc},
                        upsert=True
                    )
                
                # Get financial data for the period
                fundamentals = pykrx_stock.get_market_fundamental_by_date(start, end, symbol)
                
                for date_idx, row in fundamentals.iterrows():
                    date_str = date_idx.strftime("%Y-%m-%d")
                    
                    # Get market cap
                    cap_df = pykrx_stock.get_market_cap_by_date(
                        date_idx.strftime("%Y%m%d"), 
                        date_idx.strftime("%Y%m%d"), 
                        symbol
                    )
                    
                    market_cap = 0
                    shares = 0
                    if not cap_df.empty:
                        market_cap = cap_df.iloc[0]['시가총액']
                        shares = cap_df.iloc[0]['상장주식수']
                    
                    financial_doc = {
                        "_id": f"{symbol}_{date_str}",
                        "symbol": symbol,
                        "date": date_str,
                        "market_cap": int(market_cap),
                        "shares_outstanding": int(shares),
                        "per": float(row['PER']) if row['PER'] > 0 else None,
                        "pbr": float(row['PBR']) if row['PBR'] > 0 else None,
                        "eps": float(row['EPS']) if row['EPS'] > 0 else None,
                        "bps": float(row['BPS']) if row['BPS'] > 0 else None,
                        "dividend_yield": float(row['DIV']) if row['DIV'] > 0 else None,
                        "market": "KR",
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    self.db.db.stock_financial.update_one(
                        {"_id": financial_doc["_id"]},
                        {"$set": financial_doc},
                        upsert=True
                    )
                    
            else:  # US market
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date, end=end_date)
                
                for date_idx, row in hist.iterrows():
                    date_str = date_idx.strftime("%Y-%m-%d")
                    
                    # Calculate change
                    if date_idx > hist.index[0]:
                        prev_idx = hist.index[hist.index < date_idx][-1]
                        prev_close = hist.loc[prev_idx, 'Close']
                    else:
                        prev_close = row['Open']
                    
                    change = row['Close'] - prev_close
                    change_percent = (change / prev_close * 100) if prev_close != 0 else 0
                    
                    price_doc = {
                        "_id": f"{symbol}_{date_str}",
                        "symbol": symbol,
                        "date": date_str,
                        "open": float(row['Open']),
                        "high": float(row['High']),
                        "low": float(row['Low']),
                        "close": float(row['Close']),
                        "volume": int(row['Volume']),
                        "change": float(change),
                        "change_percent": float(change_percent),
                        "market": "US",
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    self.db.db.stock_price_daily.update_one(
                        {"_id": price_doc["_id"]},
                        {"$set": price_doc},
                        upsert=True
                    )
                
                # Collect financial data for each date
                # Note: yfinance doesn't provide historical fundamentals, so we use current data
                # This is a limitation but better than having no financial data
                info = ticker.info
                if info:
                    # Store financial data for each date in the period
                    for date_idx in hist.index:
                        date_str = date_idx.strftime("%Y-%m-%d")
                        self._collect_us_financial_for_date(symbol, ticker, date_str)
                
            logger.info(f"Historical data collection completed for {symbol}")
            
        except Exception as e:
            logger.error(f"Error collecting historical data for {symbol}: {e}")
            raise