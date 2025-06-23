import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { useTheme } from '../context/ThemeContext';
import NotificationPanel from './NotificationPanel';
import SearchResults from './SearchResults';
import { Menu, TrendingUp, Search, X, Bell, User, Sun, Moon } from 'lucide-react';
import './Header.css';

interface HeaderProps {
  onToggleSidebar: () => void;
}

const Header: React.FC<HeaderProps> = ({ onToggleSidebar }) => {
  const { setSearchTerm, notifications } = useApp();
  const { theme, toggleTheme } = useTheme();
  const [showNotifications, setShowNotifications] = useState(false);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [localSearchTerm, setLocalSearchTerm] = useState('');
  const [isScrolled, setIsScrolled] = useState(false);
  const [lastScrollY, setLastScrollY] = useState(0);
  const [headerVisible, setHeaderVisible] = useState(true);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      
      // 모바일에서만 적용
      if (window.innerWidth <= 768) {
        setIsScrolled(currentScrollY > 50);
        
        // 스크롤 방향에 따라 헤더 표시/숨김
        if (currentScrollY > lastScrollY && currentScrollY > 100) {
          setHeaderVisible(false);
        } else {
          setHeaderVisible(true);
        }
      } else {
        setIsScrolled(false);
        setHeaderVisible(true);
      }
      
      setLastScrollY(currentScrollY);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [lastScrollY]);
  return (
    <header className={`header ${isScrolled ? 'header-compact' : ''} ${!headerVisible ? 'header-hidden' : ''}`}>
      <div className="header-content">
        {/* Left Section */}
        <div className="header-left">
          <button 
            className="sidebar-toggle"
            onClick={onToggleSidebar}
            aria-label="Toggle sidebar"
          >
            <Menu size={24} />
          </button>
          
          <div className={`logo ${isScrolled ? 'logo-compact' : ''}`}>
            <div className="logo-icon">
              <TrendingUp size={isScrolled ? 28 : 32} className="gradient-text" />
            </div>
            <div className="logo-text">
              <h1 className="logo-title gradient-text">Stock Dashboard</h1>
              <span className="logo-subtitle">AI-Powered Analytics</span>
            </div>
          </div>
        </div>

        {/* Center Section - Search */}
        <div className="header-center">
          <div className="search-container">
            <Search className="search-icon" size={20} />
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
                <X size={16} />
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

          <button 
            className="theme-toggle-btn"
            onClick={toggleTheme}
            aria-label="Toggle theme"
          >
            {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
          </button>
          
          <div className="notification-container">
            <button 
              className="notification-btn" 
              aria-label="Notifications"
              onClick={() => setShowNotifications(!showNotifications)}
            >
              <Bell size={20} />
              {notifications.length > 0 && (
                <span className="notification-badge">{notifications.length}</span>
              )}
            </button>
          </div>

          <div className="user-profile">
            <div className="user-avatar">
              <User size={20} />
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