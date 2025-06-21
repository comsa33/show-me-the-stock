import React from 'react';
import './MarketOverview.css';

interface InterestRate {
  rate: number;
  description: string;
}

interface MarketOverviewProps {
  selectedMarket: 'KR' | 'US';
  interestRates: {
    korea: InterestRate;
    usa: InterestRate;
  };
  onRefresh: () => void;
}

const MarketOverview: React.FC<MarketOverviewProps> = ({ 
  selectedMarket, 
  interestRates, 
  onRefresh 
}) => {
  const marketData = {
    KR: {
      name: '한국 시장',
      flag: '🇰🇷',
      indices: [
        { name: 'KOSPI', value: '2,580.45', change: '+1.2%', positive: true },
        { name: 'KOSDAQ', value: '785.32', change: '+0.8%', positive: true },
        { name: 'KRX 100', value: '5,432.10', change: '-0.3%', positive: false }
      ]
    },
    US: {
      name: '미국 시장',
      flag: '🇺🇸',
      indices: [
        { name: 'NASDAQ', value: '15,240.83', change: '+0.8%', positive: true },
        { name: 'S&P 500', value: '4,567.12', change: '+0.5%', positive: true },
        { name: 'DOW', value: '35,123.45', change: '-0.1%', positive: false }
      ]
    }
  };

  const currentMarket = marketData[selectedMarket];
  const currentRate = selectedMarket === 'KR' ? interestRates.korea : interestRates.usa;

  return (
    <div className="market-overview fade-in">
      <div className="overview-header">
        <div className="market-title">
          <span className="market-flag">{currentMarket.flag}</span>
          <h2>{currentMarket.name} 개요</h2>
        </div>
        <button className="refresh-btn" onClick={onRefresh}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="23 4 23 10 17 10"></polyline>
            <polyline points="1 20 1 14 7 14"></polyline>
            <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
          </svg>
          새로고침
        </button>
      </div>

      <div className="overview-grid">
        {/* Market Indices */}
        <div className="overview-card indices-card">
          <h3 className="card-title">주요 지수</h3>
          <div className="indices-list">
            {currentMarket.indices.map((index, i) => (
              <div key={i} className="index-item">
                <div className="index-info">
                  <span className="index-name">{index.name}</span>
                  <span className="index-value">{index.value}</span>
                </div>
                <span className={`index-change ${index.positive ? 'status-positive' : 'status-negative'}`}>
                  {index.change}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Interest Rate */}
        <div className="overview-card rate-card">
          <h3 className="card-title">기준금리</h3>
          <div className="rate-display">
            <div className="rate-value-large">{currentRate.rate.toFixed(2)}%</div>
            <div className="rate-description">{currentRate.description}</div>
            <div className="rate-status">
              <span className="rate-trend status-neutral">안정</span>
              <span className="rate-update">실시간 업데이트</span>
            </div>
          </div>
        </div>

        {/* Market Status */}
        <div className="overview-card status-card">
          <h3 className="card-title">시장 상태</h3>
          <div className="market-status">
            <div className="status-indicator-large">
              <div className="status-dot-large status-online"></div>
              <span className="status-text">시장 열림</span>
            </div>
            <div className="market-hours">
              <div className="hours-item">
                <span className="hours-label">개장</span>
                <span className="hours-time">09:00</span>
              </div>
              <div className="hours-item">
                <span className="hours-label">마감</span>
                <span className="hours-time">15:30</span>
              </div>
            </div>
          </div>
        </div>

        {/* Trading Volume */}
        <div className="overview-card volume-card">
          <h3 className="card-title">거래량</h3>
          <div className="volume-display">
            <div className="volume-value">1,234억원</div>
            <div className="volume-comparison">
              <span className="volume-change status-positive">+15.2%</span>
              <span className="volume-label">전일 대비</span>
            </div>
            <div className="volume-bar">
              <div className="volume-progress" style={{ width: '68%' }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketOverview;