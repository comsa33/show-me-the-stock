import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';
import './MarketOverview.css';

interface InterestRate {
  rate: number;
  description: string;
}

interface MarketIndex {
  name: string;
  value: string;
  change: string;
  positive: boolean;
  data_source?: string;
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
  const [indices, setIndices] = useState<MarketIndex[]>([]);
  const [loading, setLoading] = useState(false);

  // 실제 지수 데이터 가져오기
  const fetchMarketIndices = async () => {
    setLoading(true);
    try {
      if (selectedMarket === 'KR') {
        // 한국 주요 지수 가져오기 (yfinance 사용)
        const responses = await Promise.all([
          fetch(`${API_BASE}/v1/stocks/v2/data/^KS11?market=US&period=1d`), // KOSPI
          fetch(`${API_BASE}/v1/stocks/v2/data/^KQ11?market=US&period=1d`), // KOSDAQ
        ]);
        
        const kospiData = responses[0].ok ? await responses[0].json() : null;
        const kosdaqData = responses[1].ok ? await responses[1].json() : null;
        
        const newIndices: MarketIndex[] = [];
        
        if (kospiData && kospiData.chart_data.length > 0) {
          const latest = kospiData.chart_data[kospiData.chart_data.length - 1];
          const change = kospiData.change_percent;
          newIndices.push({
            name: 'KOSPI',
            value: latest.close.toLocaleString(),
            change: `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`,
            positive: change >= 0,
            data_source: 'real'
          });
        } else {
          newIndices.push({ name: 'KOSPI', value: '2,580.45', change: '+1.2%', positive: true, data_source: 'mock' });
        }
        
        if (kosdaqData && kosdaqData.chart_data.length > 0) {
          const latest = kosdaqData.chart_data[kosdaqData.chart_data.length - 1];
          const change = kosdaqData.change_percent;
          newIndices.push({
            name: 'KOSDAQ',
            value: latest.close.toLocaleString(),
            change: `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`,
            positive: change >= 0,
            data_source: 'real'
          });
        } else {
          newIndices.push({ name: 'KOSDAQ', value: '785.32', change: '+0.8%', positive: true, data_source: 'mock' });
        }
        
        setIndices(newIndices);
      } else {
        // 미국 주요 지수 가져오기
        const responses = await Promise.all([
          fetch(`${API_BASE}/v1/stocks/v2/data/^IXIC?market=US&period=1d`), // NASDAQ
          fetch(`${API_BASE}/v1/stocks/v2/data/^GSPC?market=US&period=1d`), // S&P 500
          fetch(`${API_BASE}/v1/stocks/v2/data/^DJI?market=US&period=1d`),  // DOW
        ]);
        
        const nasdaqData = responses[0].ok ? await responses[0].json() : null;
        const spData = responses[1].ok ? await responses[1].json() : null;
        const dowData = responses[2].ok ? await responses[2].json() : null;
        
        const newIndices: MarketIndex[] = [];
        
        if (nasdaqData && nasdaqData.chart_data.length > 0) {
          const latest = nasdaqData.chart_data[nasdaqData.chart_data.length - 1];
          const change = nasdaqData.change_percent;
          newIndices.push({
            name: 'NASDAQ',
            value: latest.close.toLocaleString(),
            change: `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`,
            positive: change >= 0,
            data_source: 'real'
          });
        } else {
          newIndices.push({ name: 'NASDAQ', value: '15,240.83', change: '+0.8%', positive: true, data_source: 'mock' });
        }
        
        if (spData && spData.chart_data.length > 0) {
          const latest = spData.chart_data[spData.chart_data.length - 1];
          const change = spData.change_percent;
          newIndices.push({
            name: 'S&P 500',
            value: latest.close.toLocaleString(),
            change: `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`,
            positive: change >= 0,
            data_source: 'real'
          });
        } else {
          newIndices.push({ name: 'S&P 500', value: '4,567.12', change: '+0.5%', positive: true, data_source: 'mock' });
        }
        
        if (dowData && dowData.chart_data.length > 0) {
          const latest = dowData.chart_data[dowData.chart_data.length - 1];
          const change = dowData.change_percent;
          newIndices.push({
            name: 'DOW',
            value: latest.close.toLocaleString(),
            change: `${change >= 0 ? '+' : ''}${change.toFixed(2)}%`,
            positive: change >= 0,
            data_source: 'real'
          });
        } else {
          newIndices.push({ name: 'DOW', value: '35,123.45', change: '-0.1%', positive: false, data_source: 'mock' });
        }
        
        setIndices(newIndices);
      }
    } catch (error) {
      console.error('Failed to fetch market indices:', error);
      // 에러 시 기본값 사용
      if (selectedMarket === 'KR') {
        setIndices([
          { name: 'KOSPI', value: '2,580.45', change: '+1.2%', positive: true, data_source: 'error_fallback' },
          { name: 'KOSDAQ', value: '785.32', change: '+0.8%', positive: true, data_source: 'error_fallback' }
        ]);
      } else {
        setIndices([
          { name: 'NASDAQ', value: '15,240.83', change: '+0.8%', positive: true, data_source: 'error_fallback' },
          { name: 'S&P 500', value: '4,567.12', change: '+0.5%', positive: true, data_source: 'error_fallback' },
          { name: 'DOW', value: '35,123.45', change: '-0.1%', positive: false, data_source: 'error_fallback' }
        ]);
      }
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchMarketIndices();
  }, [selectedMarket]);
  
  const marketData = {
    KR: {
      name: '한국 시장',
      flag: '🇰🇷',
      indices: indices
    },
    US: {
      name: '미국 시장',
      flag: '🇺🇸', 
      indices: indices
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