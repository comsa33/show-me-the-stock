import React, { useEffect, useState } from 'react'
import { supabase } from '../../lib/supabase'
import { useAuth } from '../../context/AuthContext'

const SessionDebug: React.FC = () => {
  const { user, session, loading: authLoading } = useAuth()
  const [sessionInfo, setSessionInfo] = useState<any>(null)
  const [sessionError, setSessionError] = useState<string | null>(null)
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    const checkSession = async () => {
      try {
        const { data: { session }, error } = await supabase.auth.getSession()
        
        if (error) {
          setSessionError(error.message)
        } else {
          setSessionInfo({
            hasSession: !!session,
            userId: session?.user?.id,
            email: session?.user?.email,
            provider: session?.user?.app_metadata?.provider,
            expiresAt: session?.expires_at,
            isExpired: session ? new Date(session.expires_at! * 1000) < new Date() : null
          })
        }
      } catch (err: any) {
        setSessionError(err.message)
      } finally {
        setChecking(false)
      }
    }

    checkSession()

    // Re-check every 5 seconds
    const interval = setInterval(checkSession, 5000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div style={{
      position: 'fixed',
      bottom: 20,
      right: 20,
      background: 'rgba(0,0,0,0.8)',
      color: 'white',
      padding: '10px',
      borderRadius: '5px',
      fontSize: '12px',
      maxWidth: '300px',
      zIndex: 9999
    }}>
      <h4 style={{ margin: '0 0 10px 0' }}>Session Debug</h4>
      
      <div>AuthContext Loading: {authLoading ? 'Yes' : 'No'}</div>
      <div>AuthContext User: {user ? user.email : 'null'}</div>
      <div>AuthContext Session: {session ? 'Present' : 'null'}</div>
      
      <hr style={{ margin: '10px 0' }} />
      
      {checking ? (
        <div>Checking session...</div>
      ) : sessionError ? (
        <div style={{ color: 'red' }}>Error: {sessionError}</div>
      ) : sessionInfo ? (
        <>
          <div>Has Session: {sessionInfo.hasSession ? 'Yes' : 'No'}</div>
          <div>User ID: {sessionInfo.userId || 'N/A'}</div>
          <div>Email: {sessionInfo.email || 'N/A'}</div>
          <div>Provider: {sessionInfo.provider || 'N/A'}</div>
          <div>Expired: {sessionInfo.isExpired !== null ? (sessionInfo.isExpired ? 'Yes' : 'No') : 'N/A'}</div>
        </>
      ) : (
        <div>No session info</div>
      )}
      
      <hr style={{ margin: '10px 0' }} />
      
      <div style={{ fontSize: '10px' }}>
        Last updated: {new Date().toLocaleTimeString()}
      </div>
    </div>
  )
}

export default SessionDebug