import React, { useState, useEffect } from 'react';
import { TrendingUp, TrendingDown, BarChart3, Target, ChevronDown, ChevronUp, Activity, RefreshCw } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import './QuantView.css';

interface QuantViewProps {
  selectedMarket: 'KR' | 'US';
}

interface StockOption {
  symbol: string;
  name: string;
  currentPrice: number;
  market: string;
}

interface BacktestSettings {
  symbol: string;
  startDate: string;
  endDate: string;
  investmentAmount: number;
  strategy: 'buy_hold' | 'technical' | 'value';
}

interface BacktestResult {
  symbol: string;
  companyName: string;
  strategy: string;
  period: string;
  investmentAmount: number;
  finalAmount: number;
  totalReturn: number;
  totalReturnPercent: number;
  annualReturn: number;
  maxDrawdown: number;
  winRate: number;
  trades: number;
  bestTrade: number;
  worstTrade: number;
  startDate: string;
  endDate: string;
  startPrice: number;
  endPrice: number;
}

interface RecommendedStock {
  symbol: string;
  name: string;
  currentPrice: number;
  predictedPrice: number;
  predictedReturn: number;
  confidence: number;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  timeHorizon: string;
  reasoning: string[];
}


const QuantView: React.FC<QuantViewProps> = ({ selectedMarket }) => {
  const { quantData, quantDataLoading, quantDataLastUpdated, fetchQuantData } = useApp();
  const [activeTab, setActiveTab] = useState<'indicators' | 'backtest' | 'recommendations'>('indicators');
  const [availableStocks, setAvailableStocks] = useState<StockOption[]>([]);
  const [backtestSettings, setBacktestSettings] = useState<BacktestSettings>({
    symbol: '',
    startDate: '2024-01-01',
    endDate: '2025-07-02',
    investmentAmount: selectedMarket === 'KR' ? 1000000 : 1000, // 100만원 또는 $1000
    strategy: 'buy_hold'
  });
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendedStock[]>([]);
  const [sortField, setSortField] = useState<keyof import('../../context/AppContext').QuantIndicator>('limited_quant_score');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [filters, setFilters] = useState({
    per: { min: 0, max: 50 },
    pbr: { min: 0, max: 5 },
    roe: { min: 0, max: 100 },
    marketCap: { min: 0, max: 1000000 }
  });
  const [loading, setLoading] = useState(false);

  // 인기 종목 목록 (시장별)
  const popularStocks = {
    KR: [
      { symbol: '005930', name: '삼성전자', currentPrice: 67000 },
      { symbol: '000660', name: 'SK하이닉스', currentPrice: 89000 },
      { symbol: '035420', name: 'NAVER', currentPrice: 185000 },
      { symbol: '051910', name: 'LG화학', currentPrice: 380000 },
      { symbol: '005380', name: '현대차', currentPrice: 195000 },
      { symbol: '068270', name: '셀트리온', currentPrice: 178000 },
      { symbol: '035720', name: '카카오', currentPrice: 42000 },
      { symbol: '207940', name: '삼성바이오로직스', currentPrice: 850000 }
    ],
    US: [
      { symbol: 'AAPL', name: 'Apple Inc.', currentPrice: 193.50 },
      { symbol: 'MSFT', name: 'Microsoft Corp.', currentPrice: 450.30 },
      { symbol: 'GOOGL', name: 'Alphabet Inc.', currentPrice: 175.80 },
      { symbol: 'AMZN', name: 'Amazon.com Inc.', currentPrice: 188.40 },
      { symbol: 'TSLA', name: 'Tesla Inc.', currentPrice: 245.60 },
      { symbol: 'META', name: 'Meta Platforms', currentPrice: 520.80 },
      { symbol: 'NVDA', name: 'NVIDIA Corp.', currentPrice: 125.90 },
      { symbol: 'NFLX', name: 'Netflix Inc.', currentPrice: 650.20 }
    ]
  };

  useEffect(() => {
    setAvailableStocks(popularStocks[selectedMarket].map(stock => ({
      ...stock,
      market: selectedMarket
    })));
    
    // 첫 번째 종목을 기본 선택
    if (popularStocks[selectedMarket].length > 0) {
      setBacktestSettings(prev => ({
        ...prev,
        symbol: popularStocks[selectedMarket][0].symbol
      }));
    }

    generateRecommendations();
    // 퀀트 데이터 로드 (캐시된 데이터 사용)
    fetchQuantData(selectedMarket);
  }, [selectedMarket, fetchQuantData]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSort = (field: keyof import('../../context/AppContext').QuantIndicator) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const currentQuantData = quantData[selectedMarket] || [];
  
  const filteredAndSortedData = currentQuantData
    .filter(item => 
      item.per >= filters.per.min && item.per <= filters.per.max &&
      item.pbr >= filters.pbr.min && item.pbr <= filters.pbr.max &&
      item.estimated_roe >= filters.roe.min && item.estimated_roe <= filters.roe.max &&
      item.market_cap >= filters.marketCap.min && item.market_cap <= filters.marketCap.max
    )
    .sort((a, b) => {
      const aValue = a[sortField];
      const bValue = b[sortField];
      const direction = sortDirection === 'asc' ? 1 : -1;
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return (aValue - bValue) * direction;
      }
      return String(aValue).localeCompare(String(bValue)) * direction;
    });

  const SortIcon = ({ field }: { field: keyof import('../../context/AppContext').QuantIndicator }) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />;
  };

  const generateRecommendations = () => {
    const mockRecommendations: RecommendedStock[] = popularStocks[selectedMarket]
      .slice(0, 5)
      .map((stock, index) => {
        const predictedReturn = (Math.random() - 0.3) * 40; // -30% ~ +40%
        const predictedPrice = stock.currentPrice * (1 + predictedReturn / 100);
        const confidence = Math.random() * 40 + 60; // 60-100%
        
        return {
          symbol: stock.symbol,
          name: stock.name,
          currentPrice: stock.currentPrice,
          predictedPrice: Math.round(predictedPrice * 100) / 100,
          predictedReturn: Math.round(predictedReturn * 100) / 100,
          confidence: Math.round(confidence),
          riskLevel: confidence > 80 ? 'LOW' : confidence > 70 ? 'MEDIUM' : 'HIGH',
          timeHorizon: '3개월',
          reasoning: [
            '기술적 분석 상승 신호',
            '재무 지표 개선',
            '업계 전망 긍정적'
          ]
        };
      });

    setRecommendations(mockRecommendations);
  };

  const runBacktest = async () => {
    if (!backtestSettings.symbol) {
      alert('종목을 선택해주세요.');
      return;
    }

    setLoading(true);
    
    // 실제 API 호출 대신 시뮬레이션
    setTimeout(() => {
      const selectedStock = availableStocks.find(s => s.symbol === backtestSettings.symbol);
      if (!selectedStock) return;

      // 백테스트 시뮬레이션 계산
      const periodDays = Math.ceil((new Date(backtestSettings.endDate).getTime() - new Date(backtestSettings.startDate).getTime()) / (1000 * 60 * 60 * 24));
      const periodYears = periodDays / 365;
      
      // 가상의 수익률 계산 (실제로는 API에서 과거 데이터로 계산)
      const annualReturn = (Math.random() - 0.2) * 30; // -20% ~ +30%
      const totalReturn = annualReturn * periodYears;
      const finalAmount = backtestSettings.investmentAmount * (1 + totalReturn / 100);
      const profit = finalAmount - backtestSettings.investmentAmount;
      
      const result: BacktestResult = {
        symbol: backtestSettings.symbol,
        companyName: selectedStock.name,
        strategy: backtestSettings.strategy === 'buy_hold' ? '매수 후 보유' : backtestSettings.strategy === 'technical' ? '기술적 분석' : '가치 투자',
        period: `${periodDays}일 (${Math.round(periodYears * 10) / 10}년)`,
        investmentAmount: backtestSettings.investmentAmount,
        finalAmount: Math.round(finalAmount),
        totalReturn: Math.round(profit),
        totalReturnPercent: Math.round(totalReturn * 100) / 100,
        annualReturn: Math.round(annualReturn * 100) / 100,
        maxDrawdown: -(Math.random() * 15 + 5),
        winRate: Math.random() * 30 + 60,
        trades: backtestSettings.strategy === 'buy_hold' ? 1 : Math.floor(Math.random() * 10 + 5),
        bestTrade: Math.random() * 20 + 5,
        worstTrade: -(Math.random() * 15 + 3),
        startDate: backtestSettings.startDate,
        endDate: backtestSettings.endDate,
        startPrice: selectedStock.currentPrice * (0.8 + Math.random() * 0.4),
        endPrice: selectedStock.currentPrice
      };

      setBacktestResult(result);
      setLoading(false);
    }, 2000);
  };

  const formatCurrency = (amount: number) => {
    if (selectedMarket === 'KR') {
      return `${amount.toLocaleString()}원`;
    } else {
      return `$${amount.toLocaleString()}`;
    }
  };

  const renderBacktestTab = () => (
    <div className="backtest-section">
      <div className="section-header">
        <div className="section-header-content">
          <div className="section-icon">
            <Target size={18} />
          </div>
          <div className="section-info">
            <h3>개별 종목 백테스트</h3>
            <p>원하는 종목에 투자했다면 얼마의 수익/손실이 있었을지 시뮬레이션해보세요</p>
          </div>
        </div>
      </div>

      <div className="content-card">
        <div className="card-header">
          <div>
            <h4 className="card-title">백테스트 설정</h4>
            <p className="card-subtitle">투자 조건을 설정하고 백테스트를 실행하세요</p>
          </div>
        </div>
        
        <div className="form-grid backtest-grid">
          <div className="form-group">
            <label className="form-label">종목 선택</label>
            <select 
              className="form-select"
              value={backtestSettings.symbol} 
              onChange={(e) => setBacktestSettings(prev => ({ ...prev, symbol: e.target.value }))}
            >
              <option value="">종목을 선택하세요</option>
              {availableStocks.map(stock => (
                <option key={stock.symbol} value={stock.symbol}>
                  {stock.name} ({stock.symbol}) - {formatCurrency(stock.currentPrice)}
                </option>
              ))}
            </select>
          </div>
          
          <div className="form-group">
            <label className="form-label">투자 전략</label>
            <select 
              className="form-select"
              value={backtestSettings.strategy} 
              onChange={(e) => setBacktestSettings(prev => ({ ...prev, strategy: e.target.value as any }))}
            >
              <option value="buy_hold">매수 후 보유</option>
              <option value="technical">기술적 분석</option>
              <option value="value">가치 투자</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">시작 날짜</label>
            <input 
              className="form-input"
              type="date" 
              value={backtestSettings.startDate}
              max="2025-07-02"
              onChange={(e) => setBacktestSettings(prev => ({ ...prev, startDate: e.target.value }))}
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">종료 날짜</label>
            <input 
              className="form-input"
              type="date" 
              value={backtestSettings.endDate}
              max="2025-07-02"
              onChange={(e) => setBacktestSettings(prev => ({ ...prev, endDate: e.target.value }))}
            />
          </div>

          <div className="form-group">
            <label className="form-label">투자 금액</label>
            <input 
              className="form-input"
              type="number" 
              value={backtestSettings.investmentAmount}
              onChange={(e) => setBacktestSettings(prev => ({ ...prev, investmentAmount: Number(e.target.value) }))}
              placeholder={selectedMarket === 'KR' ? '1000000' : '1000'}
            />
            <div className="form-helper">{selectedMarket === 'KR' ? '원 (예: 1000000 = 100만원)' : '달러 (예: 1000 = $1,000)'}</div>
          </div>
          
          <div className="form-group button-group">
            <button 
              className="btn btn-primary" 
              onClick={runBacktest}
              disabled={loading || !backtestSettings.symbol}
            >
              {loading ? '백테스트 실행 중...' : '백테스트 실행'}
            </button>
          </div>
        </div>
      </div>

      {backtestResult && (
        <div className="backtest-result">
          <div className="result-header">
            <h4>{backtestResult.companyName} ({backtestResult.symbol}) 백테스트 결과</h4>
            <span className="result-strategy">{backtestResult.strategy} 전략 | {backtestResult.period}</span>
          </div>

          <div className="result-summary">
            <div className="summary-card">
              <div className="summary-label">투자 금액</div>
              <div className="summary-value">{formatCurrency(backtestResult.investmentAmount)}</div>
            </div>
            <div className="summary-card">
              <div className="summary-label">최종 금액</div>
              <div className="summary-value">{formatCurrency(backtestResult.finalAmount)}</div>
            </div>
            <div className={`summary-card ${backtestResult.totalReturn >= 0 ? 'profit' : 'loss'}`}>
              <div className="summary-label">총 수익/손실</div>
              <div className="summary-value">
                {backtestResult.totalReturn >= 0 ? '+' : ''}{formatCurrency(backtestResult.totalReturn)}
                <span className="percentage">({backtestResult.totalReturnPercent >= 0 ? '+' : ''}{backtestResult.totalReturnPercent}%)</span>
              </div>
            </div>
          </div>

          <div className="result-details">
            <div className="detail-row">
              <span>연간 수익률</span>
              <span className={backtestResult.annualReturn >= 0 ? 'positive' : 'negative'}>
                {backtestResult.annualReturn >= 0 ? '+' : ''}{backtestResult.annualReturn}%
              </span>
            </div>
            <div className="detail-row">
              <span>최대 낙폭</span>
              <span className="negative">{backtestResult.maxDrawdown.toFixed(1)}%</span>
            </div>
            <div className="detail-row">
              <span>승률</span>
              <span>{backtestResult.winRate.toFixed(1)}%</span>
            </div>
            <div className="detail-row">
              <span>거래 횟수</span>
              <span>{backtestResult.trades}회</span>
            </div>
          </div>

          <div className="result-interpretation">
            <h5>결과 해석</h5>
            <div className="interpretation-content">
              {backtestResult.totalReturn >= 0 ? (
                <div className="interpretation-positive">
                  <TrendingUp size={20} />
                  <span>
                    이 기간 동안 {backtestResult.companyName}에 투자했다면 <strong>{formatCurrency(Math.abs(backtestResult.totalReturn))}</strong>의 수익을 얻었을 것입니다.
                    연간 수익률은 <strong>{backtestResult.annualReturn.toFixed(1)}%</strong>입니다.
                  </span>
                </div>
              ) : (
                <div className="interpretation-negative">
                  <TrendingDown size={20} />
                  <span>
                    이 기간 동안 {backtestResult.companyName}에 투자했다면 <strong>{formatCurrency(Math.abs(backtestResult.totalReturn))}</strong>의 손실이 있었을 것입니다.
                    연간 손실률은 <strong>{Math.abs(backtestResult.annualReturn).toFixed(1)}%</strong>입니다.
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderIndicatorsTab = () => (
    <div className="quant-indicators">
      <div className="section-header">
        <div className="section-header-content">
          <div className="section-icon">
            <Activity size={18} />
          </div>
          <div className="section-info">
            <h3>퀀트 지표 분석</h3>
            <p>재무 지표와 기술적 지표를 종합하여 투자 가치를 평가합니다</p>
            {quantDataLastUpdated[selectedMarket] && (
              <small style={{ color: '#666', fontSize: '12px' }}>
                마지막 업데이트: {quantDataLastUpdated[selectedMarket]?.toLocaleTimeString()}
              </small>
            )}
          </div>
        </div>
        <div className="section-actions">
          <button 
            className="refresh-btn"
            onClick={() => fetchQuantData(selectedMarket, true)}
            disabled={quantDataLoading}
            title="퀀트 데이터 새로고침"
          >
            <RefreshCw size={16} className={quantDataLoading ? 'spinning' : ''} />
          </button>
        </div>
      </div>

      <div className="filters-section">
        <div className="filter-group">
          <label>PER</label>
          <input
            type="range"
            min="0"
            max="50"
            value={filters.per.max}
            onChange={(e) => setFilters(prev => ({ ...prev, per: { ...prev.per, max: Number(e.target.value) } }))}
          />
          <span>{filters.per.min} - {filters.per.max}</span>
        </div>
        <div className="filter-group">
          <label>PBR</label>
          <input
            type="range"
            min="0"
            max="5"
            step="0.1"
            value={filters.pbr.max}
            onChange={(e) => setFilters(prev => ({ ...prev, pbr: { ...prev.pbr, max: Number(e.target.value) } }))}
          />
          <span>{filters.pbr.min} - {filters.pbr.max}</span>
        </div>
        <div className="filter-group">
          <label>ROE (%)</label>
          <input
            type="range"
            min="0"
            max="100"
            value={filters.roe.max}
            onChange={(e) => setFilters(prev => ({ ...prev, roe: { ...prev.roe, max: Number(e.target.value) } }))}
          />
          <span>{filters.roe.min} - {filters.roe.max}</span>
        </div>
      </div>

      <div className="content-card">
        <table className="data-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('name')}>
                종목명 <SortIcon field="name" />
              </th>
              <th onClick={() => handleSort('per')}>
                PER <SortIcon field="per" />
              </th>
              <th onClick={() => handleSort('pbr')}>
                PBR <SortIcon field="pbr" />
              </th>
              <th onClick={() => handleSort('estimated_roe')}>
                추정ROE(%) <SortIcon field="estimated_roe" />
              </th>
              <th onClick={() => handleSort('eps')}>
                EPS <SortIcon field="eps" />
              </th>
              <th onClick={() => handleSort('current_price')}>
                현재가 <SortIcon field="current_price" />
              </th>
              <th onClick={() => handleSort('momentum_3m')}>
                3개월 수익률(%) <SortIcon field="momentum_3m" />
              </th>
              <th onClick={() => handleSort('volatility')}>
                변동성(%) <SortIcon field="volatility" />
              </th>
              <th onClick={() => handleSort('limited_quant_score')}>
                퀀트 점수 <SortIcon field="limited_quant_score" />
              </th>
              <th>
                데이터 상태
              </th>
              <th>추천</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedData.map((item) => (
              <tr key={item.symbol}>
                <td>
                  <div className="stock-info">
                    <span className="stock-name">{item.name}</span>
                    <span className="stock-symbol">({item.symbol})</span>
                  </div>
                </td>
                <td>{item.per}</td>
                <td>{item.pbr}</td>
                <td className={item.estimated_roe > 15 ? 'status-positive' : item.estimated_roe < 5 ? 'status-negative' : ''}>
                  {item.estimated_roe}
                </td>
                <td>{item.eps.toLocaleString()}</td>
                <td>{item.current_price.toLocaleString()}</td>
                <td className={item.momentum_3m > 0 ? 'status-positive' : 'status-negative'}>
                  {item.momentum_3m > 0 ? '+' : ''}{item.momentum_3m}
                </td>
                <td className={item.volatility < 20 ? 'status-positive' : item.volatility > 30 ? 'status-negative' : ''}>
                  {item.volatility}
                </td>
                <td>
                  <div className="quant-score">
                    <span className={`score ${item.limited_quant_score > 70 ? 'high' : item.limited_quant_score > 40 ? 'medium' : 'low'}`}>
                      {item.limited_quant_score}
                    </span>
                  </div>
                </td>
                <td>
                  <span className={`data-status ${item.data_completeness === 'FULL' ? 'full' : 'limited'}`}>
                    {item.data_completeness === 'FULL' ? '완전' : '제한적'}
                  </span>
                </td>
                <td>
                  <span className={`badge ${item.recommendation === 'BUY' ? 'badge-buy' : item.recommendation === 'SELL' ? 'badge-sell' : 'badge-hold'}`}>
                    {item.recommendation === 'BUY' ? '매수' : item.recommendation === 'SELL' ? '매도' : '보유'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderRecommendationsTab = () => (
    <div className="recommendations-section">
      <div className="section-header">
        <div className="section-header-content">
          <div className="section-icon">
            <TrendingUp size={18} />
          </div>
          <div className="section-info">
            <h3>AI 투자 추천</h3>
            <p>현재 시장 분석을 바탕으로 향후 3개월 수익 가능성이 높은 종목들을 추천합니다</p>
          </div>
        </div>
      </div>

      <div className="recommendations-grid">
        {recommendations.map((rec, index) => (
          <div key={rec.symbol} className="recommendation-card">
            <div className="rec-header">
              <div className="rec-rank">#{index + 1}</div>
              <div className="rec-risk-badge" data-risk={rec.riskLevel.toLowerCase()}>
                {rec.riskLevel === 'LOW' ? '안전' : rec.riskLevel === 'MEDIUM' ? '보통' : '위험'}
              </div>
            </div>
            
            <div className="rec-company">
              <h4>{rec.name}</h4>
              <span className="rec-symbol">({rec.symbol})</span>
            </div>

            <div className="rec-prices">
              <div className="price-row">
                <span>현재가</span>
                <span className="current-price">{formatCurrency(rec.currentPrice)}</span>
              </div>
              <div className="price-row">
                <span>예상가 ({rec.timeHorizon})</span>
                <span className="predicted-price">{formatCurrency(rec.predictedPrice)}</span>
              </div>
            </div>

            <div className={`rec-return ${rec.predictedReturn >= 0 ? 'positive' : 'negative'}`}>
              <span className="return-label">예상 수익률</span>
              <span className="return-value">
                {rec.predictedReturn >= 0 ? '+' : ''}{rec.predictedReturn}%
              </span>
            </div>

            <div className="rec-confidence">
              <span>신뢰도: {rec.confidence}%</span>
              <div className="confidence-bar">
                <div className="confidence-fill" style={{ width: `${rec.confidence}%` }}></div>
              </div>
            </div>

            <div className="rec-reasoning">
              <h5>추천 이유</h5>
              <ul>
                {rec.reasoning.map((reason, idx) => (
                  <li key={idx}>{reason}</li>
                ))}
              </ul>
            </div>

            <button 
              className="rec-backtest-btn"
              onClick={() => {
                setBacktestSettings(prev => ({ ...prev, symbol: rec.symbol }));
                setActiveTab('backtest');
              }}
            >
              백테스트 해보기
            </button>
          </div>
        ))}
      </div>
    </div>
  );

  return (
    <div className="quant-view">

      <div className="quant-tabs">
        <div className="tabs-container">
          <button
            className={`tab-button ${activeTab === 'indicators' ? 'active' : ''}`}
            onClick={() => setActiveTab('indicators')}
          >
            <Activity className="tab-icon" size={20} />
            <span className="tab-label">퀀트 지표</span>
          </button>
          <button
            className={`tab-button ${activeTab === 'backtest' ? 'active' : ''}`}
            onClick={() => setActiveTab('backtest')}
          >
            <BarChart3 className="tab-icon" size={20} />
            <span className="tab-label">백테스트</span>
          </button>
          <button
            className={`tab-button ${activeTab === 'recommendations' ? 'active' : ''}`}
            onClick={() => setActiveTab('recommendations')}
          >
            <TrendingUp className="tab-icon" size={20} />
            <span className="tab-label">AI 추천</span>
          </button>
        </div>
      </div>

      <div className="quant-content">
        <div className="content-container">
          {(quantDataLoading && currentQuantData.length === 0) && (
            <div className="loading">
              <div className="loading-spinner"></div>
              <div className="loading-text">퀀트 지표 분석 중...</div>
              <div className="loading-subtext">캐시된 데이터가 없어 새로 로딩하고 있습니다</div>
            </div>
          )}
          {activeTab === 'indicators' && renderIndicatorsTab()}
          {activeTab === 'backtest' && renderBacktestTab()}
          {activeTab === 'recommendations' && renderRecommendationsTab()}
        </div>
      </div>
    </div>
  );
};

export default QuantView;