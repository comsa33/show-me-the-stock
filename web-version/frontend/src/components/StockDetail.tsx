import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { API_BASE } from '../config';
import './StockDetail.css';

interface StockData {
  symbol: string;
  data: Array<{
    Date: string;
    Open: number;
    High: number;
    Low: number;
    Close: number;
    Volume: number;
  }>;
  current_price: number;
}

interface AnalysisData {
  symbol: string;
  market: string;
  analysis_type: string;
  timestamp: string;
  analysis: {
    summary: {
      overall_signal: string;
      confidence: string;
      recommendation: string;
      target_price: string;
      analysis_period: string;
    };
    technical_analysis: {
      rsi: {
        value: number;
        signal: string;
        description: string;
      };
      moving_average: {
        signal: string;
        description: string;
      };
      volume_analysis: {
        trend: string;
        description: string;
      };
    };
    news_analysis: {
      sentiment: string;
      score: number;
      summary: string;
      key_topics: string[];
    };
    risk_factors: string[];
    ai_insights: string[];
  };
}

const StockDetail: React.FC = () => {
  const { selectedStock, currentView, setCurrentView } = useApp();
  const [stockData, setStockData] = useState<StockData | null>(null);
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [period, setPeriod] = useState('1y');
  const [showInterestRate, setShowInterestRate] = useState(false);
  const [analysisType, setAnalysisType] = useState<'short' | 'long'>('short');

  const periods = [
    { value: '1d', label: '1일' },
    { value: '5d', label: '5일' },
    { value: '1mo', label: '1개월' },
    { value: '3mo', label: '3개월' },
    { value: '6mo', label: '6개월' },
    { value: '1y', label: '1년' },
    { value: '2y', label: '2년' },
    { value: '5y', label: '5년' }
  ];

  const fetchStockData = async () => {
    if (!selectedStock) return;
    
    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/v1/stocks/data/${selectedStock.symbol}?market=${selectedStock.market}&period=${period}`
      );
      const data = await response.json();
      setStockData(data);
    } catch (error) {
      console.error('주식 데이터 로딩 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalysis = async (type: 'short' | 'long') => {
    if (!selectedStock) return;
    
    setAnalysisLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/v1/ai/stock/analyze?symbol=${selectedStock.symbol}&market=${selectedStock.market}&analysis_type=${type}`,
        { method: 'POST' }
      );
      const data = await response.json();
      setAnalysisData(data);
    } catch (error) {
      console.error('AI 분석 실패:', error);
    } finally {
      setAnalysisLoading(false);
    }
  };

  useEffect(() => {
    if (selectedStock && currentView === 'stocks') {
      fetchStockData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedStock, period, currentView]);

  if (currentView !== 'stocks' || !selectedStock) {
    return null;
  }

  const formatPrice = (price: number) => {
    return selectedStock.market === 'KR' 
      ? `₩${price.toLocaleString()}` 
      : `$${price.toFixed(2)}`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('ko-KR');
  };

  return (
    <div className="stock-detail-container slide-up">
      <div className="stock-detail-header">
        <button 
          className="back-button"
          onClick={() => setCurrentView('dashboard')}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="m12 19-7-7 7-7"/>
            <path d="m19 12-7 7-7-7"/>
          </svg>
          돌아가기
        </button>
        
        <div className="stock-header-info">
          <h2>{selectedStock.name}</h2>
          <span className="stock-symbol-large">{selectedStock.symbol}</span>
          <span className="market-badge">{selectedStock.market === 'KR' ? '🇰🇷 한국' : '🇺🇸 미국'}</span>
        </div>

        {stockData && (
          <div className="current-price-info">
            <div className="current-price">{formatPrice(stockData.current_price)}</div>
            <div className="price-change">
              {stockData.data.length > 1 && (
                <span className={
                  stockData.current_price > stockData.data[stockData.data.length - 2].Close
                    ? 'status-positive' 
                    : stockData.current_price < stockData.data[stockData.data.length - 2].Close
                    ? 'status-negative'
                    : 'status-neutral'
                }>
                  {stockData.current_price > stockData.data[stockData.data.length - 2].Close ? '▲' : 
                   stockData.current_price < stockData.data[stockData.data.length - 2].Close ? '▼' : '—'}
                  {((stockData.current_price - stockData.data[stockData.data.length - 2].Close) / stockData.data[stockData.data.length - 2].Close * 100).toFixed(2)}%
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="stock-detail-content">
        <div className="chart-section">
          <div className="chart-controls">
            <div className="period-selector">
              {periods.map(p => (
                <button 
                  key={p.value}
                  className={`period-btn ${period === p.value ? 'active' : ''}`}
                  onClick={() => setPeriod(p.value)}
                >
                  {p.label}
                </button>
              ))}
            </div>
            
            <div className="chart-options">
              <label className="checkbox-label">
                <input 
                  type="checkbox" 
                  checked={showInterestRate}
                  onChange={(e) => setShowInterestRate(e.target.checked)}
                />
                금리 오버레이
              </label>
            </div>
          </div>

          <div className="chart-container">
            {loading ? (
              <div className="chart-loading">
                <div className="loading-spinner"></div>
                <p>차트 데이터 로딩 중...</p>
              </div>
            ) : stockData ? (
              <div className="simple-chart">
                <div className="chart-header">
                  <h4>{selectedStock.name} 주가 차트</h4>
                  <span>최근 {stockData.data.length}일간 데이터</span>
                </div>
                
                <div className="price-chart">
                  {stockData.data.slice(-30).map((point, index) => {
                    const maxPrice = Math.max(...stockData.data.slice(-30).map(d => d.High));
                    const minPrice = Math.min(...stockData.data.slice(-30).map(d => d.Low));
                    const height = ((point.Close - minPrice) / (maxPrice - minPrice)) * 200;
                    
                    return (
                      <div 
                        key={index}
                        className="price-bar"
                        style={{ height: `${height}px` }}
                        title={`${formatDate(point.Date)}: ${formatPrice(point.Close)}`}
                      />
                    );
                  })}
                </div>
                
                <div className="chart-summary">
                  <div className="summary-item">
                    <span>최고가</span>
                    <span>{formatPrice(Math.max(...stockData.data.map(d => d.High)))}</span>
                  </div>
                  <div className="summary-item">
                    <span>최저가</span>
                    <span>{formatPrice(Math.min(...stockData.data.map(d => d.Low)))}</span>
                  </div>
                  <div className="summary-item">
                    <span>평균 거래량</span>
                    <span>{(stockData.data.reduce((sum, d) => sum + d.Volume, 0) / stockData.data.length).toLocaleString()}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="chart-error">
                <p>차트 데이터를 불러올 수 없습니다.</p>
                <button onClick={fetchStockData} className="btn-primary">다시 시도</button>
              </div>
            )}
          </div>
        </div>

        <div className="analysis-section">
          <div className="analysis-header">
            <h3>AI 분석</h3>
            <div className="analysis-controls">
              <div className="analysis-type-selector">
                <button 
                  className={`analysis-btn ${analysisType === 'short' ? 'active' : ''}`}
                  onClick={() => setAnalysisType('short')}
                >
                  단기 분석 (1일)
                </button>
                <button 
                  className={`analysis-btn ${analysisType === 'long' ? 'active' : ''}`}
                  onClick={() => setAnalysisType('long')}
                >
                  장기 분석 (2주)
                </button>
              </div>
              <button 
                className="btn-primary"
                onClick={() => fetchAnalysis(analysisType)}
                disabled={analysisLoading}
              >
                {analysisLoading ? '분석 중...' : 'AI 분석 실행'}
              </button>
            </div>
          </div>

          {analysisLoading && (
            <div className="analysis-loading">
              <div className="loading-spinner"></div>
              <p>AI가 주식을 분석하고 있습니다...</p>
            </div>
          )}

          {analysisData && (
            <div className="analysis-results">
              <div className="analysis-summary">
                <h4>분석 요약</h4>
                <div className="summary-grid">
                  <div className="summary-card">
                    <div className="summary-label">전체 신호</div>
                    <div className={`summary-value signal-${analysisData.analysis.summary.overall_signal.toLowerCase()}`}>
                      {analysisData.analysis.summary.overall_signal}
                    </div>
                  </div>
                  <div className="summary-card">
                    <div className="summary-label">신뢰도</div>
                    <div className="summary-value">{analysisData.analysis.summary.confidence}</div>
                  </div>
                  <div className="summary-card">
                    <div className="summary-label">추천</div>
                    <div className="summary-value">{analysisData.analysis.summary.recommendation}</div>
                  </div>
                  <div className="summary-card">
                    <div className="summary-label">목표가</div>
                    <div className="summary-value">{analysisData.analysis.summary.target_price}</div>
                  </div>
                </div>
              </div>

              <div className="analysis-details">
                <div className="analysis-section-item">
                  <h5>기술적 분석</h5>
                  <div className="technical-indicators">
                    <div className="indicator">
                      <span>RSI</span>
                      <span className={`indicator-value rsi-${analysisData.analysis.technical_analysis.rsi.signal.toLowerCase()}`}>
                        {analysisData.analysis.technical_analysis.rsi.value} ({analysisData.analysis.technical_analysis.rsi.signal})
                      </span>
                    </div>
                    <div className="indicator">
                      <span>이동평균</span>
                      <span className="indicator-value">{analysisData.analysis.technical_analysis.moving_average.signal}</span>
                    </div>
                    <div className="indicator">
                      <span>거래량</span>
                      <span className="indicator-value">{analysisData.analysis.technical_analysis.volume_analysis.trend}</span>
                    </div>
                  </div>
                </div>

                <div className="analysis-section-item">
                  <h5>뉴스 감성 분석</h5>
                  <div className="sentiment-analysis">
                    <div className="sentiment-score">
                      <span className={`sentiment-value sentiment-${analysisData.analysis.news_analysis.sentiment.toLowerCase()}`}>
                        {analysisData.analysis.news_analysis.sentiment} ({analysisData.analysis.news_analysis.score}점)
                      </span>
                    </div>
                    <p>{analysisData.analysis.news_analysis.summary}</p>
                    <div className="key-topics">
                      {analysisData.analysis.news_analysis.key_topics.map((topic, index) => (
                        <span key={index} className="topic-tag">{topic}</span>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="analysis-section-item">
                  <h5>AI 인사이트</h5>
                  <ul className="insights-list">
                    {analysisData.analysis.ai_insights.map((insight, index) => (
                      <li key={index}>{insight}</li>
                    ))}
                  </ul>
                </div>

                <div className="analysis-section-item">
                  <h5>리스크 요인</h5>
                  <ul className="risk-list">
                    {analysisData.analysis.risk_factors.map((risk, index) => (
                      <li key={index}>{risk}</li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StockDetail;