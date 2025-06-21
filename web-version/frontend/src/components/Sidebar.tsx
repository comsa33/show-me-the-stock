import React from 'react';
import { useApp } from '../context/AppContext';
import './Sidebar.css';

interface InterestRate {
  rate: number;
  description: string;
}

interface SidebarProps {
  isOpen: boolean;
  selectedMarket: 'KR' | 'US';
  onMarketChange: (market: 'KR' | 'US') => void;
  interestRates: {
    korea: InterestRate;
    usa: InterestRate;
  };
}

const Sidebar: React.FC<SidebarProps> = ({ 
  isOpen, 
  selectedMarket, 
  onMarketChange, 
  interestRates 
}) => {
  const { currentView, setCurrentView } = useApp();
  
  const menuItems = [
    { id: 'dashboard', label: '대시보드', icon: '📊' },
    { id: 'stocks', label: '주식 분석', icon: '📈' },
    { id: 'portfolio', label: '포트폴리오', icon: '💼' },
    { id: 'watchlist', label: '관심종목', icon: '⭐' },
    { id: 'news', label: '뉴스', icon: '📰' },
    { id: 'reports', label: '리포트', icon: '📋' },
  ];

  const handleNavigation = (viewId: string) => {
    setCurrentView(viewId as any);
  };

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && <div className="sidebar-overlay" onClick={() => {}} />}
      
      <aside className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        {/* Navigation Menu */}
        <nav className="sidebar-nav">
          <ul className="nav-list">
            {menuItems.map((item) => (
              <li key={item.id}>
                <button 
                  onClick={() => handleNavigation(item.id)}
                  className={`nav-item ${currentView === item.id ? 'nav-item-active' : ''}`}
                >
                  <span className="nav-icon">{item.icon}</span>
                  <span className="nav-label">{item.label}</span>
                </button>
              </li>
            ))}
          </ul>
        </nav>

        {/* Market Selector */}
        <div className="market-selector">
          <h3 className="section-title">시장 선택</h3>
          <div className="market-buttons">
            <button 
              className={`market-btn ${selectedMarket === 'KR' ? 'market-btn-active' : ''}`}
              onClick={() => onMarketChange('KR')}
            >
              <span className="market-flag">🇰🇷</span>
              <div className="market-info">
                <span className="market-name">한국</span>
                <span className="market-desc">KOSPI/KOSDAQ</span>
              </div>
            </button>
            
            <button 
              className={`market-btn ${selectedMarket === 'US' ? 'market-btn-active' : ''}`}
              onClick={() => onMarketChange('US')}
            >
              <span className="market-flag">🇺🇸</span>
              <div className="market-info">
                <span className="market-name">미국</span>
                <span className="market-desc">NASDAQ/NYSE</span>
              </div>
            </button>
          </div>
        </div>

        {/* Interest Rates */}
        <div className="interest-rates">
          <h3 className="section-title">금리 정보</h3>
          <div className="rate-cards">
            <div className="rate-card">
              <div className="rate-header">
                <span className="rate-flag">🇰🇷</span>
                <span className="rate-country">한국</span>
              </div>
              <div className="rate-value">{interestRates.korea.rate.toFixed(2)}%</div>
              <div className="rate-desc">기준금리</div>
            </div>
            
            <div className="rate-card">
              <div className="rate-header">
                <span className="rate-flag">🇺🇸</span>
                <span className="rate-country">미국</span>
              </div>
              <div className="rate-value">{interestRates.usa.rate.toFixed(2)}%</div>
              <div className="rate-desc">연방기금금리</div>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="quick-stats">
          <h3 className="section-title">시장 현황</h3>
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-label">KOSPI</div>
              <div className="stat-value status-positive">2,580.45</div>
              <div className="stat-change status-positive">+1.2%</div>
            </div>
            
            <div className="stat-item">
              <div className="stat-label">NASDAQ</div>
              <div className="stat-value status-positive">15,240.83</div>
              <div className="stat-change status-positive">+0.8%</div>
            </div>
            
            <div className="stat-item">
              <div className="stat-label">환율 (USD)</div>
              <div className="stat-value">1,325.50</div>
              <div className="stat-change status-negative">-0.3%</div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sidebar-footer">
          <div className="version-info">
            <span>v2.0.0</span>
            <span>실시간 업데이트</span>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;