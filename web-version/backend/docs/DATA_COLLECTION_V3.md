# Data Collection V3 - Migration from pykrx

## Overview

This document describes the new data collection system that replaces pykrx with alternative data sources to avoid KRX API blocking issues.

## Data Providers

### Korean Market (KR)
- **Primary Source**: FinanceDataReader (FDR)
- **Fallback**: Yahoo Finance for major stocks
- **Stock List**: MongoDB (2,740+ stocks already loaded)

### US Market (US)
- **Primary Source**: Yahoo Finance (yfinance)
- **Stock List**: S&P 500, NASDAQ 100, and popular stocks

### Market Indices
- **Korean Indices**: Yahoo Finance (^KS11, ^KQ11, ^KS200)
- **US Indices**: Yahoo Finance (^GSPC, ^IXIC, ^DJI, etc.)

## API Endpoints

### Base URL
```
http://localhost:8000/api/v1/collection/v3
```

### Available Endpoints

#### 1. Collection Status
```bash
GET /status
```
Returns current data collection statistics.

#### 2. Collect Stock Lists
```bash
POST /stocks/list/{market}
```
- `market`: KR or US

#### 3. Collect Historical Prices
```bash
POST /stocks/prices/historical
```
Body:
```json
{
  "symbols": ["005930", "000660"],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "market": "KR"
}
```

#### 4. Collect All Historical Prices
```bash
POST /stocks/prices/all/{market}?start_date=2024-01-01&end_date=2024-12-31&limit=100
```

#### 5. Collect Financial Data
```bash
POST /stocks/financial/{market}?symbols=["AAPL","MSFT"]&limit=50
```

#### 6. Daily Data Collection
```bash
POST /daily/{market}
```
Collects today's price and financial data. Automatically skips weekends.

#### 7. Yearly Batch Collection
```bash
POST /batch/yearly?market=KR&year=2024&batch_size=50&offset=0
```
Useful for collecting large amounts of historical data in manageable batches.

## Rate Limiting

All data collection includes automatic rate limiting to avoid being blocked:
- Default delay: 0.5 seconds between requests
- Adjustable based on data source requirements

## Usage Examples

### 1. Quick Start - Collect Recent Data
```python
import requests

# Collect last 30 days for specific stocks
response = requests.post(
    "http://localhost:8000/api/v1/collection/v3/stocks/prices/historical",
    json={
        "symbols": ["005930", "000660", "035420"],
        "market": "KR"
    }
)
```

### 2. Full Historical Collection
```python
# Collect all 2024 data for Korean market in batches
offset = 0
batch_size = 100

while True:
    response = requests.post(
        "http://localhost:8000/api/v1/collection/v3/batch/yearly",
        params={
            "market": "KR",
            "year": 2024,
            "batch_size": batch_size,
            "offset": offset
        }
    )
    
    data = response.json()
    if not data["details"]["has_more"]:
        break
    
    offset = data["details"]["next_offset"]
    time.sleep(5)  # Wait between batches
```

### 3. Daily Automated Collection
```python
# Set up daily collection (skip weekends automatically)
response = requests.post(
    "http://localhost:8000/api/v1/collection/v3/daily/KR"
)
```

## Migration Progress

### Completed ✅
1. Abstract data provider interface
2. FinanceDataReader provider implementation
3. Yahoo Finance provider implementation
4. Hybrid provider for optimal data sourcing
5. New collection APIs with rate limiting
6. Service layer migration (index_data_service, real_financial_data, etc.)
7. MongoDB integration for stock lists

### Remaining Tasks
- Index data collector migration
- Complete testing and validation
- Remove pykrx dependencies

## Troubleshooting

### Common Issues

1. **Empty Data Returns**
   - Check if market is open (weekends/holidays)
   - Verify stock symbol format (Korean: 6 digits, US: ticker)

2. **Rate Limit Errors**
   - Reduce batch size
   - Increase delay between requests

3. **Missing Financial Data**
   - Some stocks may not have complete financial data
   - US financial data is current only (not historical)

## Benefits of New System

1. **No KRX Blocking**: Alternative data sources don't have weekend restrictions
2. **Better Reliability**: Multiple data sources with fallback options
3. **Unified Interface**: Same API for both Korean and US markets
4. **Rate Limiting**: Built-in protection against being blocked
5. **Batch Processing**: Efficient handling of large data requests

## Data Quality Notes

- Korean stock data from FDR is generally reliable and complete
- US stock data from Yahoo Finance is comprehensive
- Financial data update frequency varies by source
- Weekend data collection now possible for all markets