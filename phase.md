# Show Me The Stock - Supabase 통합 구현 계획

## 프로젝트 정보
- **Supabase URL**: `https://vkhevrykskspbkclbokj.supabase.co`
- **Supabase Anon Key (Public)**: `sb_publishable_TPWwN90FYHsrGeC3yKxJZw_WZT62Oj0`
- **Supabase Service Key (Secret)**: `sb_secret_2edykCta3WIYkcXJ51b7xA_3Fs2L31N` ⚠️ **절대 외부 노출 금지**

## Phase 1: Supabase 프로젝트 설정 및 기본 구성 ✅ 완료

### 1.1 Supabase 프로젝트 생성 ✅
- Supabase 프로젝트 생성 완료
- API 키 획득 완료

### 1.2 데이터베이스 스키마 설계 ✅
```sql
-- 사용자 프로필 테이블
CREATE TABLE profiles (
  id UUID REFERENCES auth.users PRIMARY KEY,
  username TEXT UNIQUE,
  full_name TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 포트폴리오 테이블
CREATE TABLE portfolios (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users NOT NULL,
  stock_symbol TEXT NOT NULL,
  market TEXT CHECK (market IN ('KR', 'US')),
  quantity INTEGER NOT NULL,
  purchase_price DECIMAL(10,2),
  purchase_date DATE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 워치리스트 테이블
CREATE TABLE watchlists (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES auth.users NOT NULL,
  stock_symbol TEXT NOT NULL,
  market TEXT CHECK (market IN ('KR', 'US')),
  added_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(user_id, stock_symbol, market)
);

-- 사용자 설정 테이블
CREATE TABLE user_settings (
  user_id UUID REFERENCES auth.users PRIMARY KEY,
  theme TEXT DEFAULT 'light',
  language TEXT DEFAULT 'ko',
  real_time_alerts BOOLEAN DEFAULT true,
  email_notifications BOOLEAN DEFAULT false,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### 1.3 Row Level Security (RLS) 정책 ✅
```sql
-- 프로필 RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

-- 포트폴리오 RLS
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own portfolio" ON portfolios
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own portfolio" ON portfolios
  FOR ALL USING (auth.uid() = user_id);

-- 워치리스트 RLS
ALTER TABLE watchlists ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own watchlist" ON watchlists
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own watchlist" ON watchlists
  FOR ALL USING (auth.uid() = user_id);

-- 사용자 설정 RLS
ALTER TABLE user_settings ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own settings" ON user_settings
  FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own settings" ON user_settings
  FOR ALL USING (auth.uid() = user_id);
```

## Phase 2: Frontend 인증 시스템 구현 ✅ 완료

### 2.1 환경 변수 설정 ✅
1. **프로젝트 루트에 `.env` 파일 생성** (web-version/frontend/.env)
```bash
REACT_APP_SUPABASE_URL=https://vkhevrykskspbkclbokj.supabase.co
REACT_APP_SUPABASE_ANON_KEY=sb_publishable_TPWwN90FYHsrGeC3yKxJZw_WZT62Oj0
```

2. **.gitignore에 .env 추가 확인** ✅

### 2.2 Supabase 패키지 설치 ✅
```bash
cd web-version/frontend
npm install @supabase/supabase-js @supabase/auth-ui-react @supabase/auth-ui-shared
```

### 2.3 Supabase 클라이언트 설정 ✅
**파일 생성: `src/lib/supabase.ts`**
```typescript
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL!
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
})

// 타입 정의
export type Database = {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string
          username: string | null
          full_name: string | null
          avatar_url: string | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          username?: string | null
          full_name?: string | null
          avatar_url?: string | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          username?: string | null
          full_name?: string | null
          avatar_url?: string | null
          created_at?: string
          updated_at?: string
        }
      }
      portfolios: {
        Row: {
          id: string
          user_id: string
          stock_symbol: string
          market: 'KR' | 'US'
          quantity: number
          purchase_price: number | null
          purchase_date: string | null
          created_at: string
        }
      }
      watchlists: {
        Row: {
          id: string
          user_id: string
          stock_symbol: string
          market: 'KR' | 'US'
          added_at: string
        }
      }
      user_settings: {
        Row: {
          user_id: string
          theme: string
          language: string
          real_time_alerts: boolean
          email_notifications: boolean
          updated_at: string
        }
      }
    }
  }
}
```

### 2.4 AuthContext 생성 ✅
**파일 생성: `src/context/AuthContext.tsx`**
```typescript
import React, { createContext, useContext, useState, useEffect } from 'react'
import { Session, User, AuthError } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signUp: (email: string, password: string, username?: string) => Promise<{ error: AuthError | null }>
  signIn: (email: string, password: string) => Promise<{ error: AuthError | null }>
  signOut: () => Promise<{ error: AuthError | null }>
  updateProfile: (updates: { username?: string; full_name?: string }) => Promise<{ error: Error | null }>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // 초기 세션 확인
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session)
      setUser(session?.user ?? null)
      setLoading(false)
    })

    // 인증 상태 변경 구독
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session)
      setUser(session?.user ?? null)
    })

    return () => subscription.unsubscribe()
  }, [])

  const signUp = async (email: string, password: string, username?: string) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        data: {
          username: username || email.split('@')[0]
        }
      }
    })

    if (!error && data.user) {
      // 프로필 생성
      await supabase.from('profiles').insert({
        id: data.user.id,
        username: username || email.split('@')[0],
        full_name: '',
        avatar_url: ''
      })

      // 기본 설정 생성
      await supabase.from('user_settings').insert({
        user_id: data.user.id
      })
    }

    return { error }
  }

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password
    })
    return { error }
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    return { error }
  }

  const updateProfile = async (updates: { username?: string; full_name?: string }) => {
    if (!user) return { error: new Error('No user logged in') }

    const { error } = await supabase
      .from('profiles')
      .update({ ...updates, updated_at: new Date().toISOString() })
      .eq('id', user.id)

    return { error }
  }

  const value = {
    user,
    session,
    loading,
    signUp,
    signIn,
    signOut,
    updateProfile
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
```

### 2.5 인증 컴포넌트 생성 ✅

#### 2.5.1 로그인 컴포넌트 ✅
**파일 생성: `src/components/auth/LoginView.tsx`**
```typescript
import React, { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { useApp } from '../../context/AppContext'
import './AuthStyles.css'

const LoginView: React.FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  const { signIn } = useAuth()
  const { setCurrentView } = useApp()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const { error } = await signIn(email, password)
    
    if (error) {
      setError(error.message)
    } else {
      setCurrentView('dashboard')
    }
    
    setLoading(false)
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>로그인</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">이메일</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="your@email.com"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">비밀번호</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="••••••••"
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" disabled={loading} className="auth-button">
            {loading ? '로그인 중...' : '로그인'}
          </button>
        </form>

        <p className="auth-link">
          계정이 없으신가요? <a href="#" onClick={() => setCurrentView('signup')}>회원가입</a>
        </p>
      </div>
    </div>
  )
}

export default LoginView
```

#### 2.5.2 회원가입 컴포넌트 ✅
**파일 생성: `src/components/auth/SignupView.tsx`**
```typescript
import React, { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { useApp } from '../../context/AppContext'
import './AuthStyles.css'

const SignupView: React.FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  
  const { signUp } = useAuth()
  const { setCurrentView } = useApp()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    const { error } = await signUp(email, password, username)
    
    if (error) {
      setError(error.message)
    } else {
      setSuccess(true)
    }
    
    setLoading(false)
  }

  if (success) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <h2>회원가입 완료</h2>
          <p>이메일을 확인하여 계정을 활성화해주세요.</p>
          <button onClick={() => setCurrentView('login')} className="auth-button">
            로그인하러 가기
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>회원가입</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">사용자명</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              placeholder="사용자명"
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">이메일</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="your@email.com"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">비밀번호</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="최소 6자 이상"
              minLength={6}
            />
          </div>

          {error && <div className="error-message">{error}</div>}

          <button type="submit" disabled={loading} className="auth-button">
            {loading ? '가입 중...' : '회원가입'}
          </button>
        </form>

        <p className="auth-link">
          이미 계정이 있으신가요? <a href="#" onClick={() => setCurrentView('login')}>로그인</a>
        </p>
      </div>
    </div>
  )
}

export default SignupView
```

#### 2.5.3 프로필 컴포넌트 ✅
**파일 생성: `src/components/auth/ProfileView.tsx`**
```typescript
import React, { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'
import { supabase } from '../../lib/supabase'
import './AuthStyles.css'

interface Profile {
  username: string
  full_name: string
  avatar_url: string
}

const ProfileView: React.FC = () => {
  const { user, signOut, updateProfile } = useAuth()
  const [loading, setLoading] = useState(true)
  const [profile, setProfile] = useState<Profile>({
    username: '',
    full_name: '',
    avatar_url: ''
  })
  const [editing, setEditing] = useState(false)

  useEffect(() => {
    if (user) {
      loadProfile()
    }
  }, [user])

  const loadProfile = async () => {
    if (!user) return

    const { data, error } = await supabase
      .from('profiles')
      .select('username, full_name, avatar_url')
      .eq('id', user.id)
      .single()

    if (data && !error) {
      setProfile(data)
    }
    setLoading(false)
  }

  const handleUpdateProfile = async () => {
    setLoading(true)
    const { error } = await updateProfile({
      username: profile.username,
      full_name: profile.full_name
    })

    if (!error) {
      setEditing(false)
    }
    setLoading(false)
  }

  const handleSignOut = async () => {
    await signOut()
  }

  if (loading) {
    return <div className="loading">프로필 불러오는 중...</div>
  }

  return (
    <div className="profile-container">
      <h2>내 프로필</h2>
      
      <div className="profile-section">
        <div className="profile-info">
          <p><strong>이메일:</strong> {user?.email}</p>
          
          {editing ? (
            <>
              <div className="form-group">
                <label>사용자명</label>
                <input
                  type="text"
                  value={profile.username}
                  onChange={(e) => setProfile({ ...profile, username: e.target.value })}
                />
              </div>
              
              <div className="form-group">
                <label>이름</label>
                <input
                  type="text"
                  value={profile.full_name}
                  onChange={(e) => setProfile({ ...profile, full_name: e.target.value })}
                />
              </div>
              
              <div className="button-group">
                <button onClick={handleUpdateProfile} disabled={loading}>
                  저장
                </button>
                <button onClick={() => setEditing(false)} className="secondary">
                  취소
                </button>
              </div>
            </>
          ) : (
            <>
              <p><strong>사용자명:</strong> {profile.username}</p>
              <p><strong>이름:</strong> {profile.full_name || '미설정'}</p>
              
              <button onClick={() => setEditing(true)}>
                프로필 수정
              </button>
            </>
          )}
        </div>
      </div>

      <button onClick={handleSignOut} className="signout-button">
        로그아웃
      </button>
    </div>
  )
}

export default ProfileView
```

#### 2.5.4 인증 스타일 ✅
**파일 생성: `src/components/auth/AuthStyles.css`**
```css
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: var(--bg-secondary);
}

.auth-card {
  background: var(--bg-primary);
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
}

.auth-card h2 {
  margin-bottom: 1.5rem;
  text-align: center;
  color: var(--text-primary);
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.form-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 1rem;
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.form-group input:focus {
  outline: none;
  border-color: var(--primary-color);
}

.auth-button {
  width: 100%;
  padding: 0.75rem;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.auth-button:hover:not(:disabled) {
  background: var(--primary-hover);
}

.auth-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error-message {
  color: var(--error-color);
  font-size: 0.875rem;
  margin-bottom: 1rem;
  padding: 0.5rem;
  background: rgba(255, 0, 0, 0.1);
  border-radius: 4px;
}

.auth-link {
  text-align: center;
  margin-top: 1rem;
  color: var(--text-secondary);
  font-size: 0.875rem;
}

.auth-link a {
  color: var(--primary-color);
  text-decoration: none;
}

.auth-link a:hover {
  text-decoration: underline;
}

.profile-container {
  padding: 2rem;
  max-width: 600px;
  margin: 0 auto;
}

.profile-section {
  background: var(--bg-secondary);
  padding: 1.5rem;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.profile-info p {
  margin-bottom: 0.75rem;
  color: var(--text-primary);
}

.button-group {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.signout-button {
  background: var(--error-color);
  color: white;
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
}

.signout-button:hover {
  background: var(--error-hover);
}

.loading {
  text-align: center;
  padding: 2rem;
  color: var(--text-secondary);
}
```

### 2.6 ProtectedRoute 컴포넌트 ✅
**파일 생성: `src/components/auth/ProtectedRoute.tsx`**
```typescript
import React from 'react'
import { useAuth } from '../../context/AuthContext'
import { useApp } from '../../context/AppContext'

interface ProtectedRouteProps {
  children: React.ReactNode
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const { user, loading } = useAuth()
  const { setCurrentView } = useApp()

  React.useEffect(() => {
    if (!loading && !user) {
      setCurrentView('login')
    }
  }, [user, loading, setCurrentView])

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  if (!user) {
    return null
  }

  return <>{children}</>
}

export default ProtectedRoute
```

### 2.7 App.tsx 업데이트 ✅
**파일 수정: `src/App.tsx`**
```typescript
import React, { useEffect } from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import Dashboard from './components/Dashboard';
import FloatingChatButton from './components/common/FloatingChatButton';
import './App.css';

const AppContent = () => {
  const { fetchMarketIndices } = useApp();

  useEffect(() => {
    fetchMarketIndices();
  }, [fetchMarketIndices]);

  return (
    <>
      <Dashboard />
      <FloatingChatButton />
    </>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppProvider>
          <div className="App">
            <AppContent />
          </div>
        </AppProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
```

### 2.8 AppContext 업데이트 ✅
**파일에 ViewType 타입 확장 추가: `src/context/AppContext.tsx`**
```typescript
export type ViewType = 'dashboard' | 'stocks' | 'quant' | 'portfolio' | 'watchlist' | 'news' | 'reports' | 'chat' | 'login' | 'signup' | 'profile' | 'auth-callback';
```

### 2.9 ViewManager 업데이트 ✅
**파일 수정: `src/components/ViewManager.tsx`에 인증 뷰 추가**
```typescript
import LoginView from './auth/LoginView';
import SignupView from './auth/SignupView';
import ProfileView from './auth/ProfileView';
import ProtectedRoute from './auth/ProtectedRoute';
import AuthCallback from './auth/AuthCallback';

// content 함수 내부에 추가
case 'login':
  return <LoginView />;
case 'signup':
  return <SignupView />;
case 'auth-callback':
  return <AuthCallback />;
case 'profile':
  return (
    <ProtectedRoute>
      <ProfileView />
    </ProtectedRoute>
  );

// 보호된 라우트에는 ProtectedRoute 컴포넌트 추가
case 'stocks':
  return (
    <ProtectedRoute>
      <StockDetail />
    </ProtectedRoute>
  );
// 기타 보호된 라우트들...
```

### 2.10 Header 컴포넌트 업데이트 ✅
**Header에 로그인/프로필 버튼 추가**
- 로그인하지 않은 경우: 로그인 버튼 표시
- 로그인한 경우: 사용자 프로필 버튼 표시
- Header.css에 스타일 추가

### 2.11 OAuth 콜백 처리 ✅
**파일 생성: `src/components/auth/AuthCallback.tsx`**
- OAuth 로그인 후 리다이렉트 처리
- 프로필 자동 생성
- 세션 확인 및 대시보드 이동

### 2.12 소셜 로그인 통합 ✅
- Google 로그인 버튼 추가
- GitHub 로그인 버튼 추가
- 로그인/회원가입 화면에 소셜 로그인 옵션 표시

## Phase 3: Backend API 보안 및 인증 통합 📋 대기

### 3.1 Backend 환경 변수 설정
### 3.2 Supabase JWT 검증 미들웨어
### 3.3 API 엔드포인트 보호
### 3.4 사용자별 데이터 분리

## Phase 4: 사용자별 데이터 마이그레이션 📋 대기

### 4.1 포트폴리오/워치리스트 마이그레이션
### 4.2 사용자 설정 동기화
### 4.3 채팅 히스토리 저장

## Phase 5: 실시간 기능 및 최적화 📋 대기

### 5.1 실시간 구독 구현
### 5.2 성능 최적화
### 5.3 보안 강화

---

## 다음 단계 (Phase 3 실행 가이드)

Phase 2가 완료되었습니다! 이제 Phase 3를 진행할 수 있습니다.

### Phase 2 완료 사항:
- ✅ Supabase 클라이언트 설정
- ✅ AuthContext 구현 (이메일/소셜 로그인)
- ✅ 로그인/회원가입/프로필 컴포넌트
- ✅ ProtectedRoute로 인증이 필요한 페이지 보호
- ✅ Header에 로그인/프로필 버튼 통합
- ✅ OAuth 콜백 처리 (Google, GitHub)
- ✅ 다크/라이트 모드 지원

### 테스트 방법:
1. **이메일 회원가입**: 회원가입 후 이메일 확인 필요
2. **소셜 로그인**: Google/GitHub 계정으로 즉시 로그인
3. **프로필 수정**: 로그인 후 프로필 버튼 클릭
4. **보호된 라우트**: 로그인하지 않으면 차단됨

## 주의사항

- **시크릿 키는 절대 프론트엔드 코드에 포함하지 마세요**
- 모든 API 키는 환경 변수로 관리
- Supabase 대시보드에서 이메일 템플릿 커스터마이징 가능
- RLS 정책이 제대로 적용되었는지 확인