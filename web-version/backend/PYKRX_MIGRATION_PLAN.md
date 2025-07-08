# pykrx 마이그레이션 계획서

## 1. 개요

### 1.1 배경
- pykrx 라이브러리가 주말/공휴일에 접근 불가 (403 Forbidden)
- KRX API의 불안정성으로 인한 서비스 장애 위험
- 더 안정적이고 신뢰할 수 있는 데이터 소스로의 전환 필요

### 1.2 목표
- pykrx 의존성을 완전히 제거
- 기존 데이터 구조와 호환성 유지
- 서비스 중단 없이 점진적 마이그레이션
- 더 안정적인 데이터 수집 파이프라인 구축

## 2. 영향 범위 분석

### 2.1 직접 영향을 받는 파일들

#### 데이터 수집 레이어
- `/app/data/pykrx_stock_data.py` - 핵심 래퍼 클래스
- `/app/collectors/stock_data_collector.py` - 주식 데이터 수집
- `/app/collectors/index_data_collector.py` - 지수 데이터 수집
- `/app/services/real_financial_data.py` - 재무 데이터 서비스
- `/app/services/realtime_service.py` - 실시간 모니터링
- `/app/services/index_data_service.py` - 지수 서비스
- `/app/data/stock_data.py` - 일반 데이터 fetcher

#### 사용되는 pykrx 함수들
1. **주식 목록**: `get_market_ticker_list()`, `get_market_ticker_name()`
2. **가격 데이터**: `get_market_ohlcv()`, `get_market_ohlcv_by_date()`
3. **재무 데이터**: `get_market_fundamental_by_date()`, `get_market_cap_by_date()`
4. **지수 데이터**: `get_index_ohlcv_by_date()`, `get_index_ticker_list()`

### 2.2 데이터 구조 호환성 요구사항

현재 MongoDB에 저장된 데이터 구조를 유지해야 함:

```javascript
// stock_price_daily 컬렉션
{
  "_id": "005930_2025-01-06",
  "symbol": "005930",
  "date": "2025-01-06",
  "open": 1234.0,
  "high": 1250.0,
  "low": 1230.0,
  "close": 1245.0,
  "volume": 1000000,
  "change": 11.0,
  "change_percent": 0.89,
  "market": "KR",
  "updated_at": "2025-01-06T10:30:00"
}

// stock_financial 컬렉션
{
  "_id": "005930_2025-01-06",
  "symbol": "005930",
  "date": "2025-01-06",
  "per": 12.5,
  "pbr": 1.2,
  "eps": 5000,
  "bps": 50000,
  "div": 2.5,
  "market_cap": 400000000000000,
  "shares": 5969782550,
  "market": "KR"
}
```

## 3. 대체 데이터 소스 선정

### 3.1 후보 옵션 분석

#### Option 1: FinanceDataReader (권장)
- **장점**: 
  - 한국 개발자가 만든 라이브러리로 한국 시장 지원 우수
  - KRX, Yahoo, Google Finance 등 다중 소스 지원
  - pykrx와 유사한 API 제공
  - 주말/공휴일에도 접근 가능
- **단점**: 
  - 실시간 데이터는 제한적
  - 일부 재무데이터 누락 가능

#### Option 2: yfinance + 한국거래소 Open API
- **장점**: 
  - yfinance는 글로벌 표준
  - 한국거래소 Open API로 보완 가능
- **단점**: 
  - 한국 주식 티커 변환 필요 (005930.KS 형식)
  - Open API 인증 필요

#### Option 3: 크롤링 기반 솔루션
- **장점**: 
  - 완전한 제어 가능
  - 모든 데이터 접근 가능
- **단점**: 
  - 유지보수 부담
  - 법적 이슈 가능성

### 3.2 선정 결과: FinanceDataReader + yfinance 하이브리드

```python
# 주요 데이터: FinanceDataReader
# 보조/검증: yfinance
# 실시간: WebSocket 또는 증권사 API
```

## 4. 마이그레이션 전략

### 4.1 단계별 접근

#### Phase 1: 데이터 소스 추상화 (1-2일)
1. 새로운 인터페이스 정의
2. 기존 pykrx 래퍼를 인터페이스 구현으로 변경
3. 새로운 FinanceDataReader 구현체 작성

#### Phase 2: 병렬 실행 및 검증 (3-4일)
1. 두 데이터 소스를 동시 실행
2. 결과 비교 및 로깅
3. 데이터 정합성 검증

#### Phase 3: 점진적 전환 (2-3일)
1. 환경변수로 데이터 소스 선택
2. 특정 기능부터 순차적 전환
3. 모니터링 강화

#### Phase 4: 완전 전환 및 정리 (1-2일)
1. pykrx 의존성 제거
2. 불필요한 코드 정리
3. 문서 업데이트

### 4.2 구현 계획

#### 새로운 추상 인터페이스
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd

class StockDataProvider(ABC):
    """주식 데이터 제공자 추상 클래스"""
    
    @abstractmethod
    def get_stock_list(self, market: str, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """주식 목록 조회"""
        pass
    
    @abstractmethod
    def get_stock_price(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """주식 가격 데이터 조회"""
        pass
    
    @abstractmethod
    def get_stock_fundamental(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """재무 데이터 조회"""
        pass
    
    @abstractmethod
    def get_index_data(self, index_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """지수 데이터 조회"""
        pass
```

#### FinanceDataReader 구현체
```python
import FinanceDataReader as fdr

class FDRStockDataProvider(StockDataProvider):
    """FinanceDataReader 기반 데이터 제공자"""
    
    def __init__(self):
        self.symbol_mapping = self._load_symbol_mapping()
    
    def get_stock_list(self, market: str, date: Optional[str] = None) -> List[Dict[str, Any]]:
        # KRX 전체 종목 리스트
        if market == "KR":
            df = fdr.StockListing('KRX')
            return self._format_stock_list(df)
        # ... 구현
```

## 5. 위험 관리

### 5.1 잠재적 위험
1. **데이터 불일치**: 소스별 데이터 차이
2. **성능 저하**: 새 라이브러리의 속도 문제
3. **API 제한**: Rate limiting
4. **호환성 문제**: 기존 코드와의 충돌

### 5.2 완화 방안
1. **데이터 검증 레이어** 구축
2. **캐싱 강화** (Redis 활용)
3. **Rate limiter** 구현
4. **충분한 테스트** 및 단계적 롤아웃

## 6. 테스트 계획

### 6.1 단위 테스트
- 각 데이터 제공자 메서드별 테스트
- 데이터 변환 로직 테스트
- 에러 처리 테스트

### 6.2 통합 테스트
- MongoDB 저장 검증
- API 엔드포인트 테스트
- 프론트엔드 연동 테스트

### 6.3 성능 테스트
- 대량 데이터 수집 시나리오
- 동시 요청 처리
- 메모리 사용량 모니터링

## 7. 일정

| 단계 | 작업 내용 | 예상 기간 | 상태 |
|------|----------|-----------|------|
| 1 | 영향 분석 및 계획 수립 | 1일 | ✅ 완료 |
| 2 | 추상 인터페이스 설계 | 1일 | ✅ 완료 |
| 3 | FinanceDataReader 구현 | 2일 | ✅ 완료 |
| 4 | Yahoo Finance Provider 구현 | 1일 | ✅ 완료 |
| 5 | Hybrid Provider 구현 | 1일 | ✅ 완료 |
| 6 | 서비스 레이어 마이그레이션 | 2일 | 🔄 진행중 |
| 7 | 데이터 검증 시스템 구축 | 2일 | ⏳ 대기 |
| 8 | 최종 전환 및 정리 | 1일 | ⏳ 대기 |

**총 예상 기간: 10-12일**

## 8. 체크리스트

### 사전 준비
- [x] FinanceDataReader 설치 및 테스트
- [x] 기존 데이터 백업
- [x] 롤백 계획 수립

### 구현
- [x] StockDataProvider 인터페이스 작성
- [x] PykrxDataProvider 어댑터 구현
- [x] FDRDataProvider 구현
- [x] YahooDataProvider 구현
- [x] HybridDataProvider 구현
- [x] 환경변수 기반 전환 시스템
- [ ] 데이터 검증 모듈 작성

### 서비스 레이어 마이그레이션
- [x] index_data_service.py 마이그레이션
- [x] real_financial_data.py 마이그레이션 (진행중)
- [ ] realtime_service.py 마이그레이션
- [ ] stock_data_collector.py 마이그레이션
- [ ] index_data_collector.py 마이그레이션

### 테스트
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 실행
- [ ] 성능 비교 분석
- [ ] 프론트엔드 동작 확인

### 배포
- [ ] 스테이징 환경 테스트
- [ ] 점진적 롤아웃
- [ ] 모니터링 대시보드 구축
- [ ] 문서 업데이트

## 9. 성공 기준

1. **기능적 요구사항**
   - 모든 기존 API 엔드포인트 정상 동작
   - 데이터 정확도 99% 이상
   - 주말/공휴일 데이터 접근 가능

2. **성능 요구사항**
   - API 응답시간 기존 대비 110% 이내
   - 일일 데이터 수집 시간 2시간 이내

3. **안정성 요구사항**
   - 99.9% 가용성
   - 자동 복구 메커니즘
   - 완전한 에러 로깅

## 10. 참고 자료

- [FinanceDataReader 문서](https://github.com/FinanceData/FinanceDataReader)
- [yfinance 문서](https://github.com/ranaroussi/yfinance)
- [한국거래소 Open API](http://data.krx.co.kr/)