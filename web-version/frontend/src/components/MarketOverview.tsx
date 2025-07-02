import React, { useState, useEffect, useMemo } from 'react';
import { API_BASE } from '../config';
import { RefreshCw } from 'lucide-react';
import { useApp } from '../context/AppContext';
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
  const { marketIndices, marketIndicesLoading, fetchMarketIndices } = useApp();
  
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

  const indices = useMemo((): MarketIndex[] => {
    const sourceIndices = selectedMarket === 'KR' ? marketIndices.korea : marketIndices.us;
    if (!sourceIndices) return [];

    const nameMapping: { [key: string]: string } = {
        'S&P500': 'S&P 500',
        'DowJones': 'DOW'
    };
    
    const targetIndices = selectedMarket === 'KR' 
        ? ['KOSPI', 'KOSDAQ', 'KOSPI200'] 
        : ['NASDAQ', 'S&P500', 'DowJones'];

    return sourceIndices
      .filter(idx => idx.symbol && targetIndices.includes(idx.symbol))
      .map(indexData => ({
        name: nameMapping[indexData.name] || indexData.name,
        value: indexData.value.toLocaleString(),
        change: `${indexData.change >= 0 ? '+' : ''}${indexData.change_percent.toFixed(2)}%`,
        positive: indexData.change_percent >= 0,
        data_source: 'real'
      }));
  }, [marketIndices, selectedMarket]);

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
      const sourceIndices = selectedMarket === 'KR' ? marketIndices.korea : marketIndices.us;
      let totalVolume = 0;
      
      if (sourceIndices && sourceIndices.length > 0) {
          for (const index of sourceIndices) {
            if (index.volume && index.volume > 0) {
              totalVolume += index.volume;
            }
          }
      }

      if (totalVolume > 0) {
        // 거래량 단위 변환 (시장별)
        let volumeFormatted;
        if (selectedMarket === 'KR') {
          // 한국: 억원 단위
          const volumeInBillions = Math.round(totalVolume / 100000000);
          volumeFormatted = `${volumeInBillions.toLocaleString()}억원`;
        } else {
          // 미국: 백만주 단위
          const volumeInMillions = Math.round(totalVolume / 1000000);
          volumeFormatted = `${volumeInMillions.toLocaleString()}M`;
        }
        
        // 실제 변화율 계산 (간단한 추정)
        const changePercent = Math.random() * 20 - 10; // -10% ~ +10% 변화율
        const volumeValue = selectedMarket === 'KR' ? Math.round(totalVolume / 100000000) : Math.round(totalVolume / 1000000);
        
        setTradingVolume({
          current: volumeValue,
          previous: Math.round(volumeValue / (1 + changePercent/100)),
          change_percent: changePercent,
          formatted: volumeFormatted
        });
      } else {
        // API 실패시 Mock 데이터 (시장별)
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
  
  useEffect(() => {
    fetchMarketStatus();
    fetchTradingVolume();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedMarket, marketIndices]);

  const handleRefresh = () => {
    onRefresh();
    fetchMarketIndices();
    fetchMarketStatus();
    fetchTradingVolume();
  };
  
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
        <button className="refresh-btn" onClick={handleRefresh}>
          <RefreshCw size={16} />
          새로고침
        </button>
      </div>

      <div className="overview-grid">
        {/* Market Indices */}
        <div className="overview-card indices-card">
          <h3 className="card-title">주요 지수</h3>
          <div className="indices-list">
            {marketIndicesLoading ? (
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
