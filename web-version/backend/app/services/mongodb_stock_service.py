"""
MongoDB-based Stock Service
Provides stock data from MongoDB instead of external APIs
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
from ..database.mongodb_client import get_mongodb_client
import logging

logger = logging.getLogger(__name__)


class MongoDBStockService:
    """Service for retrieving stock data from MongoDB"""
    
    def __init__(self):
        self.db = get_mongodb_client()
    
    def get_market_ticker_list(self, market: str) -> List[Dict[str, Any]]:
        """Get all active tickers for a market (pykrx compatible format)"""
        stocks = self.db.get_stock_list(market=market)
        if market == "US":
            # Return in the same format as stocks_v2.py expects
            return [
                {
                    "name": stock["name"],
                    "symbol": stock["symbol"],
                    "display": f"{stock['name']} ({stock['symbol']})",
                    "market": "US"
                }
                for stock in stocks
            ]
        else:
            # Korean stocks - return simple list format
            return [
                {
                    "symbol": stock["symbol"],
                    "name": stock["name"],
                    "display": f"{stock['name']} ({stock['symbol']})"
                }
                for stock in stocks
            ]
    
    def get_market_tickers(self, market: str) -> List[str]:
        """Get all active tickers for a market"""
        stocks = self.db.get_stock_list(market=market)
        return [stock["symbol"] for stock in stocks]
    
    def get_ticker_name(self, symbol: str) -> Optional[str]:
        """Get stock name by symbol"""
        stock = self.db.get_stock_info(symbol)
        return stock["name"] if stock else None
    
    def get_market_stocks_with_info(self, market: str) -> List[Dict[str, Any]]:
        """Get all stocks with basic info for a market"""
        stocks = self.db.get_stock_list(market=market)
        result = []
        
        for stock in stocks:
            # Get latest price data
            realtime = self.db.get_realtime_price(stock["symbol"])
            if realtime:
                result.append({
                    "symbol": stock["symbol"],
                    "name": stock["name"],
                    "sector": stock.get("sector", ""),
                    "price": realtime.get("current_price", 0),
                    "change": realtime.get("change", 0),
                    "change_percent": realtime.get("change_percent", 0),
                    "volume": realtime.get("volume", 0),
                    "market_cap": realtime.get("market_cap", 0)
                })
        
        return result
    
    def get_stock_price_history(self, symbol: str, 
                               period: str = "1mo",
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None) -> pd.DataFrame:
        """Get stock price history as DataFrame"""
        # Handle period conversion
        if not start_date and period:
            end_date = datetime.now().strftime("%Y-%m-%d")
            period_map = {
                "1d": 1, "5d": 5, "1mo": 30, "3mo": 90,
                "6mo": 180, "1y": 365, "2y": 730, "5y": 1825
            }
            days = period_map.get(period, 30)
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Get data from MongoDB
        price_data = self.db.get_stock_price_history(
            symbol, start_date=start_date, end_date=end_date
        )
        
        if not price_data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(price_data)
        df["Date"] = pd.to_datetime(df["date"])
        df = df.set_index("Date")
        
        # Select columns to match expected format
        columns = ["open", "high", "low", "close", "volume"]
        df = df[columns]
        df.columns = ["Open", "High", "Low", "Close", "Volume"]
        
        return df.sort_index()
    
    def get_stock_ohlcv(self, symbol: str, start_date: str, end_date: str, 
                       market: str = None) -> pd.DataFrame:
        """Get stock OHLCV data (pykrx compatible)"""
        # Convert date format if needed (YYYYMMDD to YYYY-MM-DD)
        if len(start_date) == 8 and '-' not in start_date:
            start_date = f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
        if len(end_date) == 8 and '-' not in end_date:
            end_date = f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
        
        # Get data from MongoDB
        price_data = self.db.get_stock_price_history(
            symbol, start_date=start_date, end_date=end_date
        )
        
        if not price_data:
            # Check if stock exists
            stock_info = self.db.get_stock_info(symbol)
            if not stock_info:
                raise ValueError(f"Stock {symbol} not found")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(price_data)
        df["Date"] = pd.to_datetime(df["date"])
        df = df.set_index("Date")
        
        # Select columns to match expected format
        columns = ["open", "high", "low", "close", "volume"]
        df = df[columns]
        df.columns = ["Open", "High", "Low", "Close", "Volume"]
        
        return df.sort_index()
    
    def get_stock_current_price(self, symbol: str) -> Dict[str, Any]:
        """Get current stock price and info"""
        realtime = self.db.get_realtime_price(symbol)
        if not realtime:
            # Fallback to latest daily data
            latest = self.db.get_latest_price(symbol)
            if latest:
                return {
                    "symbol": symbol,
                    "price": latest["close"],
                    "change": latest["change"],
                    "change_percent": latest["change_percent"],
                    "volume": latest["volume"],
                    "open": latest["open"],
                    "high": latest["high"],
                    "low": latest["low"],
                    "prev_close": latest["close"] + latest["change"]
                }
            return {}
        
        return {
            "symbol": realtime["symbol"],
            "price": realtime["current_price"],
            "change": realtime["change"],
            "change_percent": realtime["change_percent"],
            "volume": realtime["volume"],
            "open": realtime["open"],
            "high": realtime["high"],
            "low": realtime["low"],
            "prev_close": realtime["prev_close"]
        }
    
    def get_stock_financial_metrics(self, symbol: str) -> Dict[str, Any]:
        """Get financial metrics for a stock"""
        financial = self.db.get_stock_financial(symbol)
        if not financial:
            return {}
        
        return {
            "market_cap": financial.get("market_cap", 0),
            "shares_outstanding": financial.get("shares_outstanding", 0),
            "per": financial.get("per"),
            "pbr": financial.get("pbr"),
            "eps": financial.get("eps"),
            "bps": financial.get("bps"),
            "roe": financial.get("roe"),
            "roa": financial.get("roa"),
            "dividend_yield": financial.get("dividend_yield")
        }
    
    def get_stock_detail(self, symbol: str) -> Dict[str, Any]:
        """Get comprehensive stock details"""
        # Get basic info
        stock_info = self.db.get_stock_info(symbol)
        if not stock_info:
            return {"error": "Stock not found"}
        
        # Get current price
        current_price = self.get_stock_current_price(symbol)
        
        # Get financial metrics
        financials = self.get_stock_financial_metrics(symbol)
        
        # Get recent price history (1 month)
        price_history = self.get_stock_price_history(symbol, period="1mo")
        
        return {
            "symbol": symbol,
            "name": stock_info["name"],
            "market": stock_info["market"],
            "exchange": stock_info["exchange"],
            "sector": stock_info.get("sector", ""),
            "industry": stock_info.get("industry", ""),
            "current_price": current_price,
            "financial_metrics": financials,
            "price_data": price_history.reset_index().to_dict("records") if not price_history.empty else []
        }
    
    def search_stocks(self, keyword: str, market: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Search stocks by keyword (pykrx compatible)"""
        # Search in database
        stocks = self.db.search_stocks(keyword, limit * 2)  # Get more to filter by market
        result = []
        
        for stock in stocks:
            # Filter by market if specified
            if market and stock["market"] != market:
                continue
                
            realtime = self.db.get_realtime_price(stock["symbol"])
            result.append({
                "symbol": stock["symbol"],
                "name": stock["name"],
                "market": stock["market"],
                "exchange": stock["exchange"],
                "price": realtime["current_price"] if realtime else None,
                "change_percent": realtime["change_percent"] if realtime else None
            })
            
            if len(result) >= limit:
                break
        
        return result
    
    def get_popular_stocks(self, market: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get popular stocks by volume"""
        stocks = self.db.get_popular_stocks(market, limit)
        return [{
            "symbol": stock["symbol"],
            "name": stock["name"],
            "price": stock["current_price"],
            "change": stock["change"],
            "change_percent": stock["change_percent"],
            "volume": stock["volume"]
        } for stock in stocks]
    
    def get_market_ohlcv_today(self, market: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get today's OHLCV data for market (pykrx compatible)"""
        # Get latest date's data
        market_prices = self.db.get_market_prices(market)
        
        result = []
        for price_data in market_prices[:limit]:
            # Get stock info
            stock_info = self.db.get_stock_info(price_data["symbol"])
            if stock_info:
                result.append({
                    "symbol": price_data["symbol"],
                    "name": stock_info["name"],
                    "price": price_data["close"],
                    "change": price_data["change"],
                    "change_percent": price_data["change_percent"],
                    "volume": price_data["volume"],
                    "open": price_data["open"],
                    "high": price_data["high"],
                    "low": price_data["low"]
                })
        
        # Sort by volume descending
        result.sort(key=lambda x: x["volume"], reverse=True)
        return result
    
    def get_market_indices(self, market: str) -> List[Dict[str, Any]]:
        """Get market indices"""
        # Define index codes by market
        index_map = {
            "KR": {
                "KOSPI": "1001",
                "KOSDAQ": "2001",
                "KOSPI200": "1028",
                "KRX100": "1035"
            },
            "US": {
                "S&P500": "^GSPC",
                "NASDAQ": "^IXIC",
                "DowJones": "^DJI",
                "Russell2000": "^RUT",
                "VIX": "^VIX"
            }
        }
        
        indices = []
        codes = index_map.get(market.upper(), {})
        
        for name, code in codes.items():
            index_data = self.db.get_latest_index(code)
            if index_data:
                indices.append({
                    "name": name,
                    "code": code,
                    "value": index_data["close"],
                    "change": index_data["change"],
                    "change_percent": index_data["change_percent"],
                    "volume": index_data.get("volume", 0),
                    "market": market
                })
        
        return indices
    
    def get_index_history(self, index_code: str,
                         period: str = "1mo") -> pd.DataFrame:
        """Get index history as DataFrame"""
        # Convert period to date range
        end_date = datetime.now().strftime("%Y-%m-%d")
        period_map = {
            "1d": 1, "5d": 5, "1mo": 30, "3mo": 90,
            "6mo": 180, "1y": 365, "2y": 730, "5y": 1825
        }
        days = period_map.get(period, 30)
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Get data
        index_data = self.db.get_index_data(
            index_code, start_date=start_date, end_date=end_date
        )
        
        if not index_data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(index_data)
        df["Date"] = pd.to_datetime(df["date"])
        df = df.set_index("Date")
        
        # Select columns
        columns = ["open", "high", "low", "close", "volume"]
        df = df[columns]
        df.columns = ["Open", "High", "Low", "Close", "Volume"]
        
        return df.sort_index()
    
    def get_stock_detail_v2(self, symbol: str, market: str) -> Dict[str, Any]:
        """Get detailed stock information (v2 compatible)"""
        # Get basic stock info
        stock_info = self.db.get_stock_info(symbol)
        if not stock_info:
            raise ValueError(f"Stock {symbol} not found")
        
        # Get 1 year of price data
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        price_history = self.db.get_stock_price_history(
            symbol, start_date=start_date, end_date=end_date
        )
        
        if not price_history:
            raise ValueError(f"No price data found for {symbol}")
        
        # Convert to DataFrame for easier calculations
        df = pd.DataFrame(price_history)
        
        # Get latest data
        latest = price_history[-1]
        previous = price_history[-2] if len(price_history) > 1 else latest
        
        # Calculate metrics
        current_close = latest["close"]
        previous_close = previous["close"]
        current_high = latest["high"]
        current_low = latest["low"]
        current_volume = latest["volume"]
        
        # 52-week high/low
        year_high = max(p["high"] for p in price_history)
        year_low = min(p["low"] for p in price_history)
        
        # Average volume (20 days)
        recent_volumes = [p["volume"] for p in price_history[-20:]]
        avg_volume_20d = sum(recent_volumes) / len(recent_volumes) if recent_volumes else current_volume
        
        # Get financial metrics
        financial = self.db.get_stock_financial(symbol)
        
        # Build response
        result = {
            "symbol": symbol,
            "name": stock_info["name"],
            "market": market.upper(),
            "current_price": current_close,
            "previous_close": previous_close,
            "daily_range": {
                "low": current_low,
                "high": current_high
            },
            "year_range": {
                "low": year_low,
                "high": year_high
            },
            "volume": current_volume,
            "avg_volume_20d": int(avg_volume_20d),
            "market_cap": financial.get("market_cap") if financial else None,
            "per": financial.get("per") if financial else None,
            "pbr": financial.get("pbr") if financial else None,
            "dividend_yield": financial.get("dividend_yield") if financial else None,
            "eps": financial.get("eps") if financial else None,
            "bps": financial.get("bps") if financial else None
        }
        
        return result


# Create singleton instance
_mongodb_stock_service = None


def get_mongodb_stock_service() -> MongoDBStockService:
    """Get MongoDB stock service singleton"""
    global _mongodb_stock_service
    if _mongodb_stock_service is None:
        _mongodb_stock_service = MongoDBStockService()
    return _mongodb_stock_service