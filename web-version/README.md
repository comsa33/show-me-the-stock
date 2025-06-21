# 📈 Stock Dashboard - Web Version

Google Gemini AI 기반 모던 주식 분석 대시보드

## ✨ 완성된 기능

### 📊 전체 종목 지원
- **한국 시장**: KOSPI (962개) + KOSDAQ (1,795개) = **총 2,757개 종목**
- **미국 시장**: S&P 500, NASDAQ 100 주요 종목 **71개**
- **페이지네이션**: 효율적인 대용량 데이터 탐색
- **실시간 가격**: Mock 실시간 주가 정보

### 🤖 Google Gemini AI 분석
- **실제 AI 분석**: Google Gemini 2.5 Flash 통합
- **실시간 뉴스**: Google Search 기반 최신 뉴스 감성 분석
- **기술적 분석**: RSI, 이동평균선, 거래량 분석
- **투자 추천**: 매수/매도/보유 신호 및 목표가 제시
- **단기/장기 분석**: 1일 vs 2주 분석 옵션

### 🔍 고급 검색 시스템
- **실시간 검색**: 헤더에서 즉시 검색
- **통합 검색**: 한국/미국 전체 종목 검색
- **모달 결과**: 깔끔한 검색 결과 표시
- **페이지네이션**: 검색 결과도 페이지 단위로

### 📱 모던 웹 UI/UX
- **Glass Morphism**: 최신 디자인 트렌드 적용
- **반응형 레이아웃**: 모바일/태블릿/데스크톱 최적화
- **다크 테마**: 눈에 편한 어두운 색상 테마
- **애니메이션**: 부드러운 인터랙션 효과

### 📈 상세 차트 시스템
- **다중 기간**: 1일~5년 다양한 기간 선택
- **금리 오버레이**: 주가와 금리 동시 표시 옵션
- **기술적 지표**: 각종 지표 계산 및 표시
- **상세 분석**: 종목별 심화 분석 페이지

## 🚀 기술 스택

### Backend
- **FastAPI**: 고성능 비동기 API 서버
- **Python 3.11+**: 최신 파이썬 기능 활용
- **Pydantic**: 타입 안전한 데이터 검증
- **Redis**: 캐싱 및 세션 관리
- **PostgreSQL**: 사용자 데이터 저장

### Frontend
- **React 18**: 최신 React 기능 (Hooks, Suspense)
- **TypeScript**: 타입 안전한 개발
- **Tailwind CSS**: 유틸리티 기반 스타일링
- **Chart.js/Plotly**: 인터랙티브 차트
- **React Query**: 서버 상태 관리
- **Zustand**: 클라이언트 상태 관리

### DevOps
- **Docker**: 컨테이너화 배포
- **Docker Compose**: 개발 환경 구성
- **Nginx**: 리버스 프록시 및 정적 파일 서빙
- **GitHub Actions**: CI/CD 파이프라인

## 📁 프로젝트 구조

```
stock-dashboard/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── api/            # API 엔드포인트
│   │   ├── core/           # 설정 및 보안
│   │   ├── models/         # 데이터 모델
│   │   ├── services/       # 비즈니스 로직
│   │   └── utils/          # 유틸리티 함수
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React 프론트엔드
│   ├── src/
│   │   ├── components/     # 재사용 컴포넌트
│   │   ├── pages/         # 페이지 컴포넌트
│   │   ├── hooks/         # 커스텀 훅
│   │   ├── services/      # API 서비스
│   │   ├── store/         # 상태 관리
│   │   └── utils/         # 유틸리티 함수
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml      # 개발 환경 설정
└── nginx/                  # 프록시 설정
```

## 🛠️ 개발 환경 설정

### 필수 요구사항
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose

### 설치 및 실행

1. **프로젝트 클론**
```bash
git clone <repository-url>
cd stock-dashboard
```

2. **Docker로 전체 서비스 실행**
```bash
docker-compose up -d
```

3. **개별 서비스 개발 모드**

Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:
```bash
cd frontend
npm install
npm start
```

## 📱 UX/UI 개선사항

### 스트림릿 대비 개선점
1. **성능**: 빠른 로딩과 부드러운 인터랙션
2. **디자인**: 모던하고 직관적인 UI
3. **반응형**: 모든 디바이스에서 최적화된 경험
4. **확장성**: 기능 추가 및 유지보수 용이
5. **실시간**: WebSocket 기반 실시간 데이터 업데이트

### 새로운 UX 기능
- **다크/라이트 모드**: 사용자 선호도에 따른 테마
- **드래그앤드롭**: 대시보드 레이아웃 커스터마이징
- **키보드 단축키**: 파워 유저를 위한 빠른 네비게이션
- **오프라인 지원**: PWA 기능으로 오프라인에서도 사용
- **다국어 지원**: 한국어/영어 지원

## 🚦 개발 로드맵

### Phase 1: 기본 구조 (1-2주)
- [ ] 백엔드 API 서버 구축
- [ ] 프론트엔드 기본 레이아웃
- [ ] 기본 차트 컴포넌트

### Phase 2: 핵심 기능 (2-3주)
- [ ] 주식 데이터 API 연동
- [ ] 인터랙티브 차트 구현
- [ ] 사용자 인증 및 즐겨찾기

### Phase 3: 고급 기능 (2-3주)
- [ ] AI 분석 통합
- [ ] 실시간 데이터 스트리밍
- [ ] 고급 차트 기능

### Phase 4: 최적화 & 배포 (1-2주)
- [ ] 성능 최적화
- [ ] 테스트 작성
- [ ] 프로덕션 배포

## 📞 지원

이슈나 기능 요청은 GitHub Issues를 통해 제출해주세요.