import React, { useState, useEffect } from 'react'
import { useAuth } from '../../context/AuthContext'
import { useApp } from '../../context/AppContext'
import { supabase } from '../../lib/supabase'
import './AuthStyles.css'

interface Profile {
  username: string
  full_name: string
  avatar_url: string
}

const ProfileView: React.FC = () => {
  const { user, signOut, updateProfile } = useAuth()
  const { setCurrentView } = useApp()
  const [loading, setLoading] = useState(true)
  const [profile, setProfile] = useState<Profile>({
    username: '',
    full_name: '',
    avatar_url: ''
  })
  const [editing, setEditing] = useState(false)

  useEffect(() => {
    const fetchProfile = async () => {
      if (!user) {
        setLoading(false)
        return
      }

      setLoading(true)
      
      try {
        const { data, error } = await supabase
          .from('profiles')
          .select('username, full_name, avatar_url')
          .eq('id', user.id)
          .single()

        if (data && !error) {
          setProfile(data)
        } else if (error && error.code === 'PGRST116') {
          // 프로필이 없는 경우 (소셜 로그인 사용자일 수 있음)
          // 기본값 설정
          setProfile({
            username: user.email?.split('@')[0] || '',
            full_name: user.user_metadata?.full_name || '',
            avatar_url: user.user_metadata?.avatar_url || ''
          })
          
          // 프로필 생성 시도
          const { error: createError } = await supabase.from('profiles').insert({
            id: user.id,
            username: user.email?.split('@')[0] || '',
            full_name: user.user_metadata?.full_name || '',
            avatar_url: user.user_metadata?.avatar_url || ''
          })
          
          if (!createError) {
            // user_settings도 생성
            await supabase.from('user_settings').insert({
              user_id: user.id
            })
          }
        } else if (error) {
          // 다른 에러의 경우 - 에러가 있어도 기본값으로 프로필 표시
          setProfile({
            username: user.email?.split('@')[0] || '',
            full_name: '',
            avatar_url: ''
          })
        }
      } catch (err) {
        // 예외 발생 시에도 기본값 설정
        setProfile({
          username: user?.email?.split('@')[0] || '',
          full_name: '',
          avatar_url: ''
        })
      } finally {
        setLoading(false)
      }
    }

    fetchProfile()
  }, [user])


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
    setCurrentView('login')
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
                  value={profile.username || ''}
                  onChange={(e) => setProfile({ ...profile, username: e.target.value })}
                />
              </div>
              
              <div className="form-group">
                <label>이름</label>
                <input
                  type="text"
                  value={profile.full_name || ''}
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
              <p><strong>사용자명:</strong> {profile.username || '미설정'}</p>
              <p><strong>이름:</strong> {profile.full_name || '미설정'}</p>
              <p><strong>가입일:</strong> {user?.created_at ? new Date(user.created_at).toLocaleDateString('ko-KR') : ''}</p>
              <p><strong>인증 방법:</strong> {user?.app_metadata?.provider || 'email'}</p>
              
              <button onClick={() => setEditing(true)} className="auth-button secondary">
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