import React from 'react';
import './PortfolioView.css';

interface PortfolioViewProps {
  selectedMarket: 'KR' | 'US';
}

const PortfolioView: React.FC<PortfolioViewProps> = ({ selectedMarket }) => {
  return (
    <div className="portfolio-view">
      <div className="portfolio-header">
        <div className="header-title">
          <h2>💼 포트폴리오</h2>
          <p>내 투자 현황과 수익률을 한눈에 확인하세요</p>
        </div>
      </div>
      
      <div className="portfolio-content">
        <div className="coming-soon">
          <div className="coming-soon-icon">🚀</div>
          <h3>포트폴리오 기능 준비중</h3>
          <p>곧 멋진 포트폴리오 관리 기능을 만나보실 수 있습니다!</p>
        </div>
      </div>
    </div>
  );
};

export default PortfolioView;