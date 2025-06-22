import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { API_BASE } from '../config';
import ProfessionalStockChart from './ProfessionalStockChart';
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

interface DetailedStockInfo {
  symbol: string;
  market: string;
  basic_info: {
    current_price: number;
    previous_close: number;
    change: number;
    change_percent: number;
  };
  price_ranges: {
    daily_low: number;
    daily_high: number;
    daily_range: string;
    year_low: number;
    year_high: number;
    week_52_range: string;
  };
  trading_info: {
    current_volume: number;
    avg_volume_20d: number;
    volume_ratio: number;
  };
  financial_metrics: {
    market_cap: number | null;
    market_cap_formatted: string;
    per: number | null;
    pbr: number | null;
    dividend_yield: number | null;
  };
  last_updated: string;
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
  const [detailedInfo, setDetailedInfo] = useState<DetailedStockInfo | null>(null);
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [period, setPeriod] = useState('1y');
  const [showInterestRate, setShowInterestRate] = useState(false);
  const [interestRateData, setInterestRateData] = useState<Array<{ date: string; rate: number }>>([]);
  const [analysisType, setAnalysisType] = useState<'short' | 'long'>('short');

  const periods = [
    { value: '1d', label: '1일' },
    { value: '5d', label: '5일' },
    { value: '1mo', label: '1개월' },
    { value: '6mo', label: '6개월' },
    { value: 'ytd', label: 'YTD' },
    { value: '1y', label: '1년' },
    { value: '5y', label: '5년' },
    { value: 'max', label: '최대' }
  ];

  const fetchStockData = async () => {
    if (!selectedStock) return;
    
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `${API_BASE}/v1/stocks/v2/data/${selectedStock.symbol}?market=${selectedStock.market}&period=${period}`
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '데이터를 불러올 수 없습니다.');
      }
      
      const data = await response.json();
      
      // v2 API 응답 형식을 기존 형식에 맞게 변환
      const transformedData = {
        symbol: data.symbol,
        current_price: data.current_price,
        data: data.chart_data.map((item: any) => ({
          Date: item.date,
          Open: item.open,
          High: item.high,
          Low: item.low,
          Close: item.close,
          Volume: item.volume
        }))
      };
      
      setStockData(transformedData);
      // 주식 데이터를 받은 후 금리 데이터 생성
      generateInterestRateData(transformedData);
    } catch (error) {
      console.error('주식 데이터 로딩 실패:', error);
      setError(error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.');
      setStockData(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchDetailedInfo = async () => {
    if (!selectedStock) return;
    
    setDetailLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/v1/stocks/v2/detail/${selectedStock.symbol}?market=${selectedStock.market}`
      );
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '상세 정보를 불러올 수 없습니다.');
      }
      
      const data = await response.json();
      setDetailedInfo(data);
    } catch (error) {
      console.error('상세 정보 로딩 실패:', error);
      setDetailedInfo(null);
    } finally {
      setDetailLoading(false);
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
      fetchDetailedInfo();
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

  // 모의 금리 데이터 생성 함수
  const generateInterestRateData = (stockData: StockData) => {
    const baseRate = selectedStock.market === 'KR' ? 3.5 : 5.25; // 한국: 3.5%, 미국: 5.25%
    const rateData = stockData.data.map((point, index) => {
      // 시간에 따른 금리 변동 시뮬레이션 (실제로는 API에서 가져와야 함)
      const variation = Math.sin(index / 30) * 0.5 + Math.random() * 0.2 - 0.1;
      const rate = Math.max(0.1, baseRate + variation);
      
      return {
        date: point.Date,
        rate: parseFloat(rate.toFixed(2))
      };
    });
    
    setInterestRateData(rateData);
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
              <label className="toggle-switch-label">
                <input 
                  type="checkbox" 
                  className="toggle-input"
                  checked={showInterestRate}
                  onChange={(e) => setShowInterestRate(e.target.checked)}
                />
                <span className="toggle-slider"></span>
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
            ) : error ? (
              <div className="chart-error">
                <div className="error-icon">⚠️</div>
                <h3>데이터를 불러올 수 없습니다</h3>
                <p>{error}</p>
                <button onClick={fetchStockData} className="btn-primary">다시 시도</button>
              </div>
            ) : stockData ? (
              <>
                <ProfessionalStockChart 
                  data={stockData.data}
                  symbol={selectedStock.symbol}
                  market={selectedStock.market}
                  period={period}
                  showInterestRate={showInterestRate}
                  interestRateData={interestRateData}
                  onToggleInterestRate={setShowInterestRate}
                />

                {/* 네이버 스타일 상세 정보 */}
                {detailLoading ? (
                  <div className="detail-info-loading">
                    <div className="loading-spinner"></div>
                    <p>상세 정보 로딩 중...</p>
                  </div>
                ) : detailedInfo ? (
                  <div className="stock-detail-info">
                    <div className="detail-info-grid">
                      <div className="info-card">
                        <span className="info-label">전일 종가</span>
                        <span className="info-value">
                          {selectedStock.market === 'KR' 
                            ? `₩${detailedInfo.basic_info.previous_close.toLocaleString()}`
                            : `$${detailedInfo.basic_info.previous_close.toFixed(2)}`
                          }
                        </span>
                      </div>
                      
                      <div className="info-card">
                        <span className="info-label">일일 변동폭</span>
                        <span className="info-value">{detailedInfo.price_ranges.daily_range}</span>
                      </div>
                      
                      <div className="info-card">
                        <span className="info-label">52주 변동폭</span>
                        <span className="info-value">{detailedInfo.price_ranges.week_52_range}</span>
                      </div>
                      
                      {detailedInfo.financial_metrics.market_cap && (
                        <div className="info-card">
                          <span className="info-label">시가총액</span>
                          <span className="info-value">{detailedInfo.financial_metrics.market_cap_formatted}</span>
                        </div>
                      )}
                      
                      <div className="info-card">
                        <span className="info-label">평균 거래량</span>
                        <span className="info-value">
                          {(detailedInfo.trading_info.avg_volume_20d / 10000).toFixed(1)}만
                        </span>
                      </div>
                      
                      {detailedInfo.financial_metrics.per && (
                        <div className="info-card">
                          <span className="info-label">주가수익률 (PER)</span>
                          <span className="info-value">{detailedInfo.financial_metrics.per.toFixed(2)}</span>
                        </div>
                      )}
                      
                      {detailedInfo.financial_metrics.pbr && (
                        <div className="info-card">
                          <span className="info-label">주가순자산비율 (PBR)</span>
                          <span className="info-value">{detailedInfo.financial_metrics.pbr.toFixed(2)}</span>
                        </div>
                      )}
                      
                      {detailedInfo.financial_metrics.dividend_yield && (
                        <div className="info-card">
                          <span className="info-label">배당수익률</span>
                          <span className="info-value">{detailedInfo.financial_metrics.dividend_yield.toFixed(2)}%</span>
                        </div>
                      )}
                    </div>
                  </div>
                ) : null}
              </>
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