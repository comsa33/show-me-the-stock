# Phase 3: 사용자별 기능 구현 (수정안)

## 3.1 관심종목(Watchlist) 기능 ✅ 완료
- 관심종목 추가/제거
- 사용자별 관심종목 저장
- 실시간 가격 업데이트

## 3.2 AI 추천 추적 시스템 (포트폴리오 대체)

### 목적
실제 매매 기능 없이도 AI/퀀트 추천의 성과를 추적하고 비교할 수 있는 시스템

### 테이블 구조
```sql
-- AI 추천 추적
CREATE TABLE recommendation_tracking (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  recommendation_id UUID NOT NULL,
  stock_symbol VARCHAR(20) NOT NULL,
  market VARCHAR(10) NOT NULL,
  recommendation_type VARCHAR(50) NOT NULL, -- 'ai_analysis', 'quant_value', 'quant_momentum' 등
  recommendation_date TIMESTAMP NOT NULL,
  recommended_price DECIMAL(15,2) NOT NULL,
  target_price DECIMAL(15,2),
  stop_loss_price DECIMAL(15,2),
  recommendation_reason TEXT,
  current_price DECIMAL(15,2),
  performance_percent DECIMAL(8,2),
  status VARCHAR(20) DEFAULT 'tracking', -- 'tracking', 'target_reached', 'stopped_out', 'expired'
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 퀀트 전략 시뮬레이션
CREATE TABLE strategy_simulations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  strategy_name VARCHAR(100) NOT NULL,
  strategy_type VARCHAR(50) NOT NULL, -- 'value', 'momentum', 'quality', 'low_volatility', 'custom'
  initial_capital DECIMAL(15,2) DEFAULT 10000000, -- 1천만원 기본
  current_value DECIMAL(15,2),
  total_return_percent DECIMAL(8,2),
  sharpe_ratio DECIMAL(8,4),
  max_drawdown_percent DECIMAL(8,2),
  win_rate_percent DECIMAL(8,2),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 시뮬레이션 거래 내역
CREATE TABLE simulation_transactions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  simulation_id UUID REFERENCES strategy_simulations(id) NOT NULL,
  stock_symbol VARCHAR(20) NOT NULL,
  market VARCHAR(10) NOT NULL,
  transaction_type VARCHAR(10) NOT NULL, -- 'buy', 'sell'
  quantity INTEGER NOT NULL,
  price DECIMAL(15,2) NOT NULL,
  transaction_date TIMESTAMP NOT NULL,
  ai_score DECIMAL(5,2), -- AI 신뢰도 점수
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 주요 기능
1. **AI 추천 추적**
   - AI가 추천한 종목의 성과 자동 추적
   - 목표가/손절가 도달 시 알림
   - 추천 이유와 성과 히스토리 관리

2. **전략 시뮬레이션**
   - 퀀트 전략별 가상 포트폴리오 운영
   - 실제 시장 데이터 기반 성과 측정
   - 여러 전략 성과 비교 대시보드

3. **성과 분석**
   - 추천 정확도 통계
   - 전략별 수익률 비교
   - 리스크 지표 (샤프 비율, 최대 낙폭 등)

## 3.3 투자 목표 관리 시스템

### 테이블 구조
```sql
-- 투자 목표 설정
CREATE TABLE investment_goals (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users(id) NOT NULL,
  goal_name VARCHAR(200) NOT NULL,
  goal_type VARCHAR(50) NOT NULL, -- 'retirement', 'house', 'education', 'wealth', 'custom'
  target_amount DECIMAL(15,2) NOT NULL,
  current_amount DECIMAL(15,2) DEFAULT 0,
  monthly_investment DECIMAL(15,2),
  target_date DATE NOT NULL,
  risk_level VARCHAR(20) NOT NULL, -- 'conservative', 'moderate', 'aggressive'
  preferred_sectors TEXT[], -- ['IT', 'BIO', 'FINANCE'] 등
  excluded_sectors TEXT[],
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- 목표별 추천 종목
CREATE TABLE goal_recommendations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  goal_id UUID REFERENCES investment_goals(id) NOT NULL,
  stock_symbol VARCHAR(20) NOT NULL,
  market VARCHAR(10) NOT NULL,
  recommendation_score DECIMAL(5,2) NOT NULL, -- 0-100
  match_reasons TEXT[], -- ['높은 배당률', '안정적 성장', '낮은 변동성'] 등
  created_at TIMESTAMP DEFAULT NOW()
);
```

### 주요 기능
1. **목표 설정 위저드**
   - 은퇴 자금, 주택 구입 등 템플릿 제공
   - 리스크 성향 평가 설문
   - 목표 달성 예상 시뮬레이션

2. **맞춤형 종목 추천**
   - 목표와 리스크 성향에 맞는 종목 추천
   - 섹터 선호도 반영
   - 정기적 리밸런싱 제안

## 3.4 실시간 알림 시스템 활성화

### 구현 상태
- ✅ 백엔드 WebSocket 서버 구현 완료
- ✅ 프론트엔드 NotificationService 구현 완료
- ⚠️ 실제 연동 및 UI 통합 필요

### 활성화 작업
1. **WebSocket 연결 통합**
   ```typescript
   // App.tsx에서 NotificationService 초기화
   useEffect(() => {
     if (user) {
       const notificationService = NotificationService.getInstance();
       notificationService.startRealTimeAlerts();
       
       // 관심종목 동기화
       watchlistItems.forEach(item => {
         notificationService.addToWatchlist(item.stock_symbol);
       });
     }
   }, [user, watchlistItems]);
   ```

2. **알림 UI 컴포넌트**
   - 토스트 알림 컴포넌트
   - 알림 센터 (히스토리 보기)
   - 알림 설정 페이지

3. **Supabase 통합 (선택사항)**
   - 알림 히스토리 저장
   - 사용자별 알림 설정 저장
   ```sql
   CREATE TABLE notification_history (
     id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
     user_id UUID REFERENCES auth.users(id) NOT NULL,
     alert_type VARCHAR(50) NOT NULL,
     stock_symbol VARCHAR(20),
     title VARCHAR(200) NOT NULL,
     message TEXT NOT NULL,
     priority VARCHAR(20) NOT NULL,
     is_read BOOLEAN DEFAULT FALSE,
     created_at TIMESTAMP DEFAULT NOW()
   );
   
   CREATE TABLE notification_settings (
     user_id UUID REFERENCES auth.users(id) PRIMARY KEY,
     price_alerts_enabled BOOLEAN DEFAULT TRUE,
     price_threshold_percent DECIMAL(5,2) DEFAULT 3.0,
     volume_alerts_enabled BOOLEAN DEFAULT TRUE,
     news_alerts_enabled BOOLEAN DEFAULT TRUE,
     ai_alerts_enabled BOOLEAN DEFAULT TRUE,
     quiet_hours_start TIME,
     quiet_hours_end TIME,
     updated_at TIMESTAMP DEFAULT NOW()
   );
   ```

## 구현 우선순위

1. **Phase 3.2** - AI 추천 추적 시스템 (2-3일)
   - 가장 앱의 성격에 맞는 기능
   - 기존 AI 분석과 자연스럽게 연결
   
2. **Phase 3.4** - 실시간 알림 활성화 (1-2일)
   - 이미 대부분 구현되어 있음
   - UI 통합만 필요

3. **Phase 3.3** - 투자 목표 관리 (3-4일)
   - 장기적 사용자 인게이지먼트 향상
   - 개인화된 경험 제공

## 예상 사이드 이펙트 및 대응

1. **성능 고려사항**
   - WebSocket 연결 수 제한 필요
   - 알림 빈도 제한 (rate limiting)
   - 배치 업데이트로 DB 부하 감소

2. **데이터 정합성**
   - 추천 추적 시 실시간 가격 업데이트 필요
   - 일일 배치로 성과 지표 계산
   - 오래된 추천 자동 만료 처리

3. **사용자 경험**
   - 명확한 "시뮬레이션" 표시로 혼란 방지
   - 교육 콘텐츠로 기능 이해도 향상
   - 단계별 온보딩 제공