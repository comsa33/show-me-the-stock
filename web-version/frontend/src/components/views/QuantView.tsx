import React, { useState, useEffect } from 'react';
import { Calculator, TrendingUp, TrendingDown, BarChart3, Target, ChevronDown, ChevronUp, Activity } from 'lucide-react';
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

interface QuantIndicator {
  symbol: string;
  name: string;
  market: string;
  per: number;
  pbr: number;
  eps: number;
  bps: number;
  current_price: number;
  market_cap: number;
  estimated_roe: number;
  momentum_3m: number;
  volatility: number;
  limited_quant_score: number;
  recommendation: 'BUY' | 'HOLD' | 'SELL';
  data_completeness: 'FULL' | 'LIMITED';
}

const QuantView: React.FC<QuantViewProps> = ({ selectedMarket }) => {
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
  const [quantData, setQuantData] = useState<QuantIndicator[]>([]);
  const [sortField, setSortField] = useState<keyof QuantIndicator>('limited_quant_score');
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
    fetchQuantData();
  }, [selectedMarket]); // eslint-disable-line react-hooks/exhaustive-deps
  
  const fetchQuantData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/quant/indicators?market=${selectedMarket}`);
      if (response.ok) {
        const data = await response.json();
        setQuantData(data);
      } else {
        generateMockQuantData();
      }
    } catch (error) {
      console.error('퀀트 데이터 로딩 실패:', error);
      generateMockQuantData();
    } finally {
      setLoading(false);
    }
  };

  const generateMockQuantData = () => {
    const mockData: QuantIndicator[] = [];
    const symbols = selectedMarket === 'KR' 
      ? ['005930', '000660', '035420', '051910', '005380', '068270', '006400', '035720', '207940', '066570']
      : ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE', 'CRM'];
    
    const names = selectedMarket === 'KR'
      ? ['삼성전자', 'SK하이닉스', 'NAVER', 'LG화학', '현대차', '셀트리온', '삼성SDI', '카카오', '삼성바이오로직스', 'LG전자']
      : ['Apple', 'Microsoft', 'Alphabet', 'Amazon', 'Tesla', 'Meta', 'NVIDIA', 'Netflix', 'Adobe', 'Salesforce'];

    for (let i = 0; i < symbols.length; i++) {
      const per = Math.random() * 40 + 5;
      const pbr = Math.random() * 4 + 0.5;
      const roe = Math.random() * 30 + 5;
      const momentum3m = (Math.random() - 0.5) * 40;
      const marketCap = Math.random() * 500000 + 10000;
      const volatility = Math.random() * 30 + 10;
      const currentPrice = selectedMarket === 'KR' ? Math.random() * 50000 + 10000 : Math.random() * 300 + 50;
      
      const quantScore = Math.max(0, Math.min(100, 
        (1 / per) * 100 + 
        (1 / pbr) * 50 + 
        roe * 2 + 
        momentum3m * 0.5 +
        (50 - volatility) * 0.5
      ));

      let recommendation: 'BUY' | 'HOLD' | 'SELL' = 'HOLD';
      if (quantScore > 70) recommendation = 'BUY';
      else if (quantScore < 40) recommendation = 'SELL';

      mockData.push({
        symbol: symbols[i],
        name: names[i],
        market: selectedMarket,
        per: Number(per.toFixed(2)),
        pbr: Number(pbr.toFixed(2)),
        eps: Number((currentPrice / per).toFixed(0)),
        bps: Number((currentPrice / pbr).toFixed(0)),
        current_price: Number(currentPrice.toFixed(2)),
        market_cap: Number(marketCap.toFixed(0)),
        estimated_roe: Number(roe.toFixed(2)),
        momentum_3m: Number(momentum3m.toFixed(2)),
        volatility: Number(volatility.toFixed(2)),
        limited_quant_score: Number(quantScore.toFixed(1)),
        recommendation,
        data_completeness: 'LIMITED' as const
      });
    }
    setQuantData(mockData);
  };

  const handleSort = (field: keyof QuantIndicator) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const filteredAndSortedData = quantData
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

  const SortIcon = ({ field }: { field: keyof QuantIndicator }) => {
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
      <div className="backtest-header">
        <div className="header-icon">
          <Target size={24} />
        </div>
        <div>
          <h3>개별 종목 백테스트</h3>
          <p>원하는 종목에 투자했다면 얼마의 수익/손실이 있었을지 시뮬레이션해보세요</p>
        </div>
      </div>

      <div className="backtest-form">
        <div className="form-row">
          <div className="form-group">
            <label>종목 선택</label>
            <select 
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
            <label>투자 전략</label>
            <select 
              value={backtestSettings.strategy} 
              onChange={(e) => setBacktestSettings(prev => ({ ...prev, strategy: e.target.value as any }))}
            >
              <option value="buy_hold">매수 후 보유</option>
              <option value="technical">기술적 분석</option>
              <option value="value">가치 투자</option>
            </select>
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>시작 날짜</label>
            <input 
              type="date" 
              value={backtestSettings.startDate}
              max="2025-07-02"
              onChange={(e) => setBacktestSettings(prev => ({ ...prev, startDate: e.target.value }))}
            />
          </div>
          
          <div className="form-group">
            <label>종료 날짜</label>
            <input 
              type="date" 
              value={backtestSettings.endDate}
              max="2025-07-02"
              onChange={(e) => setBacktestSettings(prev => ({ ...prev, endDate: e.target.value }))}
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>투자 금액</label>
            <input 
              type="number" 
              value={backtestSettings.investmentAmount}
              onChange={(e) => setBacktestSettings(prev => ({ ...prev, investmentAmount: Number(e.target.value) }))}
              placeholder={selectedMarket === 'KR' ? '1000000' : '1000'}
            />
            <small>{selectedMarket === 'KR' ? '원 (예: 1000000 = 100만원)' : '달러 (예: 1000 = $1,000)'}</small>
          </div>
          
          <div className="form-group">
            <button 
              className="backtest-run-btn" 
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
      <div className="indicators-header">
        <div className="header-icon">
          <Activity size={24} />
        </div>
        <div>
          <h3>퀀트 지표 분석</h3>
          <p>재무 지표와 기술적 지표를 종합하여 투자 가치를 평가합니다</p>
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

      <div className="indicators-table">
        <table>
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
                <td className={item.estimated_roe > 15 ? 'positive' : item.estimated_roe < 5 ? 'negative' : ''}>
                  {item.estimated_roe}
                </td>
                <td>{item.eps.toLocaleString()}</td>
                <td>{item.current_price.toLocaleString()}</td>
                <td className={item.momentum_3m > 0 ? 'positive' : 'negative'}>
                  {item.momentum_3m > 0 ? '+' : ''}{item.momentum_3m}
                </td>
                <td className={item.volatility < 20 ? 'positive' : item.volatility > 30 ? 'negative' : ''}>
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
                  <span className={`recommendation ${item.recommendation.toLowerCase()}`}>
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
      <div className="recommendations-header">
        <div className="header-icon">
          <TrendingUp size={24} />
        </div>
        <div>
          <h3>AI 투자 추천</h3>
          <p>현재 시장 분석을 바탕으로 향후 3개월 수익 가능성이 높은 종목들을 추천합니다</p>
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
      <div className="quant-header">
        <div className="header-content">
          <div className="header-left">
            <Calculator className="header-icon" size={28} />
            <div>
              <h1>스마트 투자 분석</h1>
              <p>종목별 백테스트와 AI 추천으로 더 나은 투자 결정을 내려보세요</p>
            </div>
          </div>
          <div className="header-right">
            <div className="market-selector">
              <div className="market-badge">
                <span className="market-flag">{selectedMarket === 'KR' ? '🇰🇷' : '🇺🇸'}</span>
                <div className="market-text">
                  <span className="market-name">{selectedMarket === 'KR' ? '한국' : '미국'}</span>
                  <span className="market-desc">시장 분석</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="quant-tabs">
        <button
          className={`tab-button ${activeTab === 'indicators' ? 'active' : ''}`}
          onClick={() => setActiveTab('indicators')}
        >
          <Activity size={16} />
          퀀트 지표
        </button>
        <button
          className={`tab-button ${activeTab === 'backtest' ? 'active' : ''}`}
          onClick={() => setActiveTab('backtest')}
        >
          <BarChart3 size={16} />
          백테스트
        </button>
        <button
          className={`tab-button ${activeTab === 'recommendations' ? 'active' : ''}`}
          onClick={() => setActiveTab('recommendations')}
        >
          <TrendingUp size={16} />
          AI 추천
        </button>
      </div>

      <div className="quant-content">
        {loading && <div className="loading">데이터 로딩 중...</div>}
        {!loading && activeTab === 'indicators' && renderIndicatorsTab()}
        {!loading && activeTab === 'backtest' && renderBacktestTab()}
        {!loading && activeTab === 'recommendations' && renderRecommendationsTab()}
      </div>
    </div>
  );
};

export default QuantView;