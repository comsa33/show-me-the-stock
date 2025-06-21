# Google Gemini AI 분석 설정 가이드

## 1. Google API Key 발급

1. [Google AI Studio](https://makersuite.google.com/app/apikey)에 접속
2. Google 계정으로 로그인
3. "Create API Key" 버튼 클릭
4. API Key 복사

## 2. 환경변수 설정

### 방법 1: .env 파일 사용 (권장)
```bash
# 프로젝트 루트에 .env 파일 생성
cp .env.example .env

# .env 파일 편집
GOOGLE_API_KEY=your_actual_api_key_here
```

### 방법 2: 환경변수 직접 설정
```bash
export GOOGLE_API_KEY=your_actual_api_key_here
docker compose up -d
```

## 3. 동작 확인

API Key가 설정되면 자동으로 실제 Gemini AI 분석이 활성화됩니다:

```bash
# AI 분석 테스트
curl -X POST "http://localhost:8000/api/v1/ai/stock/analyze?symbol=005930&market=KR&analysis_type=short"
```

응답에서 `"ai_provider": "Google Gemini 2.5 Flash"`로 표시되면 정상 작동 중입니다.

## 4. 지원 기능

### 📊 AI 주식 분석
- **실제 주가 데이터** 기반 기술적 분석
- **Google Search 기반** 최신 뉴스 감성 분석
- **단기/장기** 분석 옵션
- **목표가 예측** 및 투자 추천

### 🔍 분석 항목
- 전체 투자 신호 (상승/하락/횡보)
- 신뢰도 (65-90%)
- 투자 추천 (매수/매도/보유)
- 목표 주가
- RSI, 이동평균선, 거래량 분석
- 뉴스 감성 분석
- 리스크 요인
- AI 인사이트

### 📈 지원 시장
- **한국 시장**: KOSPI/KOSDAQ 전 종목 (2,757개)
- **미국 시장**: 주요 종목 (71개)

## 5. 주의사항

- API Key는 보안상 중요하므로 `.env` 파일을 Git에 커밋하지 마세요
- Google AI Studio에서 월간 사용량 한도를 확인하세요
- 실제 투자 결정은 AI 분석만으로 하지 말고 종합적으로 판단하세요

## 6. 문제 해결

### API Key 오류
```bash
# 로그 확인
docker compose logs backend

# API Key 재설정
docker compose down
export GOOGLE_API_KEY=your_new_key
docker compose up -d
```

### Mock 데이터 사용 중인 경우
- `"ai_provider": "Mock Data"`로 표시됨
- Google API Key가 설정되지 않았거나 인터넷 연결 문제
- API 호출 한도 초과 등의 이유로 Fallback 동작