# Unified Data Collection API

## Overview

This document describes the unified data collection API that consolidates all data collection functionality using new data providers (FinanceDataReader and Yahoo Finance) instead of pykrx.

## Base URL

```
http://localhost:8000/api/v1/data
```

## API Endpoints

### 1. System Status & Management

#### Get Collection Status
```http
GET /status
```
Returns comprehensive data collection statistics including stock counts, price data, financial data, and indices.

#### Initialize Database
```http
POST /initialize
```
Creates MongoDB indexes for optimal performance.

### 2. Stock List Management

#### Collect Stock List
```http
POST /stocks/list/{market}
```
- **market**: `KR` or `US`
- Collects and updates stock list for the specified market

### 3. Price Data Collection

#### Historical Prices (Specific Stocks)
```http
POST /prices/historical
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

#### All Historical Prices
```http
POST /prices/all/{market}?start_date=2024-01-01&end_date=2024-12-31&limit=100
```
- **market**: `KR` or `US`
- **start_date**: Optional, defaults to 1 year ago
- **end_date**: Optional, defaults to today
- **limit**: Optional, number of stocks to process

### 4. Financial Data Collection

#### Collect Financial Data
```http
POST /financial/{market}?symbols=["AAPL","MSFT"]&limit=50
```
- **market**: `KR` or `US`
- **symbols**: Optional list of specific symbols
- **limit**: Optional limit for batch processing

### 5. Daily Collection

#### Daily Data Collection
```http
POST /daily/{market}
```
- **market**: `KR` or `US`
- Collects today's price and financial data
- Automatically skips weekends/holidays

### 6. Batch Operations

#### Yearly Batch Collection
```http
POST /batch/yearly?market=KR&year=2024&batch_size=50&offset=0
```
- **market**: `KR` or `US`
- **year**: Year to collect data for
- **batch_size**: Number of stocks per batch (default: 50)
- **offset**: Starting position in stock list

### 7. Index Data Collection

#### Historical Indices
```http
POST /indices/historical?start_date=2024-01-01&end_date=2024-12-31&market=KR
```
- **market**: `KR`, `US`, or `ALL` (default: ALL)
- **start_date**: Optional start date
- **end_date**: Optional end date

#### Daily Indices
```http
POST /indices/daily
```
Collects today's index data for all markets.

### 8. Scheduler Management

#### Get Scheduler Status
```http
GET /scheduler/status
```
Returns scheduler running status and job information.

#### Start Scheduler
```http
POST /scheduler/start
```
Starts the automated data collection scheduler.

#### Stop Scheduler
```http
POST /scheduler/stop
```
Stops the automated data collection scheduler.

## Data Providers

| Market | Provider | Features |
|--------|----------|----------|
| Korean Stocks (KR) | FinanceDataReader (FDR) | Full historical data, no weekend restrictions |
| US Stocks (US) | Yahoo Finance | Comprehensive data, real-time updates |
| Market Indices | Yahoo Finance | Both Korean and US indices |

## Rate Limiting

All data collection includes automatic rate limiting:
- Default delay: 0.5 seconds between API requests
- Prevents blocking by data sources
- Configurable based on requirements

## Example Usage

### Python Example

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1/data"

# 1. Check status
response = requests.get(f"{BASE_URL}/status")
print(json.dumps(response.json(), indent=2))

# 2. Collect Korean stock list
response = requests.post(f"{BASE_URL}/stocks/list/KR")
print(response.json())

# 3. Collect historical prices for specific stocks
data = {
    "symbols": ["005930", "000660", "035420"],
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "market": "KR"
}
response = requests.post(f"{BASE_URL}/prices/historical", json=data)
print(response.json())

# 4. Collect financial data
response = requests.post(
    f"{BASE_URL}/financial/KR",
    params={"limit": 10}
)
print(response.json())

# 5. Daily collection
response = requests.post(f"{BASE_URL}/daily/KR")
print(response.json())
```

### Batch Collection Example

```python
# Collect all 2024 data in batches
offset = 0
batch_size = 100

while True:
    response = requests.post(
        f"{BASE_URL}/batch/yearly",
        params={
            "market": "KR",
            "year": 2024,
            "batch_size": batch_size,
            "offset": offset
        }
    )
    
    data = response.json()
    print(f"Processed batch at offset {offset}")
    
    if not data["details"]["has_more"]:
        break
    
    offset = data["details"]["next_offset"]
    time.sleep(5)  # Wait between batches
```

## Response Format

All endpoints return a consistent response format:

```json
{
    "status": "started|success|error",
    "message": "Human-readable message",
    "details": {
        // Optional additional information
    }
}
```

## Error Handling

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 404 | Not Found |
| 500 | Internal Server Error |

## Migration Notes

This unified API replaces the previous versions:
- `/collection/*` endpoints (v1) - deprecated
- `/collection/v3/*` endpoints - deprecated

All functionality has been consolidated into this single, cleaner API structure with consistent naming and behavior.

## Benefits

1. **No Weekend Restrictions**: Unlike pykrx, works on weekends/holidays
2. **Unified Interface**: Same API structure for all markets
3. **Better Performance**: Built-in rate limiting and batch processing
4. **Reliability**: Multiple data sources with fallback options
5. **Simplicity**: Cleaner API paths and consistent responses