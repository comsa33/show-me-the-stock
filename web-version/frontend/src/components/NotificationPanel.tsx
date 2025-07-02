import React from 'react';
import { useApp } from '../context/AppContext';
import './NotificationPanel.css';

interface NotificationPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

const NotificationPanel: React.FC<NotificationPanelProps> = ({ isOpen, onClose }) => {
  const { notifications, removeNotification, clearAllNotifications, isRealTimeEnabled, toggleRealTime } = useApp();

  if (!isOpen) return null;

  const getNotificationIcon = (type: string, category?: string) => {
    if (category === 'price') {
      switch (type) {
        case 'error': return '🔥'; // 급락
        case 'warning': return '📈'; // 상승
        default: return '📊'; // 가격 변동
      }
    }
    if (category === 'market') return '🏛️';
    if (category === 'volume') return '📊';
    if (category === 'ai') return '🤖';
    if (category === 'news') return '📰';
    
    switch (type) {
      case 'success': return '✅';
      case 'warning': return '⚠️';
      case 'error': return '❌';
      default: return 'ℹ️';
    }
  };

  const getPriorityBadge = (priority?: string) => {
    if (!priority || priority === 'low') return null;
    const badges = {
      medium: { text: '중요', class: 'priority-medium' },
      high: { text: '긴급', class: 'priority-high' },
      critical: { text: '매우긴급', class: 'priority-critical' }
    };
    const badge = badges[priority as keyof typeof badges];
    return badge ? <span className={`priority-badge ${badge.class}`}>{badge.text}</span> : null;
  };

  const formatTime = (timestamp: Date) => {
    return timestamp.toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="notification-overlay" onClick={onClose}>
      <div className="notification-panel" onClick={(e) => e.stopPropagation()}>
        <div className="notification-header">
          <div className="header-left">
            <h3>실시간 알림</h3>
            <span className="notification-count">({notifications.length})</span>
          </div>
          <div className="header-actions">
            <button 
              className={`realtime-toggle ${isRealTimeEnabled ? 'active' : ''}`}
              onClick={toggleRealTime}
              title={isRealTimeEnabled ? '실시간 알림 비활성화' : '실시간 알림 활성화'}
            >
              {isRealTimeEnabled ? '🔔' : '🔕'}
            </button>
            {notifications.length > 0 && (
              <button 
                className="clear-all-button"
                onClick={clearAllNotifications}
                title="모든 알림 삭제"
              >
                🗑️
              </button>
            )}
            <button className="close-button" onClick={onClose}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"></line>
                <line x1="6" y1="6" x2="18" y2="18"></line>
              </svg>
            </button>
          </div>
        </div>
        
        <div className="notification-list">
          {!isRealTimeEnabled && (
            <div className="realtime-prompt">
              <div className="prompt-icon">🔔</div>
              <p>실시간 주식 알림을 받으려면 위의 알림 버튼을 클릭하세요</p>
              <button className="enable-realtime-btn" onClick={toggleRealTime}>
                실시간 알림 시작하기
              </button>
            </div>
          )}
          
          {notifications.length === 0 ? (
            <div className="empty-notifications">
              <div className="empty-icon">📬</div>
              <p>{isRealTimeEnabled ? '새로운 알림을 기다리는 중...' : '새로운 알림이 없습니다'}</p>
            </div>
          ) : (
            notifications.map((notification) => (
              <div key={notification.id} className={`notification-item notification-${notification.type} ${notification.priority ? `priority-${notification.priority}` : ''}`}>
                <div className="notification-icon">
                  {getNotificationIcon(notification.type, notification.category)}
                </div>
                <div className="notification-content">
                  <div className="notification-header-row">
                    <div className="notification-title">
                      {notification.title}
                      {notification.symbol && <span className="symbol-tag">{notification.symbol}</span>}
                    </div>
                    {getPriorityBadge(notification.priority)}
                  </div>
                  <div className="notification-message">{notification.message}</div>
                  <div className="notification-meta">
                    <span className="notification-time">{formatTime(notification.timestamp)}</span>
                    {notification.category && (
                      <span className="category-tag">{notification.category}</span>
                    )}
                  </div>
                </div>
                <button 
                  className="notification-remove"
                  onClick={() => removeNotification(notification.id)}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default NotificationPanel;