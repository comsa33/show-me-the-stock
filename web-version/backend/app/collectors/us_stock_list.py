"""
US Stock List Fetcher
Fetches comprehensive US stock list from various sources
"""
import logging
import pandas as pd
import yfinance as yf
from typing import List, Dict, Set
import requests

logger = logging.getLogger(__name__)


class USStockListFetcher:
    """Fetches US stock lists from various sources"""
    
    @staticmethod
    def get_sp500_stocks() -> List[str]:
        """Get S&P 500 stock list"""
        try:
            # Wikipedia S&P 500 list
            url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
            tables = pd.read_html(url)
            sp500_table = tables[0]
            return sp500_table['Symbol'].tolist()
        except Exception as e:
            logger.error(f"Error fetching S&P 500 list: {e}")
            return []
    
    @staticmethod
    def get_nasdaq100_stocks() -> List[str]:
        """Get NASDAQ 100 stock list"""
        try:
            url = 'https://en.wikipedia.org/wiki/Nasdaq-100'
            tables = pd.read_html(url)
            # Find the table with stock symbols
            for table in tables:
                if 'Ticker' in table.columns or 'Symbol' in table.columns:
                    col_name = 'Ticker' if 'Ticker' in table.columns else 'Symbol'
                    return table[col_name].tolist()
            return []
        except Exception as e:
            logger.error(f"Error fetching NASDAQ 100 list: {e}")
            return []
    
    @staticmethod
    def get_dow_jones_stocks() -> List[str]:
        """Get Dow Jones Industrial Average stock list"""
        try:
            url = 'https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average'
            tables = pd.read_html(url)
            # Find the table with stock symbols
            for table in tables:
                if 'Symbol' in table.columns:
                    return table['Symbol'].tolist()
            return []
        except Exception as e:
            logger.error(f"Error fetching Dow Jones list: {e}")
            return []
    
    @staticmethod
    def get_popular_etfs() -> List[str]:
        """Get popular ETF list"""
        # Popular ETFs
        etfs = [
            'SPY', 'IVV', 'VOO', 'VTI', 'QQQ', 'VEA', 'IEFA', 'VWO', 'AGG', 'BND',
            'VUG', 'VTV', 'VIG', 'VYM', 'GLD', 'SLV', 'USO', 'XLE', 'XLF', 'XLK',
            'XLV', 'XLI', 'XLY', 'XLP', 'XLB', 'XLRE', 'XLU', 'DIA', 'IWM', 'IWF',
            'IWD', 'EEM', 'EFA', 'TLT', 'IEF', 'SHY', 'HYG', 'LQD', 'ARKK', 'ARKG',
            'ARKQ', 'ARKW', 'ARKF', 'ICLN', 'TAN', 'XBI', 'JETS', 'SKYY', 'HACK'
        ]
        return etfs
    
    @staticmethod
    def get_all_us_stocks() -> List[Dict[str, str]]:
        """Get comprehensive US stock list"""
        all_symbols = set()
        
        # Get S&P 500
        logger.info("Fetching S&P 500 stocks...")
        sp500 = USStockListFetcher.get_sp500_stocks()
        all_symbols.update(sp500)
        logger.info(f"Found {len(sp500)} S&P 500 stocks")
        
        # Get NASDAQ 100
        logger.info("Fetching NASDAQ 100 stocks...")
        nasdaq100 = USStockListFetcher.get_nasdaq100_stocks()
        all_symbols.update(nasdaq100)
        logger.info(f"Found {len(nasdaq100)} NASDAQ 100 stocks")
        
        # Get Dow Jones
        logger.info("Fetching Dow Jones stocks...")
        dow = USStockListFetcher.get_dow_jones_stocks()
        all_symbols.update(dow)
        logger.info(f"Found {len(dow)} Dow Jones stocks")
        
        # Get popular ETFs
        logger.info("Adding popular ETFs...")
        etfs = USStockListFetcher.get_popular_etfs()
        all_symbols.update(etfs)
        
        # Additional popular stocks not in indices
        additional_stocks = [
            'GME', 'AMC', 'BB', 'NOK', 'PLTR', 'NIO', 'XPEV', 'LI', 'BABA', 'JD',
            'PDD', 'BIDU', 'TSM', 'ASML', 'SHOP', 'SQ', 'PYPL', 'ROKU', 'SNAP',
            'PINS', 'UBER', 'LYFT', 'DASH', 'ABNB', 'COIN', 'HOOD', 'RBLX', 'U',
            'DDOG', 'NET', 'CRWD', 'ZM', 'DOCU', 'TWLO', 'OKTA', 'ZS', 'PANW',
            'FTNT', 'CRM', 'NOW', 'TEAM', 'WDAY', 'VEEV', 'ADSK', 'INTU', 'SNOW'
        ]
        all_symbols.update(additional_stocks)
        
        logger.info(f"Total unique US stocks found: {len(all_symbols)}")
        
        # Convert to list of dicts with symbol only (name will be fetched later)
        return [{"symbol": symbol} for symbol in sorted(all_symbols)]
    
    @staticmethod
    def get_stock_info_batch(symbols: List[str]) -> Dict[str, Dict]:
        """Get stock info for multiple symbols using yfinance"""
        stock_info = {}
        
        # Process in batches to avoid overwhelming the API
        batch_size = 50
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            
            for symbol in batch:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    if info and 'longName' in info:
                        stock_info[symbol] = {
                            'name': info.get('longName', info.get('shortName', symbol)),
                            'exchange': info.get('exchange', 'NASDAQ'),
                            'sector': info.get('sector', ''),
                            'industry': info.get('industry', ''),
                            'marketCap': info.get('marketCap', 0)
                        }
                except Exception as e:
                    logger.warning(f"Failed to get info for {symbol}: {e}")
                    stock_info[symbol] = {
                        'name': symbol,
                        'exchange': 'NASDAQ',
                        'sector': '',
                        'industry': '',
                        'marketCap': 0
                    }
        
        return stock_info