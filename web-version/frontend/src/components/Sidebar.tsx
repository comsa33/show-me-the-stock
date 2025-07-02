import React, { useState, useEffect } from 'react';
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

interface IndexData {
  symbol: string;
  name: string;
  current_price: number;
  change: number;
  change_percent: number;
}

const MarketStats: React.FC<MarketStatsProps> = ({ selectedMarket }) => {
  const [marketData, setMarketData] = useState<IndexData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchMarketData = async () => {
      setLoading(true);
      try {
        const endpoint = selectedMarket === 'KR' ? 'korean' : 'us';
        const response = await fetch(`/api/v1/indices/${endpoint}`);
        if (response.ok) {
          const data = await response.json();
          const indices = data.indices || data || [];
          // 데이터 유효성 검사
          if (Array.isArray(indices) && indices.length > 0) {
            setMarketData(indices);
          } else {
            setMarketData(getMockMarketData(selectedMarket));
          }
        } else {
          // 실패시 목 데이터 사용
          setMarketData(getMockMarketData(selectedMarket));
        }
      } catch (error) {
        console.error('Failed to fetch market data:', error);
        setMarketData(getMockMarketData(selectedMarket));
      } finally {
        setLoading(false);
      }
    };

    fetchMarketData();
  }, [selectedMarket]);

  const getMockMarketData = (market: 'KR' | 'US'): IndexData[] => {
    if (market === 'KR') {
      return [
        { symbol: 'KOSPI', name: 'KOSPI', current_price: 2580.45, change: 30.25, change_percent: 1.19 },
        { symbol: 'KOSDAQ', name: 'KOSDAQ', current_price: 748.32, change: -5.68, change_percent: -0.75 },
        { symbol: 'USD/KRW', name: '환율 (USD)', current_price: 1325.50, change: -4.20, change_percent: -0.32 }
      ];
    } else {
      return [
        { symbol: 'NASDAQ', name: 'NASDAQ', current_price: 15240.83, change: 120.45, change_percent: 0.80 },
        { symbol: 'DOW', name: 'DOW', current_price: 34567.12, change: -85.23, change_percent: -0.25 },
        { symbol: 'S&P500', name: 'S&P 500', current_price: 4456.78, change: 22.34, change_percent: 0.50 }
      ];
    }
  };

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