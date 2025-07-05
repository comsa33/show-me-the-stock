import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { useTheme } from '../context/ThemeContext';
import NotificationPanel from './NotificationPanel';
import SearchResults from './SearchResults';
import { Menu, Search, X, Bell, User, Sun, Moon } from 'lucide-react';
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

  // Scroll detection for header visibility
  const [isHeaderVisible, setIsHeaderVisible] = useState(true);
  const lastScrollY = useRef(0);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      const scrollThreshold = 50;
      
      // 스크롤 방향에 따라 헤더 표시/숨김
      if (currentScrollY > lastScrollY.current && currentScrollY > scrollThreshold) {
        // 스크롤 다운 - 헤더 숨김
        setIsHeaderVisible(false);
      } else if (currentScrollY < lastScrollY.current) {
        // 스크롤 업 - 헤더 표시
        setIsHeaderVisible(true);
      }
      
      lastScrollY.current = currentScrollY;
    };

    // 이벤트 리스너 등록
    window.addEventListener('scroll', handleScroll, { passive: true });
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const term = e.target.value;
    setLocalSearchTerm(term);
    setSearchTerm(term);
    setShowSearchResults(term.length > 0);
  };

  const clearSearch = () => {
    setLocalSearchTerm('');
    setSearchTerm('');
    setShowSearchResults(false);
  };

  return (
    <header 
      className={`header ${isHeaderVisible ? 'header-visible' : 'header-hidden'}`}
    >
      <div className="header-content">
        <div className="header-left">
          <button className="sidebar-toggle" onClick={onToggleSidebar} aria-label="Toggle sidebar">
            <Menu size={24} />
          </button>
        </div>

        <div className="header-center">
          <div className="search-container">
            <Search className="search-icon" size={20} />
            <input
              type="text"
              placeholder="Search stocks..."
              className="search-input"
              value={localSearchTerm}
              onChange={handleSearchChange}
              onFocus={() => setShowSearchResults(localSearchTerm.length > 0)}
            />
            {localSearchTerm && (
              <button className="search-clear-btn" onClick={clearSearch} aria-label="Clear search">
                <X size={16} />
              </button>
            )}
          </div>
        </div>

        <div className="header-right">
          <button className="theme-toggle-btn" onClick={toggleTheme} aria-label="Toggle theme">
            {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
          </button>
          <div className="notification-container">
            <button className="notification-btn" onClick={() => setShowNotifications(!showNotifications)} aria-label="Notifications">
              <Bell size={20} />
              {notifications.length > 0 && <span className="notification-badge">{notifications.length}</span>}
            </button>
          </div>
          <div className="user-profile">
            <div className="user-avatar"><User size={20} /></div>
          </div>
        </div>
      </div>

      <NotificationPanel isOpen={showNotifications} onClose={() => setShowNotifications(false)} />
      {showSearchResults && <SearchResults query={localSearchTerm} onClose={() => setShowSearchResults(false)} />}
    </header>
  );
};

export default Header;