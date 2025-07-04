# Stock Dashboard API Endpoints

## 새로 추가/수정된 엔드포인트

### 1. 간단한 종목 목록 조회 API

#### GET `/api/v1/stocks/list/simple`
모든 종목의 코드와 이름만 간단하게 조회 (페이지네이션 없음)
**Redis 캐싱 적용 (24시간)**

**Parameters:**
- `market` (required): 시장 구분 (KR/US/ALL)

**Response Example:**
```json
{
  "market": "KR",
  "total_count": 2500,
  "stocks": [
    {
      "symbol": "005930",
      "name": "삼성전자",
      "market": "KR"
    },
    {
      "symbol": "000660",
      "name": "SK하이닉스", 
      "market": "KR"
    }
  ]
}
```

**캐시 정보:**
- 캐시 키: `stocks:list:simple:{market}` (예: stocks:list:simple:KR)
- 캐시 TTL: 24시간
- 매일 00시에 자동 갱신

#### GET `/api/v1/stocks/list/simple/{market_type}`
특정 시장의 종목 목록만 조회

**Parameters:**
- `market_type` (path): KOSPI/KOSDAQ/US

**Response Example:**
```json
{
  "market_type": "KOSPI",
  "total_count": 900,
  "stocks": [
    {
      "symbol": "005930",
      "name": "삼성전자"
    },
    {
      "symbol": "000660",
      "name": "SK하이닉스"
    }
  ]
}
```

### 2. 개선된 뉴스 검색 API

#### GET `/api/v1/news/search`
네이버 뉴스 검색 (페이지네이션 개선)

**Parameters:**
- `query` (required): 검색 키워드
- `display` (optional, default=10): 한 페이지당 항목 수 (1-100)
- `start` (optional, default=1): 시작 위치 (1-1000)
- `page` (optional): 페이지 번호 (start 대신 사용 가능)
- `sort` (optional, default="sim"): 정렬 옵션 (sim: 유사도순, date: 날짜순)

**Response Example:**
```json
{
  "lastBuildDate": "Mon, 04 Nov 2024 10:30:00 +0900",
  "total": 12500,
  "start": 1,
  "display": 10,
  "items": [
    {
      "title": "삼성전자 3분기 실적 발표",
      "originallink": "https://...",
      "link": "https://...",
      "description": "...",
      "pubDate": "Mon, 04 Nov 2024 09:00:00 +0900"
    }
  ],
  "page_info": {
    "current_page": 1,
    "total_pages": 1250,
    "items_per_page": 10,
    "total_items": 12500,
    "start_index": 1
  }
}
```

## 기존 주요 엔드포인트

### 주식 가격 조회
- GET `/api/v1/stocks/prices/{market}` - 시장별 주식 목록 및 가격 (페이지네이션)
- GET `/api/v1/stocks/all/{market}` - 전체 종목 리스트 (페이지네이션)
- GET `/api/v1/stocks/kospi` - KOSPI 종목 조회
- GET `/api/v1/stocks/kosdaq` - KOSDAQ 종목 조회

### 개별 종목 데이터
- GET `/api/v1/stocks/data/{symbol}` - 개별 주식 데이터 조회

### 종목 검색
- GET `/api/v1/stocks/search` - 종목 검색

### 인기 종목
- GET `/api/v1/stocks/popular/{market}` - 인기 종목 조회

### 시장 상태
- GET `/api/v1/stocks/market/status` - 시장 상태 정보

### 캐시 관리
- DELETE `/api/v1/stocks/cache/clear` - 종목 목록 캐시 수동 초기화 (관리자용)

### AI 분석
- GET `/api/v1/ai/analysis/{symbol}` - AI 주식 분석

### 퀀트 분석
- GET `/api/v1/quant/analysis/{symbol}` - 퀀트 지표 분석

### 지수 정보
- GET `/api/v1/indices/{index_code}` - 지수 정보 조회

### 실시간 데이터
- WebSocket `/api/v1/stocks/ws` - 실시간 주식 데이터