import React from 'react';
import './ReportsView.css';

interface ReportsViewProps {
  selectedMarket: 'KR' | 'US';
}

const ReportsView: React.FC<ReportsViewProps> = ({ selectedMarket }) => {
  return (
    <div className="reports-view">
      <div className="reports-header">
        <div className="header-title">
          <h2>📋 리포트</h2>
          <p>AI 생성 분석 리포트와 투자 리포트를 확인하세요</p>
        </div>
      </div>
      
      <div className="reports-content">
        <div className="coming-soon">
          <div className="coming-soon-icon">📋</div>
          <h3>리포트 기능 준비중</h3>
          <p>AI가 생성한 투자 분석 리포트와 시장 분석 자료를 제공할 예정입니다!</p>
        </div>
      </div>
    </div>
  );
};

export default ReportsView;