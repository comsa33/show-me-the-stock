# 📈 Stock Dashboard - Web Version

모던 주식 분석 대시보드 - React + FastAPI 기반

## ✨ 주요 기능

### 📊 데이터 시각화
- **실시간 차트**: 캔들스틱, 라인, 면적 차트
- **기술적 지표**: 이동평균선(MA5, MA20), RSI, 볼린저 밴드
- **금리 오버레이**: 주가와 금리 동시 표시
- **다중 주식 비교**: 여러 종목 동시 분석

### 🤖 AI 분석
- **종합 분석**: AI 기반 주식 분석 및 인사이트
- **기술적 분석**: 지표 기반 매매 신호
- **실시간 분석**: 최신 뉴스 및 시장 정보 포함
- **비교 분석**: 여러 종목 간 상대적 성과 분석

### 🎯 사용자 기능
- **즐겨찾기**: 관심 종목 관리
- **주식 검색**: 고급 검색 및 자동완성
- **사용자 설정**: 개인화된 대시보드
- **반응형 디자인**: 모바일, 태블릿, 데스크톱 지원

### 🌍 시장 정보
- **한국 시장**: KOSPI, KOSDAQ 전 종목
- **미국 시장**: NASDAQ, NYSE 주요 종목
- **시장 상태**: 실시간 장 개장/마감 정보
- **금리 정보**: 한국/미국 국채 금리

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