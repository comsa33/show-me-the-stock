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
  const [headerOpacity, setHeaderOpacity] = useState(1);
  const lastScrollY = useRef(0);
  const lastActivityTime = useRef(Date.now());
  const inactivityTimer = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const isMobile = window.innerWidth <= 768;
    
    const resetActivityTimer = () => {
      lastActivityTime.current = Date.now();
      if (isMobile) {
        setHeaderOpacity(1);
        setIsHeaderVisible(true);
        
        // 기존 타이머 취소
        if (inactivityTimer.current) {
          clearTimeout(inactivityTimer.current);
        }
        
        // 3초 후 투명도 감소 시작
        inactivityTimer.current = setTimeout(() => {
          if (window.scrollY > 50) {
            setHeaderOpacity(0.1);
          }
        }, 3000);
      }
    };

    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      const scrollThreshold = isMobile ? 50 : 80;
      
      // 모바일에서 스크롤 다운 시 투명도 처리
      if (isMobile) {
        if (currentScrollY > lastScrollY.current && currentScrollY > scrollThreshold) {
          // 스크롤 다운 - 점진적으로 투명해짐
          const opacity = Math.max(0.1, 1 - (currentScrollY - scrollThreshold) / 100);
          setHeaderOpacity(opacity);
        } else if (currentScrollY < lastScrollY.current) {
          // 스크롤 업 - 즉시 보이게
          resetActivityTimer();
        }
      } else {
        // 데스크톱에서는 기존 방식
        if (currentScrollY > lastScrollY.current && currentScrollY > scrollThreshold) {
          setIsHeaderVisible(false);
        } else if (currentScrollY < lastScrollY.current || currentScrollY <= scrollThreshold) {
          setIsHeaderVisible(true);
        }
      }
      
      lastScrollY.current = currentScrollY;
    };

    const handleActivity = () => {
      if (isMobile) {
        resetActivityTimer();
      }
    };

    // 이벤트 리스너 등록
    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('touchstart', handleActivity);
    window.addEventListener('touchmove', handleActivity);
    window.addEventListener('click', handleActivity);
    
    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('touchstart', handleActivity);
      window.removeEventListener('touchmove', handleActivity);
      window.removeEventListener('click', handleActivity);
      if (inactivityTimer.current) {
        clearTimeout(inactivityTimer.current);
      }
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
      style={{ 
        opacity: window.innerWidth <= 768 ? headerOpacity : undefined,
        transition: 'opacity 0.3s ease-in-out'
      }}
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