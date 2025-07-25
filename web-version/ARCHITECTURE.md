# Show Me The Stock - System Architecture

## 전체 시스템 아키텍처

```mermaid
graph TB
    subgraph "Frontend - React TypeScript"
        subgraph "UI Layer"
            UI[React Components]
            UI --> Views[View Components]
            Views --> Dashboard[Dashboard]
            Views --> StockAnalysis[Stock Analysis]
            Views --> QuantView[Quant Investment]
            Views --> Portfolio[Portfolio]
            Views --> Watchlist[Watchlist]
            Views --> Profile[Profile]
            Views --> News[News]
            Views --> Chat[AI Chat]
        end

        subgraph "State Management"
            Context[React Context]
            Context --> AppContext["AppContext<br/>전역 상태<br/>검색/필터<br/>선택 종목"]
            Context --> AuthContext["AuthContext<br/>사용자 인증<br/>세션 관리<br/>프로필 정보"]
            Context --> ThemeContext["ThemeContext<br/>다크/라이트 모드<br/>UI 테마"]
        end

        subgraph "Services Layer"
            Services[Frontend Services]
            Services --> WatchlistService["WatchlistService<br/>관심종목 CRUD<br/>Supabase 연동"]
            Services --> NotificationService["NotificationService<br/>WebSocket 연결<br/>실시간 알림<br/>알림 설정"]
            Services --> StockService["StockService<br/>API 호출<br/>데이터 캐싱"]
        end

        subgraph "External Integration"
            Supabase[Supabase Client]
            Supabase --> Auth["Authentication<br/>OAuth Google/GitHub<br/>Email/Password<br/>Session 관리"]
            Supabase --> Database["Database<br/>profiles<br/>user_settings<br/>watchlists"]
        end
    end

    subgraph "Backend - FastAPI Python"
        subgraph "API Layer"
            FastAPI[FastAPI Server]
            FastAPI --> Endpoints[API Endpoints]
            Endpoints --> StocksAPI["Stocks API<br/>종목 목록<br/>상세 정보<br/>가격 데이터"]
            Endpoints --> QuantAPI["Quant API<br/>퀀트 지표<br/>백테스트<br/>전략 추천"]
            Endpoints --> AIAPI["AI API<br/>AI 분석<br/>투자 추천"]
            Endpoints --> RealtimeAPI["Realtime API<br/>WebSocket<br/>실시간 알림"]
            Endpoints --> NewsAPI["News API<br/>뉴스 검색<br/>감성 분석"]
        end

        subgraph "Business Logic"
            Services2[Backend Services]
            Services2 --> AIService["AI Analysis Service<br/>Gemini API 연동<br/>분석 로직<br/>추천 생성"]
            Services2 --> QuantService["Quant Service<br/>지표 계산<br/>백테스트 엔진<br/>전략 평가"]
            Services2 --> RealtimeService["Realtime Service<br/>가격 모니터링<br/>알림 생성<br/>WebSocket 관리"]
            Services2 --> FinancialDataService["Financial Data Service<br/>재무 데이터 수집<br/>지표 계산"]
        end

        subgraph "Data Providers"
            DataLayer[Data Providers]
            DataLayer --> PyKrx["PyKrx Provider<br/>한국 주식<br/>실시간 가격<br/>재무 데이터"]
            DataLayer --> YFinance["YFinance Provider<br/>미국 주식<br/>글로벌 데이터<br/>히스토리 데이터"]
            DataLayer --> NewsProvider["News Provider<br/>Google Search<br/>뉴스 수집"]
        end

        subgraph "Infrastructure"
            Cache["Redis Cache<br/>가격 캐싱<br/>세션 관리"]
            WSManager["WebSocket Manager<br/>연결 관리<br/>구독 관리"]
        end
    end

    subgraph "External Services"
        GeminiAI["Google Gemini API<br/>AI 분석<br/>자연어 처리"]
        SupabaseDB[("Supabase Database<br/>PostgreSQL<br/>Row Level Security<br/>Realtime 구독")]
    end

    %% Connections
    UI --> Context
    Views --> Services
    Services --> FastAPI
    Auth --> SupabaseDB
    Database --> SupabaseDB
    
    StocksAPI --> Services2
    QuantAPI --> QuantService
    AIAPI --> AIService
    RealtimeAPI --> RealtimeService
    NewsAPI --> Services2
    
    AIService --> GeminiAI
    Services2 --> DataLayer
    RealtimeService --> WSManager
    Services2 --> Cache
    
    NotificationService -.->|WebSocket| RealtimeAPI
    WatchlistService --> Database

    classDef frontend fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef backend fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef external fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef data fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    
    class UI,Views,Context,Services,Supabase,Dashboard,StockAnalysis,QuantView,Portfolio,Watchlist,Profile,News,Chat,AppContext,AuthContext,ThemeContext,WatchlistService,NotificationService,StockService,Auth,Database frontend
    class FastAPI,Endpoints,Services2,DataLayer,Cache,WSManager,StocksAPI,QuantAPI,AIAPI,RealtimeAPI,NewsAPI,AIService,QuantService,RealtimeService,FinancialDataService backend
    class GeminiAI,SupabaseDB external
    class PyKrx,YFinance,NewsProvider data
```

## 데이터 흐름도

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant Supabase
    participant Backend
    participant DataProvider
    participant GeminiAI
    
    User->>Frontend: 로그인 요청
    Frontend->>Supabase: OAuth/Email 인증
    Supabase-->>Frontend: 세션 토큰
    Frontend->>Frontend: AuthContext 업데이트
    
    User->>Frontend: 주식 검색
    Frontend->>Backend: GET /api/v1/stocks/search
    Backend->>DataProvider: 주식 데이터 요청
    DataProvider-->>Backend: 주식 정보
    Backend-->>Frontend: 검색 결과
    
    User->>Frontend: AI 분석 요청
    Frontend->>Backend: POST /api/v1/ai/analyze
    Backend->>DataProvider: 주식 데이터 수집
    DataProvider-->>Backend: 가격/재무 데이터
    Backend->>GeminiAI: 분석 요청
    GeminiAI-->>Backend: AI 분석 결과
    Backend-->>Frontend: 분석 리포트
    
    User->>Frontend: 관심종목 추가
    Frontend->>Supabase: INSERT watchlists
    Supabase-->>Frontend: 성공
    Frontend->>Frontend: UI 업데이트
    
    Backend->>Backend: 가격 변동 감지
    Backend->>Frontend: WebSocket 알림
    Frontend->>User: 토스트 알림 표시
```

## 컴포넌트 계층 구조

```mermaid
graph TD
    App[App.tsx]
    App --> AuthProvider[AuthProvider]
    AuthProvider --> ThemeProvider[ThemeProvider]
    ThemeProvider --> AppProvider[AppProvider]
    AppProvider --> Dashboard[Dashboard]
    
    Dashboard --> Sidebar[Sidebar<br/>- 네비게이션<br/>- 메뉴 항목]
    Dashboard --> Header[Header<br/>- 검색바<br/>- 테마 토글<br/>- 사용자 메뉴]
    Dashboard --> ViewManager[ViewManager]
    
    ViewManager --> MarketDashboard[MarketDashboard<br/>- 시장 지수<br/>- 종목 목록]
    ViewManager --> StockAnalysisView[StockAnalysisView<br/>- 차트<br/>- AI 분석<br/>- 기술적 지표]
    ViewManager --> QuantView[QuantView<br/>- 퀀트 지표<br/>- 백테스트<br/>- 전략 추천]
    ViewManager --> WatchlistView[WatchlistView<br/>- 관심종목<br/>- 실시간 가격]
    ViewManager --> ProfileView[ProfileView<br/>- 사용자 정보<br/>- 설정]
    ViewManager --> NewsView[NewsView<br/>- 뉴스 목록<br/>- 감성 분석]
    
    App --> FloatingChatButton[FloatingChatButton<br/>- AI 채팅<br/>- 질문/답변]

    classDef component fill:#e3f2fd,stroke:#1565c0,stroke-width:2px
    classDef provider fill:#fce4ec,stroke:#c2185b,stroke-width:2px
    classDef view fill:#f1f8e9,stroke:#558b2f,stroke-width:2px
    
    class App,Dashboard,Sidebar,Header,ViewManager,FloatingChatButton component
    class AuthProvider,ThemeProvider,AppProvider provider
    class MarketDashboard,StockAnalysisView,QuantView,WatchlistView,ProfileView,NewsView view
```

## 데이터베이스 스키마

```mermaid
erDiagram
    users ||--o{ profiles : has
    users ||--o{ user_settings : has
    users ||--o{ watchlists : has
    
    users {
        uuid id PK
        string email
        jsonb user_metadata
        timestamp created_at
    }
    
    profiles {
        uuid id PK,FK
        string username
        string full_name
        string avatar_url
        timestamp created_at
        timestamp updated_at
    }
    
    user_settings {
        uuid user_id PK,FK
        string theme
        jsonb preferences
        timestamp created_at
        timestamp updated_at
    }
    
    watchlists {
        uuid id PK
        uuid user_id FK
        string stock_symbol
        string market
        timestamp added_at
    }
```

## 보안 및 인증 흐름

```mermaid
graph LR
    subgraph "Client"
        Browser[브라우저]
        LocalStorage[LocalStorage<br/>- Supabase 세션]
    end
    
    subgraph "Supabase"
        Auth[Supabase Auth]
        RLS[Row Level Security]
        DB[(PostgreSQL)]
    end
    
    subgraph "Security Policies"
        Policy1[profiles 정책<br/>- 자신의 프로필만 수정]
        Policy2[watchlists 정책<br/>- 자신의 관심종목만 접근]
        Policy3[user_settings 정책<br/>- 자신의 설정만 접근]
    end
    
    Browser -->|1. 로그인 요청| Auth
    Auth -->|2. JWT 토큰 발급| Browser
    Browser -->|3. 토큰 저장| LocalStorage
    Browser -->|4. API 요청 + 토큰| RLS
    RLS -->|5. 정책 검증| Policy1
    RLS --> Policy2
    RLS --> Policy3
    Policy1 -->|6. 승인된 데이터만| DB
    Policy2 --> DB
    Policy3 --> DB
    DB -->|7. 결과 반환| Browser

    classDef client fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px
    classDef supabase fill:#e0f2f1,stroke:#00695c,stroke-width:2px
    classDef policy fill:#fff8e1,stroke:#f57c00,stroke-width:2px
    
    class Browser,LocalStorage client
    class Auth,RLS,DB supabase
    class Policy1,Policy2,Policy3 policy
```

## 비개발자를 위한 시스템 구성도

### 서비스 전체 구조

```mermaid
graph TD
    subgraph "사용자가 보는 화면"
        User["👤 사용자"]
        Browser["🌐 웹 브라우저<br/>(Chrome, Safari 등)"]
        Mobile["📱 모바일 브라우저"]
    end

    subgraph "우리 서비스"
        subgraph "화면 구성"
            Main["🏠 메인 대시보드<br/>주식 목록과 시장 현황"]
            Analysis["📊 주식 분석<br/>차트와 AI 분석 결과"]
            Quant["🧮 퀀트 투자<br/>투자 전략과 백테스트"]
            MyPage["👤 마이페이지<br/>프로필과 관심종목"]
            AIChat["💬 AI 챗봇<br/>투자 질문과 답변"]
        end

        subgraph "핵심 기능"
            StockData["📈 실시간 주가 정보<br/>한국/미국 주식"]
            AIAnalysis["🤖 AI 투자 분석<br/>Google AI가 분석"]
            Alert["🔔 실시간 알림<br/>가격 변동 알림"]
            Login["🔐 로그인 시스템<br/>Google/GitHub/이메일"]
        end
    end

    subgraph "외부 서비스"
        Gemini["🧠 Google Gemini AI<br/>인공지능 분석"]
        Market["🏛️ 증권거래소<br/>실시간 시세 정보"]
        Supabase2["☁️ Supabase 클라우드<br/>사용자 정보 저장"]
    end

    User --> Browser
    User --> Mobile
    Browser --> Main
    Mobile --> Main
    
    Main --> Analysis
    Main --> Quant
    Main --> MyPage
    Main --> AIChat
    
    Analysis --> StockData
    Analysis --> AIAnalysis
    Quant --> StockData
    MyPage --> Login
    
    StockData --> Market
    AIAnalysis --> Gemini
    Login --> Supabase2
    Alert --> User

    classDef user fill:#ffebee,stroke:#d32f2f,stroke-width:3px
    classDef screen fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef feature fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef external fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    
    class User,Browser,Mobile user
    class Main,Analysis,Quant,MyPage,AIChat screen
    class StockData,AIAnalysis,Alert,Login feature
    class Gemini,Market,Supabase2 external
```

### 사용자 여정 (User Journey)

```mermaid
graph LR
    subgraph "1. 서비스 접속"
        Start["🏁 시작"]
        Visit["🌐 웹사이트 방문<br/>showmethestock.com"]
        Login2["🔐 로그인<br/>(선택사항)"]
    end

    subgraph "2. 주식 탐색"
        Search["🔍 주식 검색<br/>삼성전자, 애플 등"]
        List["📋 종목 목록 보기<br/>한국/미국 주식"]
        Select["👆 종목 선택"]
    end

    subgraph "3. 분석 확인"
        Chart["📊 차트 확인<br/>가격 추이"]
        AI["🤖 AI 분석 보기<br/>투자 추천"]
        Quant2["🧮 퀀트 지표<br/>재무 분석"]
    end

    subgraph "4. 개인화 기능"
        Watchlist2["⭐ 관심종목 추가"]
        Alert2["🔔 알림 설정"]
        Chat["💬 AI 챗봇 질문"]
    end

    subgraph "5. 투자 결정"
        Decision["🤔 투자 결정<br/>매수/매도/관망"]
        Monitor["📱 지속 모니터링"]
    end

    Start --> Visit
    Visit --> Login2
    Login2 --> Search
    Visit --> Search
    Search --> List
    List --> Select
    Select --> Chart
    Chart --> AI
    AI --> Quant2
    Select --> Watchlist2
    Watchlist2 --> Alert2
    AI --> Chat
    Quant2 --> Decision
    Decision --> Monitor
    Monitor --> Alert2

    classDef step1 fill:#ffebee,stroke:#c62828
    classDef step2 fill:#e3f2fd,stroke:#1565c0
    classDef step3 fill:#f3e5f5,stroke:#6a1b9a
    classDef step4 fill:#fff3e0,stroke:#ef6c00
    classDef step5 fill:#e8f5e9,stroke:#2e7d32
    
    class Start,Visit,Login2 step1
    class Search,List,Select step2
    class Chart,AI,Quant2 step3
    class Watchlist2,Alert2,Chat step4
    class Decision,Monitor step5
```

### 주요 기능 설명

```mermaid
mindmap
  root((Show Me The Stock))
    실시간 정보
      한국 주식 2,757개
      미국 주식 71개
      실시간 가격 업데이트
      거래량 정보
    AI 분석
      Google AI 기술
      투자 추천
      목표가 제시
      리스크 분석
    퀀트 투자
      재무 지표 분석
      투자 전략 5가지
      백테스트 기능
      맞춤형 추천
    개인화 기능
      관심종목 관리
      실시간 알림
      투자 목표 설정
      AI 챗봇 상담
    편의 기능
      다크/라이트 모드
      모바일 최적화
      Google/GitHub 로그인
      한국어 지원
```

## 배포 아키텍처

```mermaid
graph TB
    subgraph "Production Environment"
        Domain["🌐 ai-stock.po24lio.com"]
        
        subgraph "RKE2 Kubernetes Cluster"
            Ingress["Ingress Controller<br/>- HTTPS 라우팅<br/>- TLS 인증서"]
            
            subgraph "Frontend Pod"
                Frontend["React App<br/>- Nginx<br/>- Static Files"]
            end
            
            subgraph "Backend Pod"
                Backend["FastAPI Server<br/>- Python 3.12<br/>- Uvicorn"]
            end
            
            subgraph "Cache Pod"
                Redis["Redis Cache<br/>- 세션 관리<br/>- API 캐싱"]
            end
        end
        
        subgraph "Database"
            SupabaseCloud["Supabase Cloud<br/>- PostgreSQL<br/>- Auth Service<br/>- Realtime"]
        end
        
        subgraph "External APIs"
            Gemini["Google Gemini API"]
            MarketData["Market Data<br/>- PyKrx<br/>- YFinance"]
        end
    end
    
    Users["사용자"] -->|HTTPS| Domain
    Domain --> Ingress
    Ingress -->|/| Frontend
    Ingress -->|/api| Backend
    Frontend -->|API 호출| Backend
    Frontend -->|인증/DB| SupabaseCloud
    Backend -->|캐싱| Redis
    Backend -->|AI 분석| Gemini
    Backend -->|시장 데이터| MarketData
    Backend -->|사용자 데이터| SupabaseCloud

    classDef user fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef k8s fill:#326ce5,stroke:#1e4ec9,stroke-width:2px
    classDef pod fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef external fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef database fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    
    class Users user
    class Domain,Ingress k8s
    class Frontend,Backend,Redis pod
    class SupabaseCloud database
    class Gemini,MarketData external
```