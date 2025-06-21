import React, { useState } from 'react';
import { useApp } from '../../context/AppContext';
import { ApiData } from '../Dashboard';
import './StockAnalysisView.css';

interface StockAnalysisViewProps {
  apiData: ApiData;
  selectedMarket: 'KR' | 'US';
  onRefresh: () => void;
}

const StockAnalysisView: React.FC<StockAnalysisViewProps> = ({ apiData, selectedMarket, onRefresh }) => {
  const { selectedStock, setSelectedStock } = useApp();
  const [analysisType, setAnalysisType] = useState<'short' | 'long'>('short');

  const handleStockSelect = (stock: any) => {
    setSelectedStock(stock);
  };

  return (
    <div className="stock-analysis-view">
      <div className="analysis-header">
        <div className="header-title">
          <h2>📈 주식 분석</h2>
          <p>AI를 활용한 실시간 주식 분석 및 예측</p>
        </div>
        <div className="analysis-controls">
          <button 
            className={`analysis-type-btn ${analysisType === 'short' ? 'active' : ''}`}
            onClick={() => setAnalysisType('short')}
          >
            단기 분석 (1일)
          </button>
          <button 
            className={`analysis-type-btn ${analysisType === 'long' ? 'active' : ''}`}
            onClick={() => setAnalysisType('long')}
          >
            장기 분석 (2주)
          </button>
        </div>
      </div>

      <div className="analysis-content">
        <div className="stock-selector-panel">
          <h3>종목 선택</h3>
          <div className="stock-grid">
            {apiData.stocks.map((stock) => (
              <div 
                key={stock.symbol} 
                className={`stock-item ${selectedStock?.symbol === stock.symbol ? 'selected' : ''}`}
                onClick={() => handleStockSelect(stock)}
              >
                <div className="stock-name">{stock.name}</div>
                <div className="stock-symbol">{stock.symbol}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="analysis-panel">
          {selectedStock ? (
            <div className="analysis-details">
              <div className="selected-stock-info">
                <h3>{selectedStock.name} ({selectedStock.symbol})</h3>
                <div className="market-badge">{selectedMarket === 'KR' ? '🇰🇷 한국' : '🇺🇸 미국'}</div>
              </div>

              <div className="analysis-sections">
                <div className="chart-section">
                  <h4>📊 차트 분석</h4>
                  <div className="chart-placeholder">
                    <div className="chart-mock">
                      <p>실시간 차트가 여기에 표시됩니다</p>
                      <div className="chart-features">
                        <span>✓ 기술적 지표</span>
                        <span>✓ 금리 오버레이</span>
                        <span>✓ 거래량 분석</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="ai-analysis-section">
                  <h4>🤖 AI 분석</h4>
                  <div className="ai-analysis-placeholder">
                    <div className="analysis-loading">
                      <div className="loading-spinner"></div>
                      <p>AI가 {analysisType === 'short' ? '단기' : '장기'} 분석을 수행중입니다...</p>
                    </div>
                    <div className="analysis-features">
                      <div className="feature">
                        <span className="feature-icon">📰</span>
                        <span>뉴스 감성 분석</span>
                      </div>
                      <div className="feature">
                        <span className="feature-icon">📈</span>
                        <span>기술적 지표 분석</span>
                      </div>
                      <div className="feature">
                        <span className="feature-icon">🎯</span>
                        <span>목표가 예측</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="no-stock-selected">
              <div className="empty-state">
                <span className="empty-icon">📈</span>
                <h3>종목을 선택하세요</h3>
                <p>분석할 종목을 왼쪽에서 선택해주세요</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StockAnalysisView;