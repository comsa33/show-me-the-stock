"""
MongoDB Client for Stock Data
"""
import os
from typing import Optional, List, Dict, Any
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB client for stock data operations"""
    
    def __init__(self, uri: Optional[str] = None):
        self.uri = uri or os.getenv("MONGODB_URI")
        if not self.uri:
            # Try with hardcoded URI as fallback
            self.uri = "mongodb://admin:durwl4wlK@ruoserver.iptime.org:30017"
            logger.warning("Using hardcoded MongoDB URI as fallback")
        
        self.client = None
        self.db = None
        self._connect()
    
    def _connect(self):
        """Establish connection to MongoDB"""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.server_info()
            self.db = self.client.stock_data
            logger.info("Successfully connected to MongoDB")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
    
    def create_indexes(self):
        """Create indexes for all collections"""
        from .mongodb_schema import INDEXES
        
        for collection_name, index_list in INDEXES.items():
            collection = self.db[collection_name]
            for index_config in index_list:
                collection.create_index(
                    index_config["fields"],
                    unique=index_config.get("unique", False)
                )
        logger.info("All indexes created successfully")
    
    # Stock List Operations
    def get_stock_list(self, market: Optional[str] = None, 
                      exchange: Optional[str] = None,
                      is_active: bool = True) -> List[Dict[str, Any]]:
        """Get stock list filtered by market/exchange"""
        query = {"is_active": is_active}
        if market:
            query["market"] = market.upper()
        if exchange:
            query["exchange"] = exchange.upper()
        
        return list(self.db.stock_list.find(query))
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get single stock information"""
        return self.db.stock_list.find_one({"_id": symbol.upper()})
    
    def search_stocks(self, keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search stocks by name or symbol"""
        query = {
            "$or": [
                {"symbol": {"$regex": keyword, "$options": "i"}},
                {"name": {"$regex": keyword, "$options": "i"}}
            ],
            "is_active": True
        }
        return list(self.db.stock_list.find(query).limit(limit))
    
    # Price Data Operations
    def get_stock_price_history(self, symbol: str, 
                               start_date: Optional[str] = None,
                               end_date: Optional[str] = None,
                               limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get historical price data for a stock"""
        query = {"symbol": symbol.upper()}
        
        if start_date:
            query["date"] = {"$gte": start_date}
        if end_date:
            if "date" in query:
                query["date"]["$lte"] = end_date
            else:
                query["date"] = {"$lte": end_date}
        
        cursor = self.db.stock_price_daily.find(query).sort("date", DESCENDING)
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    
    def get_latest_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get latest price data for a stock"""
        return self.db.stock_price_daily.find_one(
            {"symbol": symbol.upper()},
            sort=[("date", DESCENDING)]
        )
    
    def get_market_prices(self, market: str, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all stock prices for a market on a specific date"""
        if not date:
            # Get latest date with data
            latest = self.db.stock_price_daily.find_one(
                {"market": market.upper()},
                sort=[("date", DESCENDING)]
            )
            if latest:
                date = latest["date"]
            else:
                return []
        
        return list(self.db.stock_price_daily.find({
            "market": market.upper(),
            "date": date
        }))
    
    # Financial Data Operations
    def get_stock_financial(self, symbol: str, 
                           date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get financial metrics for a stock"""
        if date:
            return self.db.stock_financial.find_one({
                "symbol": symbol.upper(),
                "date": date
            })
        else:
            # Get latest
            return self.db.stock_financial.find_one(
                {"symbol": symbol.upper()},
                sort=[("date", DESCENDING)]
            )
    
    def get_financial_history(self, symbol: str,
                             start_date: Optional[str] = None,
                             end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get historical financial data"""
        query = {"symbol": symbol.upper()}
        
        if start_date:
            query["date"] = {"$gte": start_date}
        if end_date:
            if "date" in query:
                query["date"]["$lte"] = end_date
            else:
                query["date"] = {"$lte": end_date}
        
        return list(self.db.stock_financial.find(query).sort("date", DESCENDING))
    
    # Index Data Operations
    def get_index_data(self, index_code: str,
                      start_date: Optional[str] = None,
                      end_date: Optional[str] = None,
                      limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get index historical data"""
        query = {"code": index_code}
        
        if start_date:
            query["date"] = {"$gte": start_date}
        if end_date:
            if "date" in query:
                query["date"]["$lte"] = end_date
            else:
                query["date"] = {"$lte": end_date}
        
        cursor = self.db.market_indices.find(query).sort("date", DESCENDING)
        if limit:
            cursor = cursor.limit(limit)
        
        return list(cursor)
    
    def get_latest_index(self, index_code: str) -> Optional[Dict[str, Any]]:
        """Get latest index data"""
        return self.db.market_indices.find_one(
            {"code": index_code},
            sort=[("date", DESCENDING)]
        )
    
    def get_indices_by_market(self, market: str, 
                             date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all indices for a market"""
        if not date:
            # Get latest date
            latest = self.db.market_indices.find_one(
                {"market": market.upper()},
                sort=[("date", DESCENDING)]
            )
            if latest:
                date = latest["date"]
            else:
                return []
        
        return list(self.db.market_indices.find({
            "market": market.upper(),
            "date": date
        }))
    
    # Realtime Data Operations
    def get_realtime_price(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get realtime price snapshot"""
        return self.db.stock_realtime.find_one({"_id": symbol.upper()})
    
    def get_realtime_prices(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Get realtime prices for multiple symbols"""
        return list(self.db.stock_realtime.find({
            "_id": {"$in": [s.upper() for s in symbols]}
        }))
    
    def get_top_movers(self, market: str, 
                      direction: str = "gainers",
                      limit: int = 10) -> List[Dict[str, Any]]:
        """Get top gainers or losers"""
        sort_order = DESCENDING if direction == "gainers" else ASCENDING
        
        return list(self.db.stock_realtime.find({
            "market": market.upper(),
            "change_percent": {"$ne": None}
        }).sort("change_percent", sort_order).limit(limit))
    
    def get_popular_stocks(self, market: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get popular stocks by volume"""
        return list(self.db.stock_realtime.find({
            "market": market.upper()
        }).sort("volume", DESCENDING).limit(limit))


# Singleton instance
_mongodb_client = None


def get_mongodb_client() -> MongoDBClient:
    """Get MongoDB client singleton"""
    global _mongodb_client
    if _mongodb_client is None:
        _mongodb_client = MongoDBClient()
    return _mongodb_client