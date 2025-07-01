# 📈 Show Me The Stock - 완전체 주식 분석 플랫폼

Google Gemini AI 기반 모던 주식 분석 대시보드 + 퀀트투자 시스템

## ✨ 완성된 기능

### 📊 전체 종목 지원 (실시간 데이터)
- **한국 시장**: KOSPI (962개) + KOSDAQ (1,795개) = **총 2,757개 종목**
- **미국 시장**: S&P 500, NASDAQ 100 주요 종목 **71개**  
- **실시간 주가**: pykrx + yfinance를 통한 실제 시장 데이터
- **실시간 재무지표**: PER, PBR, ROE, ROA 등 실제 재무 데이터

### 🧮 퀀트투자 시스템 (NEW!)
- **실시간 퀀트 지표**: 
  - PER (주가수익비율) - 실제 데이터
  - PBR (주가장부가치비율) - 실제 데이터  
  - ROE (자기자본이익률) - 실제 데이터
  - ROA (총자산이익률) - 실제 데이터
  - 부채비율 - 실제 데이터
  - 3개월 모멘텀 - 실제 주가 데이터 기반
  - 변동성 - 실제 주가 데이터 기반
  - 시가총액 - 실제 데이터

- **5가지 팩터 전략**:
  1. **가치 전략 (Value)**: 저평가된 우량 기업 선별
  2. **모멘텀 전략 (Momentum)**: 상승 추세 종목 투자
  3. **품질 전략 (Quality)**: 재무 건전성 우수 기업
  4. **저변동성 전략 (Low Volatility)**: 안정적 종목 투자
  5. **소형주 전략 (Size)**: 성장 잠재력 높은 소형주

- **백테스트 엔진**: 전략별 과거 성과 시뮬레이션
- **개인화 추천**: 투자자 프로필 기반 맞춤 종목 추천
- **포트폴리오 구성**: 리스크 수준별 자동 포트폴리오 생성
- **실시간 필터링**: 슬라이더로 즉시 조건 변경
- **정렬 기능**: 모든 지표별 오름차순/내림차순 정렬

### 🤖 Google Gemini AI 분석
- **실제 AI 분석**: Google Gemini 2.5 Flash 통합
- **실시간 뉴스**: Google Search 기반 최신 뉴스 감성 분석
- **기술적 분석**: RSI, 이동평균선, 거래량 분석
- **투자 추천**: 매수/매도/보유 신호 및 목표가 제시
- **3가지 분석 모드**: 초보자/스윙/투자자별 맞춤 분석

### 🔍 고급 검색 시스템
- **실시간 검색**: 헤더에서 즉시 검색
- **통합 검색**: 한국/미국 전체 종목 검색
- **모달 결과**: 깔끔한 검색 결과 표시
- **페이지네이션**: 검색 결과도 페이지 단위로

### 📱 모던 웹 UI/UX
- **Glass Morphism**: 최신 디자인 트렌드 적용
- **반응형 레이아웃**: 모바일/태블릿/데스크톱 최적화
- **다크/라이트 테마**: 자동 테마 전환 + 수동 토글
- **애니메이션**: 부드러운 인터랙션 효과
- **직관적 탭 구조**: 대시보드, 주식분석, 퀀트투자, 포트폴리오 등

### 📈 상세 차트 시스템
- **다중 기간**: 1일~5년 다양한 기간 선택
- **금리 오버레이**: 주가와 금리 동시 표시 옵션
- **기술적 지표**: 각종 지표 계산 및 표시
- **상세 분석**: 종목별 심화 분석 페이지

## 🚀 기술 스택

### Backend
- **FastAPI**: 고성능 비동기 API 서버
- **Python 3.12**: 최신 파이썬 기능 활용
- **Pydantic**: 타입 안전한 데이터 검증
- **실시간 데이터**: pykrx (한국) + yfinance (미국)
- **Redis**: 캐싱 및 세션 관리

### Frontend  
- **React 19**: 최신 React 기능 (Hooks, Suspense)
- **TypeScript**: 타입 안전한 개발
- **CSS Variables**: 테마 시스템 구현
- **Lucide React**: 모던 아이콘 세트
- **반응형 CSS**: 모바일 우선 디자인

### AI & Data
- **Google Gemini 2.5 Flash**: 실제 AI 분석
- **pykrx**: 한국 주식시장 실시간 데이터
- **yfinance**: 미국 주식시장 실시간 데이터
- **pandas + numpy**: 퀀트 분석 계산 엔진

## 📁 프로젝트 구조

```
show-me-the-stock/web-version/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── api/v1/         # API 엔드포인트
│   │   │   └── endpoints/
│   │   │       ├── stocks.py      # 주식 데이터 API
│   │   │       ├── ai_analysis.py # AI 분석 API
│   │   │       └── quant.py       # 퀀트투자 API (NEW!)
│   │   ├── data/           # 데이터 수집
│   │   │   ├── stock_data.py      # 실시간 주식 데이터
│   │   │   └── interest_rate_data.py
│   │   ├── services/       # 비즈니스 로직
│   │   │   ├── ai_analysis.py           # AI 분석 서비스
│   │   │   ├── quant_service.py         # 퀀트 분석 (NEW!)
│   │   │   ├── real_financial_data.py   # 실시간 재무데이터 (NEW!)
│   │   │   └── recommendation_service.py # 개인화 추천 (NEW!)
│   │   └── core/           # 설정 및 보안
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── components/     # 재사용 컴포넌트
│   │   │   ├── views/
│   │   │   │   ├── StockAnalysisView.tsx
│   │   │   │   ├── QuantView.tsx      # 퀀트투자 탭 (NEW!)
│   │   │   │   ├── PortfolioView.tsx
│   │   │   │   └── ...
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Sidebar.tsx            # 퀀트투자 메뉴 추가
│   │   │   └── ViewManager.tsx
│   │   ├── context/        # React Context
│   │   │   ├── AppContext.tsx         # 앱 상태 관리
│   │   │   └── ThemeContext.tsx       # 테마 관리
│   │   └── config.ts
│   ├── package.json
│   └── Dockerfile
└── docker-compose.yml      # 개발 환경 설정
```

## 🛠️ 개발 환경 설정

### 필수 요구사항
- Node.js 18+
- Python 3.12+
- Docker & Docker Compose (선택사항)

### 설치 및 실행

1. **프로젝트 클론**
```bash
git clone <repository-url>
cd show-me-the-stock/web-version
```

2. **Backend 실행**
```bash
cd backend
pip install -r requirements.txt

# 환경변수 설정 (선택사항 - AI 분석용)
export GEMINI_API_KEY="your-gemini-api-key"

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. **Frontend 실행**
```bash
cd frontend
npm install
npm start
```

4. **접속**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API 문서: http://localhost:8000/docs

## 📊 API 엔드포인트

### 퀀트투자 API (신규)
```
GET  /api/v1/quant/indicators              # 퀀트 지표 조회
GET  /api/v1/quant/indicators/{symbol}     # 개별 종목 지표
POST /api/v1/quant/backtest               # 백테스트 실행
POST /api/v1/quant/recommendations        # 개인화 종목 추천
POST /api/v1/quant/portfolio-recommendations # 포트폴리오 추천
GET  /api/v1/quant/strategies             # 전략 목록
GET  /api/v1/quant/market-summary         # 시장 요약
GET  /api/v1/quant/investment-profiles    # 투자자 프로필 템플릿
```

### 기존 API
```
GET  /api/v1/stocks                       # 종목 목록
GET  /api/v1/stocks/{symbol}/data         # 개별 종목 데이터
POST /api/v1/ai/analyze                   # AI 분석
GET  /api/v1/interest-rates               # 금리 정보
```

## 🎯 주요 기능 사용법

### 1. 퀀트투자 분석
1. 사이드바에서 "퀀트투자" 탭 클릭
2. "퀀트 지표" 탭에서 실시간 재무지표 확인
3. 슬라이더로 PER, PBR, ROE 범위 필터링
4. 컬럼 헤더 클릭으로 정렬

### 2. 팩터 전략 백테스트
1. "팩터 전략" 탭 선택
2. 원하는 전략 선택 (가치, 모멘텀, 품질, 저변동성, 소형주)
3. "백테스트 실행" 버튼 클릭
4. "백테스트 결과" 탭에서 성과 확인

### 3. 개인화 종목 추천
1. 투자자 프로필 설정 (위험성향, 투자목표, 투자기간)
2. 선호 섹터 및 변동성 한계 설정
3. 맞춤형 종목 추천 및 포트폴리오 구성 받기

## 📈 실시간 데이터 소스

### 한국 시장 (pykrx)
- **주가**: 실시간 OHLCV 데이터
- **재무지표**: PER, PBR, EPS, BPS 실제 데이터
- **시가총액**: 실제 상장주식수 × 현재가
- **거래량**: 실시간 거래량 데이터

### 미국 시장 (yfinance)
- **주가**: 실시간 OHLCV 데이터  
- **재무지표**: SEC 보고서 기반 실제 데이터
- **밸류에이션**: trailing/forward PE, PB 비율
- **수익성**: ROE, ROA 실제 데이터

## 🚦 개발 완료 현황

### ✅ 완료된 기능
- [x] 백엔드 API 서버 구축
- [x] 프론트엔드 React 애플리케이션
- [x] 실시간 주식 데이터 연동
- [x] Google Gemini AI 분석 통합
- [x] **퀀트투자 시스템 구축** (NEW!)
- [x] **실시간 재무데이터 수집** (NEW!)
- [x] **팩터 기반 투자전략** (NEW!)
- [x] **백테스트 엔진** (NEW!)
- [x] **개인화 추천 시스템** (NEW!)
- [x] 반응형 UI/UX 구현
- [x] 다크/라이트 테마 시스템
- [x] 검색 및 필터링 기능

### 🔄 개선 가능한 부분
- [ ] 더 많은 기술적 지표 추가
- [ ] 실시간 알림 시스템
- [ ] 사용자 계정 및 포트폴리오 저장
- [ ] 모바일 앱 버전
- [ ] 더 많은 해외 시장 지원

## 📞 지원

이슈나 기능 요청은 GitHub Issues를 통해 제출해주세요.

---

**🎉 Show Me The Stock은 이제 완전한 퀀트투자 플랫폼입니다!**  
실시간 데이터 기반의 체계적인 퀀트 분석으로 더 스마트한 투자 결정을 내리세요.