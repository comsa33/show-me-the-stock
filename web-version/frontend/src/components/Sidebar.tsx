import React from 'react';
import { useApp } from '../context/AppContext';
import { BarChart3, TrendingUp, Briefcase, Star, Newspaper, FileText, Calculator } from 'lucide-react';
import './Sidebar.css';

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
        <div className="stat-item">
          <div className="stat-label">로딩중...</div>
        </div>
      </div>
    );
  }

  if (!marketData || marketData.length === 0) {
    return (
      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-label">데이터 없음</div>
          <div className="stat-value">-</div>
          <div className="stat-change">-</div>
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
            <div className="stat-value">
              {typeof item.current_price === 'number' ? item.current_price.toLocaleString() : '0'}
            </div>
            <div className={`stat-change ${(item.change_percent || 0) >= 0 ? 'status-positive' : 'status-negative'}`}>
              {(item.change_percent || 0) >= 0 ? '+' : ''}{(item.change_percent || 0).toFixed(2)}%
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
  interestRates 
}) => {
  const { currentView, setCurrentView } = useApp();

  const handleOverlayClick = () => {
    // 모바일에서 외부 영역 클릭 시 사이드바 닫기
    if (window.innerWidth <= 1024) {
      // 부모 컴포넌트에서 사이드바 상태를 관리하므로, 
      // 이벤트를 통해 닫기 요청을 전달
      const event = new CustomEvent('closeSidebar');
      window.dispatchEvent(event);
    }
  };
  
  const menuItems = [
    { id: 'dashboard', label: '대시보드', icon: BarChart3 },
    { id: 'stocks', label: '주식 분석', icon: TrendingUp },
    { id: 'quant', label: '퀀트투자', icon: Calculator },
    { id: 'portfolio', label: '포트폴리오', icon: Briefcase },
    { id: 'watchlist', label: '관심종목', icon: Star },
    { id: 'news', label: '뉴스', icon: Newspaper },
    { id: 'reports', label: '리포트', icon: FileText },
  ];

  const handleNavigation = (viewId: string) => {
    setCurrentView(viewId as any);
  };

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && <div className="sidebar-overlay" onClick={handleOverlayClick} />}
      
      <aside className={`sidebar ${isOpen ? 'sidebar-open' : ''}`}>
        {/* Navigation Menu */}
        <nav className="sidebar-nav">
          <ul className="nav-list">
            {menuItems.map((item) => {
              const IconComponent = item.icon;
              return (
                <li key={item.id}>
                  <button 
                    onClick={() => handleNavigation(item.id)}
                    className={`nav-item ${currentView === item.id ? 'nav-item-active' : ''}`}
                  >
                    <span className="nav-icon">
                      <IconComponent size={18} />
                    </span>
                    <span className="nav-label">{item.label}</span>
                  </button>
                </li>
              );
            })}
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
                <span className="market-desc">KOSPI</span>
              </div>
            </button>
            
            <button 
              className={`market-btn ${selectedMarket === 'US' ? 'market-btn-active' : ''}`}
              onClick={() => onMarketChange('US')}
            >
              <span className="market-flag">🇺🇸</span>
              <div className="market-info">
                <span className="market-name">미국</span>
                <span className="market-desc">NASDAQ</span>
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
                <span className="rate-country">한국 KR</span>
              </div>
              <div className="rate-value">
                {interestRates?.korea?.rate ? `${interestRates.korea.rate.toFixed(2)}%` : '로딩중...'}
              </div>
              <div className="rate-desc">기준금리</div>
            </div>
            
            <div className="rate-card">
              <div className="rate-header">
                <span className="rate-country">미국 US</span>
              </div>
              <div className="rate-value">
                {interestRates?.usa?.rate ? `${interestRates.usa.rate.toFixed(2)}%` : '로딩중...'}
              </div>
              <div className="rate-desc">연방기금금리</div>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="quick-stats">
          <h3 className="section-title">시장 현황</h3>
          <MarketStats selectedMarket={selectedMarket} />
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