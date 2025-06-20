DEFAULT_KOSPI_STOCKS = {
    "삼성전자": "005930",
    "SK하이닉스": "000660",
    "NAVER": "035420",
    "LG화학": "051910",
    "KB금융": "105560",
    "현대차": "005380",
    "POSCO홀딩스": "005490",
    "삼성바이오로직스": "207940",
    "LG전자": "066570",
    "기아": "000270",
}

DEFAULT_NASDAQ_STOCKS = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Google": "GOOGL",
    "Tesla": "TSLA",
    "Meta": "META",
    "Netflix": "NFLX",
    "NVIDIA": "NVDA",
    "AMD": "AMD",
    "Intel": "INTC",
}

CHART_CONFIG = {
    "height": 600,
    "template": "plotly_white",
    "margin": {"l": 0, "r": 0, "t": 30, "b": 0},
}

CACHE_TTL = 300  # 5분

PERIOD_OPTIONS = {
    "1개월": "1mo",
    "3개월": "3mo",
    "6개월": "6mo",
    "1년": "1y",
    "2년": "2y",
    "5년": "5y",
}
