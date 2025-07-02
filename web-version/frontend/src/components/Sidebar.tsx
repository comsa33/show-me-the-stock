import React from 'react';
import { useApp } from '../context/AppContext';
import { BarChart3, TrendingUp, Briefcase, Star, Newspaper, FileText, Calculator } from 'lucide-react';
import './Sidebar.css';

const StockLogo = () => (
  <svg width="32" height="32" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <linearGradient id="sidebarLogoGradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#8B5CF6" />
        <stop offset="50%" stopColor="#A855F7" />
        <stop offset="100%" stopColor="#C084FC" />
      </linearGradient>
      <linearGradient id="sidebarLogoGradientBg" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.1" />
        <stop offset="100%" stopColor="#C084FC" stopOpacity="0.2" />
      </linearGradient>
    </defs>
    
    {/* Background Circle */}
    <circle cx="18" cy="18" r="16" fill="url(#sidebarLogoGradientBg)" stroke="url(#sidebarLogoGradient)" strokeWidth="1.5"/>
    
    {/* Chart Background */}
    <rect x="8" y="12" width="20" height="14" rx="2" fill="url(#sidebarLogoGradientBg)" stroke="url(#sidebarLogoGradient)" strokeWidth="1" strokeOpacity="0.3"/>
    
    {/* Rising Stock Chart Lines */}
    <path d="M10 22L13 19L16 21L20 16L24 14L26 12" stroke="url(#sidebarLogoGradient)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
    
    {/* Chart Points */}
    <circle cx="13" cy="19" r="2" fill="url(#sidebarLogoGradient)"/>
    <circle cx="20" cy="16" r="2" fill="url(#sidebarLogoGradient)"/>
    <circle cx="26" cy="12" r="2" fill="url(#sidebarLogoGradient)"/>
    
    {/* Trend Arrow */}
    <path d="M22 10L26 10L26 14" stroke="url(#sidebarLogoGradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
    <path d="M22 14L26 10" stroke="url(#sidebarLogoGradient)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" fill="none"/>
  </svg>
);

interface InterestRate {
  rate: number;
  description: string;
}

interface SidebarProps {
  isOpen: boolean;
  selectedMarket: 'KR' | 'US';
  onMarketChange: (market: 'KR' | 'US') => void;
  interestRates?: {
    korea?: InterestRate;
    usa?: InterestRate;
  };
  onClose: () => void;
}

interface MarketStatsProps {
  selectedMarket: 'KR' | 'US';
}

const MarketStats: React.FC<MarketStatsProps> = ({ selectedMarket }) => {
  const { marketIndices, marketIndicesLoading: loading } = useApp();
  const marketData = selectedMarket === 'KR' ? marketIndices.korea : marketIndices.us;

  if (loading) {
    return (
      <div className="stats-grid">
        <div className="stat-item loading-placeholder" />
        <div className="stat-item loading-placeholder" />
        <div className="stat-item loading-placeholder" />
      </div>
    );
  }

  if (!marketData || marketData.length === 0) {
    return (
      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-label">데이터 없음</div>
          <div className="stat-value">-</div>
        </div>
      </div>
    );
  }

  return (
    <div className="stats-grid">
      {marketData.slice(0, 3).map((item) => {
        if (!item) return null;
        return (
          <div key={item.symbol || Math.random()} className="stat-item">
            <div className="stat-label">{item.name || item.symbol || '알 수 없음'}</div>
            <div className="stat-value-container">
              <div className="stat-value">
                {typeof item.current_price === 'number' ? item.current_price.toLocaleString(undefined, { maximumFractionDigits: 2 }) : '0'}
              </div>
              <div className={`stat-change ${(item.change_percent || 0) >= 0 ? 'status-positive' : 'status-negative'}`}>
                {(item.change_percent || 0) >= 0 ? '+' : ''}{(item.change_percent || 0).toFixed(2)}%
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

const Sidebar: React.FC<SidebarProps> = ({ 
  isOpen, 
  selectedMarket, 
  onMarketChange, 
  interestRates, 
  onClose
}) => {
  const { currentView, setCurrentView } = useApp();

  const menuItems = [
    { id: 'dashboard', label: '대시보드', icon: BarChart3 },
    { id: 'stocks', label: '주식 분석', icon: TrendingUp },
    { id: 'quant', label: '퀀트 투자', icon: Calculator },
    { id: 'portfolio', label: '포트폴리오', icon: Briefcase },
    { id: 'watchlist', label: '관심종목', icon: Star },
    { id: 'news', label: '뉴스', icon: Newspaper },
    { id: 'reports', label: '리포트', icon: FileText },
  ];

  const handleNavigation = (viewId: string) => {
    setCurrentView(viewId as any);
    if (window.innerWidth <= 1024) {
      onClose();
    }
  };

  return (
    <>
      <aside className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-logo">
          <StockLogo />
          <h1 className="sidebar-logo-title">ShowMeTheStock</h1>
        </div>
        
        <nav className="sidebar-nav">
          <h3 className="nav-title">메뉴</h3>
          <ul className="nav-list">
            {menuItems.map((item) => (
              <li key={item.id}>
                <button 
                  onClick={() => handleNavigation(item.id)}
                  className={`nav-item ${currentView === item.id ? 'nav-item-active' : ''}`}
                >
                  <item.icon size={20} className="nav-icon" />
                  <span className="nav-label">{item.label}</span>
                </button>
              </li>
            ))}
          </ul>
        </nav>

        <div className="sidebar-section">
          <h3 className="section-title">시장 선택</h3>
          <div className="market-buttons">
            <button 
              className={`market-btn ${selectedMarket === 'KR' ? 'market-btn-active' : ''}`}
              onClick={() => onMarketChange('KR')}
            >
              한국 (KR)
            </button>
            <button 
              className={`market-btn ${selectedMarket === 'US' ? 'market-btn-active' : ''}`}
              onClick={() => onMarketChange('US')}
            >
              미국 (US)
            </button>
          </div>
        </div>

        <div className="sidebar-section">
          <h3 className="section-title">시장 현황</h3>
          <MarketStats selectedMarket={selectedMarket} />
        </div>

        <div className="sidebar-footer">
          <div className="version-info">
            <span>Version 2.0.0</span>
          </div>
        </div>
      </aside>
      
      <div className={`sidebar-overlay ${isOpen ? 'overlay-visible' : ''}`} onClick={onClose} />
    </>
  );
};

export default Sidebar;
