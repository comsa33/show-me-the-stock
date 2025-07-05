"""
MongoDB Schema Design for Stock Data

Collections:
1. stock_list - 종목 목록 정보
2. stock_price_daily - 일별 주가 데이터
3. stock_financial - 재무 지표 데이터
4. market_indices - 지수 데이터
5. stock_realtime - 실시간 주가 스냅샷
"""

# Collection: stock_list
# 종목 정보 마스터 데이터
STOCK_LIST_SCHEMA = {
    "_id": "symbol",  # 종목코드 (예: "005930", "AAPL")
    "symbol": "005930",
    "name": "삼성전자",
    "market": "KR",  # KR, US
    "exchange": "KOSPI",  # KOSPI, KOSDAQ, NASDAQ, NYSE
    "sector": "전자/전기",
    "industry": "반도체",
    "listing_date": "1975-06-11",
    "is_active": True,
    "updated_at": "2025-01-01T00:00:00"
}

# Collection: stock_price_daily
# 일별 주가 데이터 (OHLCV)
STOCK_PRICE_DAILY_SCHEMA = {
    "_id": "005930_2025-01-01",  # symbol_date 복합키
    "symbol": "005930",
    "date": "2025-01-01",
    "open": 69500,
    "high": 70500,
    "low": 69000,
    "close": 70000,
    "volume": 12345678,
    "change": -500,
    "change_percent": -0.71,
    "market": "KR",
    "updated_at": "2025-01-01T18:00:00"
}

# Collection: stock_financial
# 재무 지표 데이터 (일별)
STOCK_FINANCIAL_SCHEMA = {
    "_id": "005930_2025-01-01",  # symbol_date 복합키
    "symbol": "005930",
    "date": "2025-01-01",
    "market_cap": 420000000000000,  # 시가총액 (원)
    "shares_outstanding": 5969782550,  # 발행주식수
    "per": 15.2,  # PER
    "pbr": 1.1,   # PBR
    "eps": 4604,  # EPS
    "bps": 63636, # BPS
    "roe": 7.2,   # ROE (%)
    "roa": 4.8,   # ROA (%)
    "dividend_yield": 2.5,  # 배당수익률 (%)
    "market": "KR",
    "updated_at": "2025-01-01T18:00:00"
}

# Collection: market_indices
# 지수 데이터
MARKET_INDICES_SCHEMA = {
    "_id": "KOSPI_2025-01-01",  # index_code_date 복합키
    "code": "1001",  # 지수코드
    "name": "KOSPI",
    "date": "2025-01-01",
    "open": 2490.50,
    "high": 2510.25,
    "low": 2485.75,
    "close": 2500.50,
    "volume": 500000000,
    "change": 15.25,
    "change_percent": 0.61,
    "market": "KR",  # KR, US
    "updated_at": "2025-01-01T18:00:00"
}

# Collection: stock_realtime
# 실시간 주가 스냅샷 (최신 데이터만 유지)
STOCK_REALTIME_SCHEMA = {
    "_id": "005930",  # symbol
    "symbol": "005930",
    "name": "삼성전자",
    "market": "KR",
    "exchange": "KOSPI",
    "current_price": 70000,
    "prev_close": 70500,
    "open": 69500,
    "high": 70500,
    "low": 69000,
    "volume": 12345678,
    "change": -500,
    "change_percent": -0.71,
    "market_cap": 420000000000000,
    "per": 15.2,
    "pbr": 1.1,
    "dividend_yield": 2.5,
    "last_updated": "2025-01-01T15:30:00",
    "trading_status": "closed"  # open, closed, pre_market, after_hours
}

# Indexes for better query performance
INDEXES = {
    "stock_price_daily": [
        {"fields": [("symbol", 1), ("date", -1)], "unique": True},
        {"fields": [("date", -1)]},
        {"fields": [("market", 1), ("date", -1)]}
    ],
    "stock_financial": [
        {"fields": [("symbol", 1), ("date", -1)], "unique": True},
        {"fields": [("date", -1)]},
        {"fields": [("market", 1), ("date", -1)]}
    ],
    "market_indices": [
        {"fields": [("code", 1), ("date", -1)], "unique": True},
        {"fields": [("name", 1), ("date", -1)]},
        {"fields": [("market", 1), ("date", -1)]}
    ],
    "stock_list": [
        {"fields": [("symbol", 1)], "unique": True},
        {"fields": [("market", 1), ("is_active", 1)]},
        {"fields": [("exchange", 1), ("is_active", 1)]},
        {"fields": [("name", 1)]}
    ],
    "stock_realtime": [
        {"fields": [("symbol", 1)], "unique": True},
        {"fields": [("market", 1)]},
        {"fields": [("exchange", 1)]},
        {"fields": [("change_percent", -1)]}  # For sorting by top movers
    ]
}