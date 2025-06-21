import React from 'react';
import './WatchlistView.css';

interface WatchlistViewProps {
  selectedMarket: 'KR' | 'US';
}

const WatchlistView: React.FC<WatchlistViewProps> = ({ selectedMarket }) => {
  return (
    <div className="watchlist-view">
      <div className="watchlist-header">
        <div className="header-title">
          <h2>⭐ 관심종목</h2>
          <p>즐겨찾기한 종목들을 관리하고 모니터링하세요</p>
        </div>
      </div>
      
      <div className="watchlist-content">
        <div className="coming-soon">
          <div className="coming-soon-icon">⭐</div>
          <h3>관심종목 기능 준비중</h3>
          <p>관심있는 종목을 저장하고 추적할 수 있는 기능을 개발중입니다!</p>
        </div>
      </div>
    </div>
  );
};

export default WatchlistView;