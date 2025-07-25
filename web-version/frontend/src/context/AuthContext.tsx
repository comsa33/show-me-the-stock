import React, { createContext, useContext, useState, useEffect } from 'react'
import { Session, User, AuthError } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'
import { isInAppBrowser, openInExternalBrowser } from '../utils/browserDetect'

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signUp: (email: string, password: string, username?: string) => Promise<{ error: AuthError | null }>
  signIn: (email: string, password: string) => Promise<{ error: AuthError | null }>
  signInWithGoogle: () => Promise<{ error: AuthError | null }>
  signInWithGitHub: () => Promise<{ error: AuthError | null }>
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
    let mounted = true

    // 프로필 확인 및 생성 함수
    const checkAndCreateProfile = async (user: User) => {
      if (!user || !mounted) return

      try {
        // 프로필 존재 확인
        const { data: existingProfile } = await supabase
          .from('profiles')
          .select('id')
          .eq('id', user.id)
          .single()

        if (!existingProfile) {
          // 프로필이 없으면 생성
          const { error: profileError } = await supabase.from('profiles').insert({
            id: user.id,
            username: user.email?.split('@')[0] || '',
            full_name: user.user_metadata?.full_name || '',
            avatar_url: user.user_metadata?.avatar_url || ''
          })

          // user_settings 테이블에도 레코드 생성
          if (!profileError && mounted) {
            const { data: existingSettings } = await supabase
              .from('user_settings')
              .select('user_id')
              .eq('user_id', user.id)
              .single()

            if (!existingSettings) {
              await supabase.from('user_settings').insert({
                user_id: user.id
              })
            }
          }
        }
      } catch (error) {
        // Silent error handling
      }
    }

    // 초기 세션 확인 - 즉시 로딩 해제
    const initializeSession = async () => {
      try {
        // 먼저 로컬 세션 확인 (빠른 응답)
        const { data: { session }, error } = await supabase.auth.getSession()
        
        if (error) {
          // Error getting session
          if (mounted) {
            setLoading(false)
          }
          return
        }
        
        if (mounted) {
          setSession(session)
          setUser(session?.user ?? null)
          setLoading(false) // 즉시 로딩 해제
        }
        
        // 프로필 생성은 백그라운드에서 처리
        if (session?.user && mounted) {
          checkAndCreateProfile(session.user)
        }
      } catch (error) {
        // Error initializing session
        if (mounted) {
          setLoading(false)
        }
      }
    }
    
    initializeSession()

    // 인증 상태 변경 구독
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (_event, session) => {
      if (!mounted) return
      
      setSession(session)
      setUser(session?.user ?? null)
      
      // 로그인 이벤트 시 프로필 확인 및 생성 (백그라운드)
      if (_event === 'SIGNED_IN' && session?.user && mounted) {
        checkAndCreateProfile(session.user)
      }
    })

    return () => {
      mounted = false
      subscription.unsubscribe()
    }
  }, [])

  const signUp = async (email: string, password: string, username?: string) => {
    try {
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            username: username || email.split('@')[0]
          }
        }
      })

      // 트리거가 프로필을 생성하므로 여기서는 생성하지 않음
      // 만약 트리거가 없거나 실패했을 경우를 위한 백업으로만 checkAndCreateProfile 사용

      return { error }
    } catch (err) {
      return { error: err as AuthError }
    }
  }

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password
    })
    return { error }
  }

  const signInWithGoogle = async () => {
    // Check if we're in an in-app browser
    if (isInAppBrowser()) {
      // For in-app browsers, we need to open in external browser
      const { data } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth-callback`,
          skipBrowserRedirect: true
        }
      })
      
      if (data?.url) {
        // Try to open in external browser
        openInExternalBrowser(data.url);
        
        // Also show a message to the user
        return { 
          error: {
            message: '인앱 브라우저에서는 구글 로그인이 제한됩니다. 기본 브라우저에서 다시 시도해주세요.',
            status: 403
          } as AuthError 
        };
      }
    }
    
    // Normal flow for regular browsers
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth-callback`
      }
    })
    return { error }
  }

  const signInWithGitHub = async () => {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'github',
      options: {
        redirectTo: `${window.location.origin}/auth-callback`
      }
    })
    return { error }
  }

  const signOut = async () => {
    const { error } = await supabase.auth.signOut()
    return { error }
  }

  const updateProfile = async (updates: { username?: string; full_name?: string }) => {
    if (!user) return { error: new Error('No user logged in') }

    try {
      // 먼저 프로필이 존재하는지 확인
      const { data: existingProfile } = await supabase
        .from('profiles')
        .select('id')
        .eq('id', user.id)
        .single()

      if (!existingProfile) {
        // 프로필이 없으면 insert
        const { error } = await supabase
          .from('profiles')
          .insert({
            id: user.id,
            ...updates,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          })
        return { error }
      } else {
        // 프로필이 있으면 update
        const { error } = await supabase
          .from('profiles')
          .update({ ...updates, updated_at: new Date().toISOString() })
          .eq('id', user.id)
        return { error }
      }
    } catch (error) {
      return { error: error as Error }
    }
  }

  const value = {
    user,
    session,
    loading,
    signUp,
    signIn,
    signInWithGoogle,
    signInWithGitHub,
    signOut,
    updateProfile
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}