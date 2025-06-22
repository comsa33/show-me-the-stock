import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import NotificationPanel from './NotificationPanel';
import SearchResults from './SearchResults';
import './Header.css';

interface HeaderProps {
  onToggleSidebar: () => void;
}

const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  const { setSearchTerm, notifications } = useApp();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [localSearchTerm, setLocalSearchTerm] = useState('');
  return (
    <header className="header">
      <div className="header-content">
        {/* Left Section */}
        <div className="header-left">
          <button 
            className="sidebar-toggle"
            onClick={onToggleSidebar}
            aria-label="Toggle sidebar"
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="3" y1="6" x2="21" y2="6"></line>
              <line x1="3" y1="12" x2="21" y2="12"></line>
              <line x1="3" y1="18" x2="21" y2="18"></line>
            </svg>
          </button>
          
          <div className="logo">
            <div className="logo-icon">📈</div>
            <div className="logo-text">
              <h1 className="logo-title gradient-text">Stock Dashboard</h1>
              <span className="logo-subtitle">AI-Powered Analytics</span>
            </div>
          </div>
        </div>

        {/* Center Section - Search */}
        <div className="header-center">
          <div className="search-container">
            <svg className="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.35-4.35"></path>
            </svg>
            <input 
              type="text" 
              placeholder="주식 검색..." 
              className="search-input"
              value={localSearchTerm}
              onChange={(e) => {
                setLocalSearchTerm(e.target.value);
                setSearchTerm(e.target.value);
              }}
              onFocus={() => {
                if (localSearchTerm.trim().length > 0) {
                  setShowSearchResults(true);
                }
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && localSearchTerm.trim().length > 0) {
                  setShowSearchResults(true);
                }
              }}
            />
            {localSearchTerm.trim().length > 0 && (
              <button 
                className="search-clear-btn"
                onClick={() => {
                  setLocalSearchTerm('');
                  setSearchTerm('');
                  setShowSearchResults(false);
                }}
              >
                ×
              </button>
            )}
          </div>
        </div>

        {/* Right Section */}
        <div className="header-right">
          <div className="status-indicator">
            <div className="status-dot status-online"></div>
            <span>실시간</span>
          </div>
          
          <div className="notification-container">
            <button 
              className="notification-btn" 
              aria-label="Notifications"
              onClick={() => setShowNotifications(!showNotifications)}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"></path>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
              </svg>
              {notifications.length > 0 && (
                <span className="notification-badge">{notifications.length}</span>
              )}
            </button>
          </div>

          <div className="user-profile">
            <div className="user-avatar">
              <span>U</span>
            </div>
          </div>
        </div>
      </div>
      
      <NotificationPanel 
        isOpen={showNotifications} 
        onClose={() => setShowNotifications(false)} 
      />
      
      {showSearchResults && (
        <SearchResults 
          query={localSearchTerm}
          onClose={() => setShowSearchResults(false)}
        />
      )}
    </header>
  );
};

export default Header;