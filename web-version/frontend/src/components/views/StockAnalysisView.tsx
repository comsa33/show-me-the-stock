import React, { useState, useEffect } from 'react';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import { watchlistService } from '../../services/watchlistService';
import { ApiData } from '../Dashboard';
import { TrendingUp, BarChart3, Bot, Newspaper, Target, ArrowLeft, Star } from 'lucide-react';
import './StockAnalysisView.css';

interface StockAnalysisViewProps {
  apiData: ApiData;
  selectedMarket: 'KR' | 'US';
  onRefresh: () => void;
}

const StockAnalysisView: React.FC<StockAnalysisViewProps> = ({ apiData, selectedMarket, onRefresh }) => {
  const { selectedStock, setSelectedStock, setCurrentView } = useApp();
  const { user } = useAuth();
  const [analysisType, setAnalysisType] = useState<'short' | 'long'>('short');
  const [isInWatchlist, setIsInWatchlist] = useState(false);
  const [isTogglingWatchlist, setIsTogglingWatchlist] = useState(false);

  const handleStockSelect = (stock: any) => {
    setSelectedStock(stock);
  };

  // Check if selected stock is in watchlist
  useEffect(() => {
    const checkWatchlist = async () => {
      if (selectedStock && user) {
        try {
          const inWatchlist = await watchlistService.isInWatchlist(selectedStock.symbol, selectedMarket);
          setIsInWatchlist(inWatchlist);
        } catch (error) {
          console.error('Failed to check watchlist status:', error);
        }
      }
    };
    
    checkWatchlist();
  }, [selectedStock, user, selectedMarket]);

  const toggleWatchlist = async () => {
    if (!user) {
      setCurrentView('login');
      return;
    }

    if (!selectedStock || isTogglingWatchlist) return;

    setIsTogglingWatchlist(true);
    try {
      if (isInWatchlist) {
        await watchlistService.remove(selectedStock.symbol, selectedMarket);
        setIsInWatchlist(false);
      } else {
        await watchlistService.add(selectedStock.symbol, selectedMarket);
        setIsInWatchlist(true);
      }
    } catch (error) {
      console.error('Failed to toggle watchlist:', error);
    } finally {
      setIsTogglingWatchlist(false);
    }
  };

  return (
    <div className="stock-analysis-view">
      <div className="analysis-header">
        <div className="header-title">
          <h2 className="flex items-center gap-2">
            <TrendingUp size={24} />
            주식 분석
          </h2>
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
                <div className="stock-title-row">
                  <h3>{selectedStock.name} ({selectedStock.symbol})</h3>
                  <button
                    className={`watchlist-btn ${isInWatchlist ? 'active' : ''}`}
                    onClick={toggleWatchlist}
                    disabled={isTogglingWatchlist}
                    title={isInWatchlist ? '관심종목에서 제거' : '관심종목에 추가'}
                  >
                    {isTogglingWatchlist ? (
                      <div className="loading-spinner-small"></div>
                    ) : (
                      <Star
                        size={20}
                        fill={isInWatchlist ? 'currentColor' : 'none'}
                        stroke="currentColor"
                      />
                    )}
                  </button>
                </div>
                <div className="market-badge">{selectedMarket === 'KR' ? '한국 KR' : '미국 US'}</div>
              </div>

              <div className="analysis-sections">
                <div className="chart-section">
                  <h4 className="flex items-center gap-2">
                    <BarChart3 size={18} />
                    차트 분석
                  </h4>
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
                  <h4 className="flex items-center gap-2">
                    <Bot size={18} />
                    AI 분석
                  </h4>
                  <div className="ai-analysis-placeholder">
                    <div className="analysis-loading">
                      <div className="loading-spinner"></div>
                      <p>AI가 {analysisType === 'short' ? '단기' : '장기'} 분석을 수행중입니다...</p>
                    </div>
                    <div className="analysis-features">
                      <div className="feature">
                        <span className="feature-icon">
                          <Newspaper size={16} />
                        </span>
                        <span>뉴스 감성 분석</span>
                      </div>
                      <div className="feature">
                        <span className="feature-icon">
                          <TrendingUp size={16} />
                        </span>
                        <span>기술적 지표 분석</span>
                      </div>
                      <div className="feature">
                        <span className="feature-icon">
                          <Target size={16} />
                        </span>
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
                <TrendingUp size={64} className="empty-icon" />
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