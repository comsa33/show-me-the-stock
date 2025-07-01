# 📊 완전한 퀀트투자를 위한 추가 재무데이터 요구사항

## 🚨 현재 제한사항

### 미국 주식 (yfinance) ✅
- **완전한 데이터 수집 가능**
- PER, PBR, ROE, ROA, 부채비율, 시가총액 등 모든 지표 실시간 수집

### 한국 주식 (pykrx) ⚠️  
- **제한적 데이터만 수집 가능**
- 수집 가능: PER, PBR, EPS, BPS, 주가, 시가총액
- **수집 불가**: ROE, ROA, 부채비율, 현금흐름, 매출성장률 등

## 📋 추가 수집 필요한 한국 주식 재무데이터

### 1. 핵심 재무비율
```json
{
  "symbol": "005930",
  "company_name": "삼성전자",
  "market": "KOSPI",
  "financial_ratios": {
    "roe": 12.5,           // 자기자본이익률 (%)
    "roa": 8.3,            // 총자산이익률 (%)
    "debt_to_equity": 45.2, // 부채비율 (%)
    "current_ratio": 2.1,   // 유동비율
    "quick_ratio": 1.8,     // 당좌비율
    "interest_coverage": 15.2 // 이자보상배수
  }
}
```

### 2. 성장성 지표
```json
{
  "growth_metrics": {
    "revenue_growth_1y": 8.5,    // 매출성장률 (1년)
    "revenue_growth_3y": 12.3,   // 매출성장률 (3년 평균)
    "net_income_growth_1y": 15.2, // 순이익성장률 (1년)
    "eps_growth_1y": 12.8,       // EPS 성장률
    "book_value_growth": 9.1     // 장부가치 성장률
  }
}
```

### 3. 현금흐름 지표
```json
{
  "cash_flow": {
    "operating_cash_flow": 50000000000,  // 영업현금흐름 (원)
    "free_cash_flow": 35000000000,       // 잉여현금흐름 (원)
    "cash_flow_per_share": 8500,         // 주당 현금흐름 (원)
    "cash_to_debt_ratio": 0.8            // 현금부채비율
  }
}
```

### 4. 배당 정보
```json
{
  "dividend_info": {
    "dividend_yield": 2.3,          // 배당수익률 (%)
    "dividend_per_share": 1500,     // 주당 배당금 (원)
    "payout_ratio": 28.5,           // 배당성향 (%)
    "dividend_growth_rate": 5.2     // 배당성장률 (%)
  }
}
```

### 5. 밸류에이션 지표
```json
{
  "valuation": {
    "peg_ratio": 1.2,               // PEG 비율
    "price_to_sales": 1.8,          // PSR (주가매출비율)
    "price_to_cash_flow": 12.5,     // PCR (주가현금흐름비율)
    "enterprise_value": 450000000000, // 기업가치 (원)
    "ev_to_ebitda": 8.5             // EV/EBITDA
  }
}
```

## 🗄️ MongoDB 스키마 설계

### 컬렉션: `kr_financial_data`

```javascript
{
  _id: ObjectId("..."),
  symbol: "005930",                    // 종목코드
  company_name: "삼성전자",             // 회사명
  market: "KOSPI",                     // 시장구분
  sector: "반도체",                    // 섹터
  industry: "반도체 제조",             // 업종
  
  // 기본 정보
  basic_info: {
    market_cap: 400000000000000,       // 시가총액 (원)
    shares_outstanding: 5969782550,    // 발행주식수
    current_price: 67000,              // 현재가 (원)
    currency: "KRW"
  },
  
  // 재무비율
  financial_ratios: {
    per: 12.16,                        // 주가수익비율
    pbr: 1.04,                         // 주가장부가치비율
    roe: 12.5,                         // 자기자본이익률 (%)
    roa: 8.3,                          // 총자산이익률 (%)
    debt_to_equity: 45.2,              // 부채비율 (%)
    current_ratio: 2.1,                // 유동비율
    quick_ratio: 1.8,                  // 당좌비율
    interest_coverage: 15.2,           // 이자보상배수
    gross_margin: 45.8,                // 매출총이익률 (%)
    operating_margin: 15.2,            // 영업이익률 (%)
    net_margin: 12.8                   // 순이익률 (%)
  },
  
  // 성장성 지표
  growth_metrics: {
    revenue_growth_1y: 8.5,            // 매출성장률 1년 (%)
    revenue_growth_3y: 12.3,           // 매출성장률 3년 평균 (%)
    net_income_growth_1y: 15.2,        // 순이익성장률 1년 (%)
    eps_growth_1y: 12.8,               // EPS 성장률 (%)
    book_value_growth: 9.1,            // 장부가치 성장률 (%)
    total_asset_growth: 7.2            // 총자산 성장률 (%)
  },
  
  // 현금흐름
  cash_flow: {
    operating_cash_flow: 50000000000,  // 영업현금흐름 (원)
    investing_cash_flow: -25000000000, // 투자현금흐름 (원)
    financing_cash_flow: -8000000000,  // 재무현금흐름 (원)
    free_cash_flow: 35000000000,       // 잉여현금흐름 (원)
    cash_flow_per_share: 8500,         // 주당 현금흐름 (원)
    cash_to_debt_ratio: 0.8            // 현금부채비율
  },
  
  // 배당 정보
  dividend_info: {
    dividend_yield: 2.3,               // 배당수익률 (%)
    dividend_per_share: 1500,          // 주당 배당금 (원)
    payout_ratio: 28.5,                // 배당성향 (%)
    dividend_growth_rate: 5.2,         // 배당성장률 (%)
    ex_dividend_date: "2024-12-31"     // 배당락일
  },
  
  // 밸류에이션
  valuation: {
    peg_ratio: 1.2,                    // PEG 비율
    price_to_sales: 1.8,               // PSR (주가매출비율)
    price_to_cash_flow: 12.5,          // PCR (주가현금흐름비율)
    enterprise_value: 450000000000,    // 기업가치 (원)
    ev_to_ebitda: 8.5,                 // EV/EBITDA
    price_to_tangible_book: 1.1        // 유형자산 대비 주가비율
  },
  
  // 안정성 지표
  stability: {
    asset_turnover: 0.85,              // 자산회전율
    equity_ratio: 68.5,                // 자기자본비율 (%)
    debt_ratio: 31.5,                  // 부채비율 (%)
    times_interest_earned: 15.2,       // 이자보상배수
    working_capital: 45000000000       // 운전자본 (원)
  },
  
  // 메타데이터
  data_source: "manual_collection",    // 데이터 출처
  last_updated: ISODate("2024-01-15T09:00:00Z"), // 최종 업데이트
  quarter: "2024Q4",                   // 기준 분기
  fiscal_year: 2024,                   // 회계연도
  data_quality: "verified",            // 데이터 품질
  
  // 인덱스를 위한 필드
  created_at: ISODate("2024-01-15T09:00:00Z"),
  updated_at: ISODate("2024-01-15T09:00:00Z")
}
```

### 인덱스 설정
```javascript
// 복합 인덱스
db.kr_financial_data.createIndex({ "symbol": 1, "quarter": -1 })
db.kr_financial_data.createIndex({ "market": 1, "sector": 1 })
db.kr_financial_data.createIndex({ "last_updated": -1 })

// 퀀트 스크리닝용 인덱스
db.kr_financial_data.createIndex({ 
  "financial_ratios.per": 1, 
  "financial_ratios.pbr": 1, 
  "financial_ratios.roe": -1 
})
```

## 📊 데이터 수집 방법

### 1. 한국거래소 전자공시 (DART)
- **Open API**: https://opendart.fss.or.kr/
- 상장기업 재무제표, 사업보고서 데이터
- 분기별/연간 재무데이터 수집 가능

### 2. 네이버 금융, 다음 금융
- 웹 스크래핑을 통한 실시간 재무비율 수집
- 주의: 서비스 약관 확인 필요

### 3. 한국은행 ECOS API
- 거시경제 지표, 금리 데이터
- 무료 API 제공

### 4. 증권사 API
- 키움증권, 이베스트투자증권 등 Open API
- 실시간 재무데이터 제공

## 🚀 구현 우선순위

### Phase 1 (즉시 구현 가능)
- 현재 pykrx + yfinance로 수집 가능한 제한된 데이터로 퀀트 시스템 구축
- 미국 주식은 완전한 퀀트 분석, 한국 주식은 기본 분석

### Phase 2 (추가 데이터 수집 후)
- DART API 연동으로 한국 기업 상세 재무데이터 수집
- MongoDB에 저장 후 완전한 퀀트 분석 구현

## 💡 권장사항

1. **단계적 구현**: 현재 가능한 데이터로 먼저 구축 후 점진적 개선
2. **데이터 품질 관리**: 수집된 데이터의 정확성 검증 프로세스 구축
3. **업데이트 주기**: 분기별 재무제표 발표 시점에 맞춘 데이터 갱신
4. **백업 전략**: 여러 데이터 소스 확보로 안정성 확보