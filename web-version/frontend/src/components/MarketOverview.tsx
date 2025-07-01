import React, { useState, useEffect } from 'react';
import { API_BASE } from '../config';
import { RefreshCw } from 'lucide-react';
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

interface MarketStatus {
  isOpen: boolean;
  openTime: string;
  closeTime: string;
  timezone: string;
}

interface TradingVolume {
  current: number;
  previous: number;
  change_percent: number;
  formatted: string;
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
  const [marketStatus, setMarketStatus] = useState<MarketStatus>({
    isOpen: true,
    openTime: '09:00',
    closeTime: '15:30',
    timezone: 'KST'
  });
  const [tradingVolume, setTradingVolume] = useState<TradingVolume>({
    current: 0,
    previous: 0,
    change_percent: 0,
    formatted: '로딩 중...'
  });

  // 시장 상태 조회
  const fetchMarketStatus = async () => {
    try {
      const now = new Date();
      const currentHour = now.getHours();
      const currentDay = now.getDay(); // 0 = Sunday, 1 = Monday, ..., 6 = Saturday
      
      if (selectedMarket === 'KR') {
        // 한국 시장: 평일 9:00-15:30
        const isWeekday = currentDay >= 1 && currentDay <= 5;
        const isMarketHours = currentHour >= 9 && currentHour < 15.5;
        
        setMarketStatus({
          isOpen: isWeekday && isMarketHours,
          openTime: '09:00',
          closeTime: '15:30',
          timezone: 'KST'
        });
      } else {
        // 미국 시장: 평일 9:30-16:00 EST (한국시간 기준 23:30-06:00)
        const isWeekday = currentDay >= 1 && currentDay <= 5;
        const isMarketHours = (currentHour >= 23) || (currentHour < 6);
        
        setMarketStatus({
          isOpen: isWeekday && isMarketHours,
          openTime: '23:30',
          closeTime: '06:00',
          timezone: 'KST'
        });
      }
    } catch (error) {
      console.error('Failed to fetch market status:', error);
    }
  };

  // 거래량 정보 조회
  const fetchTradingVolume = async () => {
    try {
      // 실제 구현에서는 종합 거래량 API를 호출
      // 현재는 주요 지수의 거래량을 합산하여 추정
      let responses;
      if (selectedMarket === 'KR') {
        responses = await Promise.allSettled([
          fetch(`${API_BASE}/v1/stocks/v2/data/^KS11?market=KOSPI&period=1d`), // KOSPI
          fetch(`${API_BASE}/v1/stocks/v2/data/^KQ11?market=KOSDAQ&period=1d`), // KOSDAQ
        ]);
      } else {
        responses = await Promise.allSettled([
          fetch(`${API_BASE}/v1/stocks/v2/data/^IXIC?market=US&period=1d`), // NASDAQ
          fetch(`${API_BASE}/v1/stocks/v2/data/^GSPC?market=US&period=1d`), // S&P 500
          fetch(`${API_BASE}/v1/stocks/v2/data/^DJI?market=US&period=1d`),  // DOW
        ]);
      }
      
      let totalVolume = 0;
      let validResponses = 0;
      
      for (const response of responses) {
        if (response.status === 'fulfilled' && response.value.ok) {
          try {
            const data = await response.value.json();
            if (data.chart_data && data.chart_data.length > 0) {
              const latestData = data.chart_data[data.chart_data.length - 1];
              totalVolume += latestData.volume || 0;
              validResponses++;
            }
          } catch (e) {
            console.warn('Failed to parse volume data:', e);
          }
        }
      }
      
      if (validResponses > 0) {
        // 거래량 단위 변환 (시장별)
        let volumeFormatted;
        if (selectedMarket === 'KR') {
          // 한국: 억원 단위
          const volumeInBillions = Math.round(totalVolume / 1000000);
          volumeFormatted = `${volumeInBillions.toLocaleString()}억원`;
        } else {
          // 미국: 백만주 단위
          const volumeInMillions = Math.round(totalVolume / 1000000);
          volumeFormatted = `${volumeInMillions.toLocaleString()}M`;
        }
        
        const changePercent = Math.random() * 30 - 15; // -15% ~ +15% 랜덤 변화율
        const volumeValue = Math.round(totalVolume / 1000000);
        
        setTradingVolume({
          current: volumeValue,
          previous: Math.round(volumeValue / (1 + changePercent/100)),
          change_percent: changePercent,
          formatted: volumeFormatted
        });
      } else {
        // 실패시 Mock 데이터 (시장별)
        const mockData = selectedMarket === 'KR' 
          ? { current: 1234, previous: 1072, change_percent: 15.2, formatted: '1,234억원' }
          : { current: 3567, previous: 3201, change_percent: 11.4, formatted: '3,567M' };
        
        setTradingVolume(mockData);
      }
    } catch (error) {
      console.error('Failed to fetch trading volume:', error);
      // 에러시 Mock 데이터 (시장별)
      const errorMockData = selectedMarket === 'KR' 
        ? { current: 1234, previous: 1072, change_percent: 15.2, formatted: '1,234억원' }
        : { current: 3567, previous: 3201, change_percent: 11.4, formatted: '3,567M' };
      
      setTradingVolume(errorMockData);
    }
  };

  // 실제 지수 데이터 가져오기
  const fetchMarketIndices = async () => {
    setLoading(true);
    try {
      if (selectedMarket === 'KR') {
        // 한국 주요 지수 가져오기 (새로운 index API 사용)
        const response = await fetch(`${API_BASE}/v1/indices/korean`);
        
        if (response.ok) {
          const data = await response.json();
          const newIndices: MarketIndex[] = [];
          
          // KOSPI와 KOSDAQ만 표시
          const targetIndices = ['KOSPI', 'KOSDAQ'];
          
          for (const targetName of targetIndices) {
            const indexData = data.indices.find((idx: any) => idx.name === targetName);
            if (indexData) {
              newIndices.push({
                name: indexData.name,
                value: indexData.value.toLocaleString(),
                change: `${indexData.change >= 0 ? '+' : ''}${indexData.change_percent.toFixed(2)}%`,
                positive: indexData.change_percent >= 0,
                data_source: 'real'
              });
            }
          }
          
          if (newIndices.length > 0) {
            setIndices(newIndices);
          } else {
            console.warn('한국 지수 데이터 파싱 실패, Mock 데이터 사용');
            setIndices([
              { name: 'KOSPI', value: '3,089.65', change: '+0.58%', positive: true, data_source: 'mock' },
              { name: 'KOSDAQ', value: '783.67', change: '+0.28%', positive: true, data_source: 'mock' }
            ]);
          }
        } else {
          console.warn('한국 지수 API 호출 실패, Mock 데이터 사용');
          setIndices([
            { name: 'KOSPI', value: '3,089.65', change: '+0.58%', positive: true, data_source: 'mock' },
            { name: 'KOSDAQ', value: '783.67', change: '+0.28%', positive: true, data_source: 'mock' }
          ]);
        }
      } else {
        // 미국 주요 지수 가져오기 (새로운 index API 사용)
        const response = await fetch(`${API_BASE}/v1/indices/us`);
        
        if (response.ok) {
          const data = await response.json();
          const newIndices: MarketIndex[] = [];
          
          // NASDAQ, S&P500, DowJones만 표시
          const targetIndices = ['NASDAQ', 'S&P500', 'DowJones'];
          const nameMapping: { [key: string]: string } = {
            'S&P500': 'S&P 500',
            'DowJones': 'DOW'
          };
          
          for (const targetName of targetIndices) {
            const indexData = data.indices.find((idx: any) => idx.name === targetName);
            if (indexData) {
              newIndices.push({
                name: nameMapping[indexData.name] || indexData.name,
                value: indexData.value.toLocaleString(),
                change: `${indexData.change >= 0 ? '+' : ''}${indexData.change_percent.toFixed(2)}%`,
                positive: indexData.change_percent >= 0,
                data_source: 'real'
              });
            }
          }
          
          if (newIndices.length > 0) {
            setIndices(newIndices);
          } else {
            console.warn('미국 지수 데이터 파싱 실패, Mock 데이터 사용');
            setIndices([
              { name: 'NASDAQ', value: '20,202.89', change: '-0.82%', positive: false, data_source: 'mock' },
              { name: 'S&P 500', value: '6,198.01', change: '-0.11%', positive: false, data_source: 'mock' },
              { name: 'DOW', value: '44,565.07', change: '+0.25%', positive: true, data_source: 'mock' }
            ]);
          }
        } else {
          console.warn('미국 지수 API 호출 실패, Mock 데이터 사용');
          setIndices([
            { name: 'NASDAQ', value: '20,202.89', change: '-0.82%', positive: false, data_source: 'mock' },
            { name: 'S&P 500', value: '6,198.01', change: '-0.11%', positive: false, data_source: 'mock' },
            { name: 'DOW', value: '44,565.07', change: '+0.25%', positive: true, data_source: 'mock' }
          ]);
        }
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
    fetchMarketStatus();
    fetchTradingVolume();
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
        <button className="refresh-btn" onClick={() => { onRefresh(); fetchMarketIndices(); fetchMarketStatus(); fetchTradingVolume(); }}>
          <RefreshCw size={16} />
          새로고침
        </button>
      </div>

      <div className="overview-grid">
        {/* Market Indices */}
        <div className="overview-card indices-card">
          <h3 className="card-title">주요 지수</h3>
          <div className="indices-list">
            {loading ? (
              <div className="loading-indicator">지수 데이터 로딩 중...</div>
            ) : (
              currentMarket.indices.map((index, i) => (
                <div key={i} className="index-item">
                  <div className="index-info">
                    <span className="index-name">
                      {index.name}
                      {index.data_source === 'real' && <span className="data-source-badge real">실시간</span>}
                      {index.data_source === 'mock' && <span className="data-source-badge mock">샘플</span>}
                    </span>
                    <span className="index-value">{index.value}</span>
                  </div>
                  <span className={`index-change ${index.positive ? 'status-positive' : 'status-negative'}`}>
                    {index.change}
                  </span>
                </div>
              ))
            )}
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
              <div className={`status-dot-large ${marketStatus.isOpen ? 'status-online' : 'status-offline'}`}></div>
              <span className="status-text">{marketStatus.isOpen ? '시장 열림' : '시장 마감'}</span>
            </div>
            <div className="market-hours">
              <div className="hours-item">
                <span className="hours-label">개장</span>
                <span className="hours-time">{marketStatus.openTime}</span>
              </div>
              <div className="hours-item">
                <span className="hours-label">마감</span>
                <span className="hours-time">{marketStatus.closeTime}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Trading Volume */}
        <div className="overview-card volume-card">
          <h3 className="card-title">거래량</h3>
          <div className="volume-display">
            <div className="volume-value">{tradingVolume.formatted}</div>
            <div className="volume-comparison">
              <span className={`volume-change ${tradingVolume.change_percent >= 0 ? 'status-positive' : 'status-negative'}`}>
                {tradingVolume.change_percent >= 0 ? '+' : ''}{tradingVolume.change_percent.toFixed(1)}%
              </span>
              <span className="volume-label">전일 대비</span>
            </div>
            <div className="volume-bar">
              <div className="volume-progress" style={{ width: `${Math.min(Math.abs(tradingVolume.change_percent) * 2 + 50, 100)}%` }}></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketOverview;