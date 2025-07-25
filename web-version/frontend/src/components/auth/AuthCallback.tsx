import React, { useEffect } from 'react'
import { useApp } from '../../context/AppContext'
import { supabase } from '../../lib/supabase'

const AuthCallback: React.FC = () => {
  const { setCurrentView } = useApp()

  useEffect(() => {
    // Handle the OAuth callback
    const handleCallback = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession()
        
        if (error) {
          console.error('Auth callback error:', error)
          setCurrentView('login')
          return
        }

        if (session) {
          // Check if profile exists
          const { data: profile } = await supabase
            .from('profiles')
            .select('id')
            .eq('id', session.user.id)
            .single()

          if (!profile) {
            // Create profile for OAuth users
            await supabase.from('profiles').insert({
              id: session.user.id,
              username: session.user.email?.split('@')[0] || '',
              full_name: session.user.user_metadata?.full_name || '',
              avatar_url: session.user.user_metadata?.avatar_url || ''
            })

            // Create default settings
            await supabase.from('user_settings').insert({
              user_id: session.user.id
            })
          }

          setCurrentView('dashboard')
        } else {
          setCurrentView('login')
        }
      } catch (error) {
        console.error('Callback error:', error)
        setCurrentView('login')
      }
    }

    handleCallback()
  }, [setCurrentView])

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      color: 'var(--text-secondary)'
    }}>
      <div>인증 처리 중...</div>
    </div>
  )
}

export default AuthCallback