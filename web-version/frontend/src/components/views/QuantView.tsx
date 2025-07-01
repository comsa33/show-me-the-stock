import React, { useState, useEffect } from 'react';
import { Calculator, ChevronDown, ChevronUp } from 'lucide-react';
import './QuantView.css';

interface QuantViewProps {
  selectedMarket: 'KR' | 'US';
}

interface QuantIndicator {
  symbol: string;
  name: string;
  market: string;
  per: number;
  pbr: number;
  roe: number;
  roa: number;
  debtRatio: number;
  momentum3m: number;
  marketCap: number;
  volatility: number;
  quantScore: number;
  recommendation: 'BUY' | 'HOLD' | 'SELL';
}

interface FactorStrategy {
  id: string;
  name: string;
  description: string;
  factors: string[];
  isActive: boolean;
}

interface BacktestResult {
  strategy: string;
  totalReturn: number;
  annualReturn: number;
  maxDrawdown: number;
  sharpeRatio: number;
  winRate: number;
  startDate: string;
  endDate: string;
}

const QuantView: React.FC<QuantViewProps> = ({ selectedMarket }) => {
  const [activeTab, setActiveTab] = useState<'indicators' | 'strategies' | 'backtest'>('indicators');
  const [quantData, setQuantData] = useState<QuantIndicator[]>([]);
  const [strategies, setStrategies] = useState<FactorStrategy[]>([]);
  const [backtestResults, setBacktestResults] = useState<BacktestResult[]>([]);
  const [sortField, setSortField] = useState<keyof QuantIndicator>('quantScore');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [filters, setFilters] = useState({
    per: { min: 0, max: 50 },
    pbr: { min: 0, max: 5 },
    roe: { min: 0, max: 100 },
    marketCap: { min: 0, max: 1000000 }
  });
  const [loading, setLoading] = useState(true);

  const factorStrategies: FactorStrategy[] = [
    {
      id: 'value',
      name: '가치 전략 (Value)',
      description: '저평가된 우량 기업을 선별하여 투자',
      factors: ['PER < 15', 'PBR < 1.5', 'ROE > 10%'],
      isActive: false
    },
    {
      id: 'momentum',
      name: '모멘텀 전략 (Momentum)',
      description: '상승 추세가 지속되는 종목에 투자',
      factors: ['3개월 수익률 > 15%', '거래량 증가', '기술적 지표 양호'],
      isActive: false
    },
    {
      id: 'quality',
      name: '품질 전략 (Quality)',
      description: '재무 건전성이 우수한 기업에 투자',
      factors: ['ROE > 15%', '부채비율 < 50%', '매출 성장 > 10%'],
      isActive: false
    },
    {
      id: 'lowvol',
      name: '저변동성 전략 (Low Volatility)',
      description: '변동성이 낮은 안정적인 종목에 투자',
      factors: ['변동성 < 20%', '베타 < 1.0', '배당수익률 > 3%'],
      isActive: false
    },
    {
      id: 'size',
      name: '소형주 전략 (Size)',
      description: '성장 잠재력이 큰 소형주에 투자',
      factors: ['시가총액 < 1조원', '매출 성장 > 20%', 'PEG < 1.0'],
      isActive: false
    }
  ];

  useEffect(() => {
    const fetchQuantData = async () => {
      setLoading(true);
      try {
        const response = await fetch(`/api/v1/quant/indicators?market=${selectedMarket}`);
        if (response.ok) {
          const data = await response.json();
          setQuantData(data);
        } else {
          generateMockData();
        }
      } catch (error) {
        console.error('퀀트 데이터 로딩 실패:', error);
        generateMockData();
      } finally {
        setLoading(false);
      }
    };

    const generateMockData = () => {
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
        const roa = Math.random() * 15 + 2;
        const debtRatio = Math.random() * 80 + 10;
        const momentum3m = (Math.random() - 0.5) * 40;
        const marketCap = Math.random() * 500000 + 10000;
        const volatility = Math.random() * 30 + 10;
        
        const quantScore = Math.max(0, Math.min(100, 
          (1 / per) * 100 + 
          (1 / pbr) * 50 + 
          roe * 2 + 
          roa * 3 + 
          (100 - debtRatio) * 0.5 +
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
          roe: Number(roe.toFixed(2)),
          roa: Number(roa.toFixed(2)),
          debtRatio: Number(debtRatio.toFixed(2)),
          momentum3m: Number(momentum3m.toFixed(2)),
          marketCap: Number(marketCap.toFixed(0)),
          volatility: Number(volatility.toFixed(2)),
          quantScore: Number(quantScore.toFixed(1)),
          recommendation
        });
      }
      setQuantData(mockData);
    };

    fetchQuantData();
    setStrategies(factorStrategies);
  }, [selectedMarket]); // eslint-disable-line react-hooks/exhaustive-deps

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
      item.roe >= filters.roe.min && item.roe <= filters.roe.max &&
      item.marketCap >= filters.marketCap.min && item.marketCap <= filters.marketCap.max
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

  const runBacktest = async (strategyId: string) => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/quant/backtest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          strategy: strategyId,
          market: selectedMarket,
          period: '1y'
        })
      });

      if (response.ok) {
        const result = await response.json();
        setBacktestResults(prev => [...prev.filter(r => r.strategy !== strategyId), result]);
      } else {
        generateMockBacktestResult(strategyId);
      }
    } catch (error) {
      console.error('백테스트 실행 실패:', error);
      generateMockBacktestResult(strategyId);
    } finally {
      setLoading(false);
    }
  };

  const generateMockBacktestResult = (strategyId: string) => {
    const mockResult: BacktestResult = {
      strategy: strategyId,
      totalReturn: (Math.random() - 0.3) * 50,
      annualReturn: (Math.random() - 0.2) * 30,
      maxDrawdown: -(Math.random() * 20 + 5),
      sharpeRatio: Math.random() * 2 + 0.5,
      winRate: Math.random() * 40 + 50,
      startDate: '2023-01-01',
      endDate: '2023-12-31'
    };
    setBacktestResults(prev => [...prev.filter(r => r.strategy !== strategyId), mockResult]);
  };

  const SortIcon = ({ field }: { field: keyof QuantIndicator }) => {
    if (sortField !== field) return null;
    return sortDirection === 'asc' ? <ChevronUp size={16} /> : <ChevronDown size={16} />;
  };

  const renderIndicatorsTab = () => (
    <div className="quant-indicators">
      <div className="indicators-header">
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
              <th onClick={() => handleSort('roe')}>
                ROE(%) <SortIcon field="roe" />
              </th>
              <th onClick={() => handleSort('roa')}>
                ROA(%) <SortIcon field="roa" />
              </th>
              <th onClick={() => handleSort('debtRatio')}>
                부채비율(%) <SortIcon field="debtRatio" />
              </th>
              <th onClick={() => handleSort('momentum3m')}>
                3개월 수익률(%) <SortIcon field="momentum3m" />
              </th>
              <th onClick={() => handleSort('volatility')}>
                변동성(%) <SortIcon field="volatility" />
              </th>
              <th onClick={() => handleSort('quantScore')}>
                퀀트 점수 <SortIcon field="quantScore" />
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
                <td className={item.roe > 15 ? 'positive' : item.roe < 5 ? 'negative' : ''}>
                  {item.roe}
                </td>
                <td className={item.roa > 10 ? 'positive' : item.roa < 3 ? 'negative' : ''}>
                  {item.roa}
                </td>
                <td className={item.debtRatio < 30 ? 'positive' : item.debtRatio > 70 ? 'negative' : ''}>
                  {item.debtRatio}
                </td>
                <td className={item.momentum3m > 0 ? 'positive' : 'negative'}>
                  {item.momentum3m > 0 ? '+' : ''}{item.momentum3m}
                </td>
                <td className={item.volatility < 20 ? 'positive' : item.volatility > 30 ? 'negative' : ''}>
                  {item.volatility}
                </td>
                <td>
                  <div className="quant-score">
                    <span className={`score ${item.quantScore > 70 ? 'high' : item.quantScore > 40 ? 'medium' : 'low'}`}>
                      {item.quantScore}
                    </span>
                  </div>
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

  const renderStrategiesTab = () => (
    <div className="quant-strategies">
      <div className="strategies-grid">
        {strategies.map((strategy) => (
          <div key={strategy.id} className="strategy-card">
            <div className="strategy-header">
              <h3>{strategy.name}</h3>
              <button
                className={`strategy-toggle ${strategy.isActive ? 'active' : ''}`}
                onClick={() => setStrategies(prev => 
                  prev.map(s => s.id === strategy.id ? { ...s, isActive: !s.isActive } : s)
                )}
              >
                {strategy.isActive ? '활성화' : '비활성화'}
              </button>
            </div>
            <p className="strategy-description">{strategy.description}</p>
            <div className="strategy-factors">
              <h4>선별 조건:</h4>
              <ul>
                {strategy.factors.map((factor, index) => (
                  <li key={index}>{factor}</li>
                ))}
              </ul>
            </div>
            <div className="strategy-actions">
              <button
                className="backtest-btn"
                onClick={() => runBacktest(strategy.id)}
                disabled={loading}
              >
                백테스트 실행
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderBacktestTab = () => (
    <div className="quant-backtest">
      <div className="backtest-results">
        {backtestResults.length === 0 ? (
          <div className="no-results">
            <p>전략 탭에서 백테스트를 실행해보세요.</p>
          </div>
        ) : (
          <div className="results-grid">
            {backtestResults.map((result) => (
              <div key={result.strategy} className="result-card">
                <h3>{strategies.find(s => s.id === result.strategy)?.name}</h3>
                <div className="result-metrics">
                  <div className="metric">
                    <label>총 수익률</label>
                    <span className={result.totalReturn >= 0 ? 'positive' : 'negative'}>
                      {result.totalReturn >= 0 ? '+' : ''}{result.totalReturn.toFixed(2)}%
                    </span>
                  </div>
                  <div className="metric">
                    <label>연간 수익률</label>
                    <span className={result.annualReturn >= 0 ? 'positive' : 'negative'}>
                      {result.annualReturn >= 0 ? '+' : ''}{result.annualReturn.toFixed(2)}%
                    </span>
                  </div>
                  <div className="metric">
                    <label>최대 낙폭</label>
                    <span className="negative">{result.maxDrawdown.toFixed(2)}%</span>
                  </div>
                  <div className="metric">
                    <label>샤프 비율</label>
                    <span>{result.sharpeRatio.toFixed(2)}</span>
                  </div>
                  <div className="metric">
                    <label>승률</label>
                    <span>{result.winRate.toFixed(1)}%</span>
                  </div>
                </div>
                <div className="result-period">
                  <small>{result.startDate} ~ {result.endDate}</small>
                </div>
              </div>
            ))}
          </div>
        )}
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
              <h1>퀀트 투자 분석</h1>
              <p>데이터 기반 투자 전략 및 백테스트</p>
            </div>
          </div>
          <div className="header-right">
            <div className="market-indicator">
              <span className="market-label">{selectedMarket === 'KR' ? '한국' : '미국'} 시장</span>
            </div>
          </div>
        </div>
      </div>

      <div className="quant-tabs">
        <button
          className={`tab-button ${activeTab === 'indicators' ? 'active' : ''}`}
          onClick={() => setActiveTab('indicators')}
        >
          퀀트 지표
        </button>
        <button
          className={`tab-button ${activeTab === 'strategies' ? 'active' : ''}`}
          onClick={() => setActiveTab('strategies')}
        >
          팩터 전략
        </button>
        <button
          className={`tab-button ${activeTab === 'backtest' ? 'active' : ''}`}
          onClick={() => setActiveTab('backtest')}
        >
          백테스트 결과
        </button>
      </div>

      <div className="quant-content">
        {loading && <div className="loading">데이터 로딩 중...</div>}
        {!loading && activeTab === 'indicators' && renderIndicatorsTab()}
        {!loading && activeTab === 'strategies' && renderStrategiesTab()}
        {!loading && activeTab === 'backtest' && renderBacktestTab()}
      </div>
    </div>
  );
};

export default QuantView;