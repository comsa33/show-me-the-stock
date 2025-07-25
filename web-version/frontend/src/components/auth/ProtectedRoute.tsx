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
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        color: 'var(--text-secondary)'
      }}>
        <div>Loading...</div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return <>{children}</>
}

export default ProtectedRoute