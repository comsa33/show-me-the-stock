# pykrx → FinanceDataReader 마이그레이션 요약

## 현재 상황 (2025-01-06)

### 완료된 작업

1. **추상화 계층 구축**
   - `StockDataProvider` 인터페이스 설계
   - `PykrxDataProvider`, `FDRDataProvider` 구현체 작성
   - `StockDataProviderFactory` 팩토리 패턴 구현

2. **데이터 제공자 테스트**
   - FinanceDataReader 주가 데이터 ✅ 작동
   - 한국 주식 목록 ⚠️ KRX API 문제로 백업 데이터 사용
   - 지수 데이터 ❌ KRX 완전 차단 (403 Forbidden)

3. **Collector V2 작성**
   - `stock_data_collector_v2.py` - Provider 기반으로 재작성
   - pykrx 직접 호출 제거
   - 환경변수로 provider 선택 가능

### 주요 문제점

1. **KRX API 차단**
   - pykrx와 FinanceDataReader 모두 KRX API 의존
   - 주말 문제가 아닌 완전 차단 상태
   - 한국 지수 데이터 수집 불가

2. **데이터 제한**
   - 재무 데이터: FDR 미지원
   - 시가총액: FDR 미지원
   - 지수: KRX 차단으로 불가

### 권장 해결책

#### 1. Yahoo Finance 통합 (즉시 실행 가능)
```bash
pip install yfinance
```

한국 주요 지수 심볼:
- KOSPI: `^KS11`
- KOSDAQ: `^KQ11`
- KOSPI 200: `^KS200`

#### 2. 하이브리드 접근
```python
class HybridDataProvider(StockDataProvider):
    def __init__(self):
        self.fdr = FDRDataProvider()      # 주가
        self.yf = YahooDataProvider()     # 지수, 재무
```

#### 3. 대체 데이터 소스
- 네이버 금융 API
- 다음 금융 API
- 증권사 API (키움, 대신 등)

### 다음 단계

1. **Yahoo Finance Provider 구현**
   - 한국 지수 데이터 수집
   - 재무 데이터 보완

2. **기존 서비스 마이그레이션**
   - `real_financial_data.py`
   - `realtime_service.py`
   - `index_data_service.py`

3. **API 엔드포인트 업데이트**
   - Provider 사용하도록 수정
   - 에러 처리 강화

4. **프론트엔드 영향 분석**
   - 데이터 형식 호환성 확인
   - 필요시 매핑 레이어 추가

### 마이그레이션 전략

#### Phase 1: 병렬 실행 (현재)
- 기존 코드 유지
- 새 Provider 시스템 병렬 구축
- 환경변수로 전환

#### Phase 2: 점진적 전환
- 기능별로 순차 전환
- 모니터링 강화
- 롤백 준비

#### Phase 3: 정리
- pykrx 의존성 제거
- 불필요 코드 삭제
- 문서 업데이트

### 코드 예시

#### 환경 설정
```bash
# .env
STOCK_DATA_PROVIDER=fdr  # 또는 pykrx, auto
```

#### 사용 예
```python
from app.data.stock_data_provider_factory import StockDataProviderFactory

# 자동 선택
provider = StockDataProviderFactory.get_provider()

# 명시적 선택
provider = StockDataProviderFactory.get_provider('fdr')

# 주가 조회
df = provider.get_stock_price('005930', '2025-01-01', '2025-01-06')
```

### 예상 일정
- Yahoo Finance 통합: 1-2일
- 서비스 레이어 마이그레이션: 2-3일
- 테스트 및 안정화: 2-3일
- **총 예상: 5-8일**

### 위험 요소
1. 데이터 정합성 (날짜, 형식)
2. 성능 저하 가능성
3. API Rate Limit
4. 프론트엔드 호환성

### 성공 지표
- ✅ 주말/공휴일 데이터 접근 가능
- ✅ 모든 기존 기능 정상 작동
- ✅ 에러율 5% 이하
- ✅ 응답속도 기존 대비 110% 이내