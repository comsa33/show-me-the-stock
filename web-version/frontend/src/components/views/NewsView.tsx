import React from 'react';
import './NewsView.css';

interface NewsViewProps {
  selectedMarket: 'KR' | 'US';
}

const NewsView: React.FC<NewsViewProps> = ({ selectedMarket }) => {
  return (
    <div className="news-view">
      <div className="news-header">
        <div className="header-title">
          <h2>📰 뉴스</h2>
          <p>최신 경제 뉴스와 시장 동향을 확인하세요</p>
        </div>
      </div>
      
      <div className="news-content">
        <div className="coming-soon">
          <div className="coming-soon-icon">📰</div>
          <h3>뉴스 기능 준비중</h3>
          <p>실시간 경제 뉴스와 종목별 뉴스 분석 기능을 준비중입니다!</p>
        </div>
      </div>
    </div>
  );
};

export default NewsView;