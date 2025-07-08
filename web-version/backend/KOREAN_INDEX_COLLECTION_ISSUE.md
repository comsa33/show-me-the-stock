# 한국 지수 데이터 수집 이슈

## 문제 상황
- pykrx를 통한 한국 지수 데이터 수집이 실패하고 있음
- 에러: KeyError: '지수명' 및 '시장'
- KRX API 응답: 403 Forbidden

## 원인 분석
1. 주말/공휴일에 pykrx가 지수 메타데이터를 가져오지 못하는 버그
2. KRX API 접근이 차단되었을 가능성 (403 응답)
3. pykrx 라이브러리와 KRX API 간의 호환성 문제

## 해결 방안

### 단기 해결책
1. **평일 업무시간에 수집 재시도**
   - 월요일~금요일 09:00~18:00 KST 시간대에 실행
   - KRX 서버가 주말에는 제한적으로 운영될 수 있음

2. **대체 데이터 소스 사용**
   - Yahoo Finance API를 통한 한국 지수 수집
   - 예: ^KS11 (KOSPI), ^KQ11 (KOSDAQ)

3. **VPN 또는 프록시 사용**
   - IP 차단이 원인일 경우

### 장기 해결책
1. **pykrx 라이브러리 업데이트 확인**
   ```bash
   pip install --upgrade pykrx
   ```

2. **커스텀 스크래퍼 구현**
   - KRX 웹사이트 직접 스크래핑
   - 또는 증권사 API 활용

3. **데이터 제공업체 API 구독**
   - 한국거래소 정보데이터시스템
   - 금융투자협회 API

## 임시 해결 코드 (Yahoo Finance 사용)

```python
import yfinance as yf

# 한국 주요 지수 Yahoo Finance 심볼
kr_indices_yahoo = {
    'KOSPI': '^KS11',
    'KOSDAQ': '^KQ11',
    'KOSPI200': '^KS200'
}

# 데이터 수집
for name, symbol in kr_indices_yahoo.items():
    ticker = yf.Ticker(symbol)
    data = ticker.history(period="1y")
    # MongoDB에 저장
```

## 수집 명령어
평일에 다시 시도:
```bash
curl -X POST "http://localhost:8000/api/v1/collection/collect-indices-historical" \
  -H "Content-Type: application/json" \
  -d '{"start_date": "2024-01-06", "end_date": "2025-01-03", "market": "KR"}'
```