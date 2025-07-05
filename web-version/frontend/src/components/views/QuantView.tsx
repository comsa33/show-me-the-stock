import React, { useState, useEffect, useCallback } from 'react';
import { TrendingUp, TrendingDown, BarChart3, Target, ChevronDown, ChevronUp, Activity, RefreshCw } from 'lucide-react';
import { useApp } from '../../context/AppContext';
import SearchableSelect from '../common/SearchableSelect';
import { API_BASE } from '../../config';
import { stockCache } from '../../utils/stockCache';
import './QuantView.css';

interface QuantViewProps {
  selectedMarket: 'KR' | 'US';
}

interface StockOption {
  symbol: string;
  name: string;
  currentPrice?: number;
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
  timeHorizon: 'SHORT' | 'MEDIUM' | 'LONG';
  keyIndicators: {
    PER?: number;
    PBR?: number;
    ROE?: number;
    quantScore?: number;
    [key: string]: number | undefined;
  };
  reasoning: string[];
  warnings?: string[];
}


const QuantView: React.FC<QuantViewProps> = ({ selectedMarket }) => {
  const { quantData, quantDataLoading, quantDataLastUpdated, fetchQuantData, setSelectedStock, setCurrentView } = useApp();
  const [activeTab, setActiveTab] = useState<'indicators' | 'backtest' | 'recommendations'>('indicators');
  const [availableStocks, setAvailableStocks] = useState<StockOption[]>([]);
  const [stocksLoading, setStocksLoading] = useState(false);
  // 백테스트 기본 날짜 설정 (최근 3개월)
  const getDefaultDates = () => {
    const endDate = new Date();
    endDate.setDate(endDate.getDate() - 1); // 어제
    const startDate = new Date(endDate);
    startDate.setMonth(startDate.getMonth() - 3); // 3개월 전
    
    return {
      start: startDate.toISOString().split('T')[0],
      end: endDate.toISOString().split('T')[0]
    };
  };

  const defaultDates = getDefaultDates();
  const [backtestSettings, setBacktestSettings] = useState<BacktestSettings>({
    symbol: '',
    startDate: defaultDates.start,
    endDate: defaultDates.end,
    investmentAmount: selectedMarket === 'KR' ? 1000000 : 1000, // 100만원 또는 $1000
    strategy: 'buy_hold'
  });
  const [backtestResult, setBacktestResult] = useState<BacktestResult | null>(null);
  const [recommendations, setRecommendations] = useState<RecommendedStock[]>([]);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);
  const [recommendationsFetched, setRecommendationsFetched] = useState(false);
  const [sortField, setSortField] = useState<keyof import('../../context/AppContext').QuantIndicator>('quant_score');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [filters, setFilters] = useState({
    per: { min: 0, max: 50 },
    pbr: { min: 0, max: 5 },
    roe: { min: 0, max: 100 },
    marketCap: { min: 0, max: 10000000 } // 10조원으로 증가
  });
  const [loading, setLoading] = useState(false);

  // 백엔드에서 종목 목록 가져오기
  const fetchStocks = useCallback(async () => {
    const cacheKey = `stocks_simple_${selectedMarket}`;
    
    // 캐시 확인
    const cached = stockCache.get<StockOption[]>(cacheKey);
    if (cached) {
      setAvailableStocks(cached);
      setStocksLoading(false);
      return;
    }
    
    // 캐시가 없으면 API 호출
    setStocksLoading(true);
    try {
      const response = await fetch(`${API_BASE}/v1/stocks/list/simple?market=${selectedMarket}`);
      if (!response.ok) throw new Error('Failed to fetch stocks');
      const data = await response.json();
      
      // API 응답 형식에 맞게 처리
      const stocks = (data.stocks || data).map((stock: any) => ({
        symbol: stock.symbol,
        name: stock.name,
        market: stock.market || selectedMarket
      }));
      setAvailableStocks(stocks);
      
      // 캐시에 저장 (24시간)
      stockCache.set(cacheKey, stocks);
    } catch (error) {
      console.error('Failed to fetch stocks:', error);
      // 실패 시 빈 배열
      setAvailableStocks([]);
    } finally {
      setStocksLoading(false);
    }
  }, [selectedMarket]);

  // AI 추천 가져오기
  const fetchAIRecommendations = useCallback(async () => {
    const cacheKey = `ai_recommendations_${selectedMarket}`;
    
    // 캐시 확인 (빈 배열이 아닌 경우에만 사용)
    const cached = stockCache.get<RecommendedStock[]>(cacheKey);
    if (cached && cached.length > 0) {
      setRecommendations(cached);
      setRecommendationsLoading(false);
      return;
    }
    
    setRecommendationsLoading(true);
    try {
      const url = `${API_BASE}/v1/ai-recommendations/top-stocks?market=${selectedMarket}&top_n=6`;
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch AI recommendations');
      
      const data = await response.json();
      const recommendations = data.recommendations || [];
      
      setRecommendations(recommendations);
      // 캐시에 저장 (1시간) - 데이터가 있을 때만
      if (recommendations.length > 0) {
        stockCache.set(cacheKey, recommendations, 60 * 60 * 1000);
      }
    } catch (error) {
      console.error('Failed to fetch AI recommendations:', error);
      // 실패 시 빈 배열
      setRecommendations([]);
    } finally {
      setRecommendationsLoading(false);
    }
  }, [selectedMarket]);

  useEffect(() => {
    // 종목 목록 가져오기
    fetchStocks();
    
    // 퀀트 데이터 로드 (캐시된 데이터 사용)
    fetchQuantData(selectedMarket);
    
    // 시장이 변경되면 백테스트 결과 초기화
    setBacktestResult(null);
    // 백테스트 설정에서 종목 선택과 투자금액 초기화
    setBacktestSettings(prev => ({
      ...prev,
      symbol: '',
      investmentAmount: selectedMarket === 'KR' ? 1000000 : 1000
    }));
    // AI 추천도 다시 가져와야 함
    setRecommendationsFetched(false);
  }, [selectedMarket, fetchQuantData, fetchStocks]);

  // AI 추천 탭이 활성화될 때 데이터 가져오기
  useEffect(() => {
    if (activeTab === 'recommendations' && !recommendationsFetched && !recommendationsLoading) {
      fetchAIRecommendations();
      setRecommendationsFetched(true);
    }
  }, [activeTab, recommendationsFetched, recommendationsLoading, fetchAIRecommendations]);

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
    .filter(item => {
      const per = item.per ?? 999;
      const pbr = item.pbr ?? 999;
      const roe = item.roe ?? item.estimated_roe ?? 0;
      const marketCap = item.market_cap ?? 0;
      
      return per >= filters.per.min && per <= filters.per.max &&
             pbr >= filters.pbr.min && pbr <= filters.pbr.max &&
             roe >= filters.roe.min && roe <= filters.roe.max &&
             marketCap >= filters.marketCap.min * 1000000000; // Convert from billion to won
    })
    .sort((a, b) => {
      let aValue: any = a[sortField];
      let bValue: any = b[sortField];
      
      // Handle MongoDB vs legacy API compatibility
      if (sortField === 'quant_score') {
        aValue = a.quant_score ?? a.limited_quant_score ?? 0;
        bValue = b.quant_score ?? b.limited_quant_score ?? 0;
      } else if (sortField === 'roe') {
        aValue = a.roe ?? a.estimated_roe ?? 0;
        bValue = b.roe ?? b.estimated_roe ?? 0;
      }
      
      // Handle null/undefined values
      if (aValue === null || aValue === undefined) aValue = sortDirection === 'asc' ? Number.MAX_VALUE : -Number.MAX_VALUE;
      if (bValue === null || bValue === undefined) bValue = sortDirection === 'asc' ? Number.MAX_VALUE : -Number.MAX_VALUE;
      
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

  const runBacktest = async () => {
    if (!backtestSettings.symbol) {
      alert('종목을 선택해주세요.');
      return;
    }

    setLoading(true);
    
    try {
      // 실제 백테스트 API 호출
      const params = new URLSearchParams({
        symbol: backtestSettings.symbol,
        market: selectedMarket,
        start_date: backtestSettings.startDate,
        end_date: backtestSettings.endDate,
        investment_amount: backtestSettings.investmentAmount.toString(),
        strategy: backtestSettings.strategy
      });

      const response = await fetch(`${API_BASE}/v1/backtest/run?${params}`, {
        method: 'POST'
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '백테스트 실행 실패');
      }

      const data = await response.json();
      const apiResult = data.result;

      // API 응답을 프론트엔드 형식으로 변환
      const result: BacktestResult = {
        symbol: apiResult.symbol,
        companyName: apiResult.company_name,
        strategy: apiResult.strategy,
        period: apiResult.period,
        investmentAmount: apiResult.investment_amount,
        finalAmount: apiResult.final_amount,
        totalReturn: apiResult.total_return,
        totalReturnPercent: apiResult.total_return_percent,
        annualReturn: apiResult.annual_return,
        maxDrawdown: apiResult.max_drawdown,
        winRate: apiResult.win_rate,
        trades: apiResult.trades,
        bestTrade: apiResult.best_trade,
        worstTrade: apiResult.worst_trade,
        startDate: apiResult.start_date,
        endDate: apiResult.end_date,
        startPrice: apiResult.start_price,
        endPrice: apiResult.end_price
      };

      setBacktestResult(result);
    } catch (error) {
      console.error('Backtest error:', error);
      alert(error instanceof Error ? error.message : '백테스트 실행 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
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
            <SearchableSelect
              options={availableStocks.map(stock => ({
                value: stock.symbol,
                label: stock.name,
                subLabel: stock.symbol
              }))}
              value={backtestSettings.symbol}
              onChange={(value) => {
                setBacktestSettings(prev => ({ ...prev, symbol: value }));
                // 종목이 변경되면 이전 백테스트 결과 초기화
                setBacktestResult(null);
              }}
              placeholder="종목명 또는 코드로 검색..."
              loading={stocksLoading}
              disabled={stocksLoading}
            />
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

          <div className="date-input-group">
            <label className="form-label">시작 날짜</label>
            <div className="date-input-wrapper">
              <svg className="date-input-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
                <line x1="3" y1="10" x2="21" y2="10"></line>
              </svg>
              <input 
                className="form-input"
                type="date" 
                value={backtestSettings.startDate}
                max={new Date().toISOString().split('T')[0]}
                min="2020-01-01"
                onChange={(e) => setBacktestSettings(prev => ({ ...prev, startDate: e.target.value }))}
              />
            </div>
          </div>
          
          <div className="date-input-group">
            <label className="form-label">종료 날짜</label>
            <div className="date-input-wrapper">
              <svg className="date-input-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
                <line x1="3" y1="10" x2="21" y2="10"></line>
              </svg>
              <input 
                className="form-input"
                type="date" 
                value={backtestSettings.endDate}
                max={new Date().toISOString().split('T')[0]}
                min={backtestSettings.startDate || "2020-01-01"}
                onChange={(e) => setBacktestSettings(prev => ({ ...prev, endDate: e.target.value }))}
              />
            </div>
            <div className="date-range-indicator">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
              </svg>
              <span>
                {(() => {
                  const start = new Date(backtestSettings.startDate);
                  const end = new Date(backtestSettings.endDate);
                  const days = Math.floor((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
                  return `${days}일 동안의 백테스트`;
                })()}
              </span>
            </div>
            <div className="quick-date-buttons">
              <button 
                type="button"
                className="quick-date-btn"
                onClick={() => {
                  const end = new Date();
                  end.setDate(end.getDate() - 1);
                  const start = new Date(end);
                  start.setMonth(start.getMonth() - 1);
                  setBacktestSettings(prev => ({
                    ...prev,
                    startDate: start.toISOString().split('T')[0],
                    endDate: end.toISOString().split('T')[0]
                  }));
                }}
              >
                1개월
              </button>
              <button 
                type="button"
                className="quick-date-btn"
                onClick={() => {
                  const end = new Date();
                  end.setDate(end.getDate() - 1);
                  const start = new Date(end);
                  start.setMonth(start.getMonth() - 3);
                  setBacktestSettings(prev => ({
                    ...prev,
                    startDate: start.toISOString().split('T')[0],
                    endDate: end.toISOString().split('T')[0]
                  }));
                }}
              >
                3개월
              </button>
              <button 
                type="button"
                className="quick-date-btn"
                onClick={() => {
                  const end = new Date();
                  end.setDate(end.getDate() - 1);
                  const start = new Date(end);
                  start.setMonth(start.getMonth() - 6);
                  setBacktestSettings(prev => ({
                    ...prev,
                    startDate: start.toISOString().split('T')[0],
                    endDate: end.toISOString().split('T')[0]
                  }));
                }}
              >
                6개월
              </button>
              <button 
                type="button"
                className="quick-date-btn"
                onClick={() => {
                  const end = new Date();
                  end.setDate(end.getDate() - 1);
                  const start = new Date(end);
                  start.setFullYear(start.getFullYear() - 1);
                  setBacktestSettings(prev => ({
                    ...prev,
                    startDate: start.toISOString().split('T')[0],
                    endDate: end.toISOString().split('T')[0]
                  }));
                }}
              >
                1년
              </button>
              <button 
                type="button"
                className="quick-date-btn"
                onClick={() => {
                  const end = new Date();
                  end.setDate(end.getDate() - 1);
                  const start = new Date(end.getFullYear(), 0, 1); // 올해 1월 1일
                  setBacktestSettings(prev => ({
                    ...prev,
                    startDate: start.toISOString().split('T')[0],
                    endDate: end.toISOString().split('T')[0]
                  }));
                }}
              >
                YTD
              </button>
            </div>
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
        </div>

        <div className="backtest-actions">
          <button 
            className="btn btn-primary"
            onClick={() => runBacktest()}
            disabled={loading || !backtestSettings.symbol}
          >
            {loading ? (
              <>
                <div className="loading-spinner small"></div>
                <span>백테스트 실행 중...</span>
              </>
            ) : (
              <>
                <Target size={18} />
                <span>백테스트 실행</span>
              </>
            )}
          </button>
        </div>
      </div>

      {backtestResult && (
        <div className="backtest-result">
          <div className="result-header">
            <h4>
              <span 
                style={{ cursor: 'pointer', textDecoration: 'underline' }}
                onClick={() => {
                  setSelectedStock({ 
                    name: backtestResult.companyName, 
                    symbol: backtestResult.symbol, 
                    market: selectedMarket,
                    display: `${backtestResult.companyName} (${backtestResult.symbol})`
                  });
                  setCurrentView('stocks');
                }}
              >
                {backtestResult.companyName} ({backtestResult.symbol})
              </span> 백테스트 결과
            </h4>
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
            <div className="detail-row">
              <span>최고 수익 거래</span>
              <span className="positive">+{backtestResult.bestTrade.toFixed(1)}%</span>
            </div>
            <div className="detail-row">
              <span>최대 손실 거래</span>
              <span className="negative">{backtestResult.worstTrade.toFixed(1)}%</span>
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
              <th onClick={() => handleSort('roe')}>
                ROE(%) <SortIcon field="roe" />
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
              <th onClick={() => handleSort('quant_score')}>
                퀀트 점수 <SortIcon field="quant_score" />
              </th>
              <th>
                데이터 상태
              </th>
              <th>추천</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedData.length === 0 ? (
              <tr>
                <td colSpan={11} style={{ textAlign: 'center', padding: '40px' }}>
                  {quantDataLoading ? (
                    <div>데이터를 불러오는 중...</div>
                  ) : quantData[selectedMarket].length === 0 ? (
                    <div>
                      <p>퀀트 데이터가 없습니다.</p>
                      <p style={{ fontSize: '0.9em', color: '#666', marginTop: '10px' }}>
                        MongoDB에 데이터가 없을 수 있습니다. 데이터 수집이 필요합니다.
                      </p>
                    </div>
                  ) : (
                    <div>
                      <p>필터 조건에 맞는 종목이 없습니다.</p>
                      <p style={{ fontSize: '0.9em', color: '#666', marginTop: '10px' }}>
                        필터 조건을 완화해보세요.
                      </p>
                    </div>
                  )}
                </td>
              </tr>
            ) : (
              filteredAndSortedData.map((item) => (
              <tr key={item.symbol}>
                <td>
                  <div className="stock-info" 
                    style={{ cursor: 'pointer' }}
                    onClick={() => {
                      setSelectedStock({ 
                        name: item.name, 
                        symbol: item.symbol, 
                        market: selectedMarket,
                        display: `${item.name} (${item.symbol})`
                      });
                      setCurrentView('stocks');
                    }}
                  >
                    <span className="stock-name" style={{ textDecoration: 'underline' }}>{item.name}</span>
                    <span className="stock-symbol">({item.symbol})</span>
                  </div>
                </td>
                <td>{item.per?.toFixed(2) ?? '-'}</td>
                <td>{item.pbr?.toFixed(2) ?? '-'}</td>
                <td className={(item.roe ?? item.estimated_roe ?? 0) > 15 ? 'status-positive' : (item.roe ?? item.estimated_roe ?? 0) < 5 ? 'status-negative' : ''}>
                  {(item.roe ?? item.estimated_roe)?.toFixed(2) ?? '-'}
                </td>
                <td>{item.eps?.toLocaleString() ?? '-'}</td>
                <td>{item.current_price.toLocaleString()}</td>
                <td className={item.momentum_3m > 0 ? 'status-positive' : 'status-negative'}>
                  {item.momentum_3m > 0 ? '+' : ''}{item.momentum_3m.toFixed(1)}
                </td>
                <td className={item.volatility < 20 ? 'status-positive' : item.volatility > 30 ? 'status-negative' : ''}>
                  {item.volatility.toFixed(1)}
                </td>
                <td>
                  <div className="quant-score">
                    <span className={`score ${(item.quant_score ?? item.limited_quant_score ?? 0) > 70 ? 'high' : (item.quant_score ?? item.limited_quant_score ?? 0) > 40 ? 'medium' : 'low'}`}>
                      {(item.quant_score ?? item.limited_quant_score)?.toFixed(1) ?? '-'}
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
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderRecommendationsTab = () => (
    <div className="recommendations-section">
      <div className="section-header">
        <div className="section-header-content">
          <div className="section-info">
            <h3>AI 투자 추천</h3>
            <p>퀴트 지표 상위 종목을 AI가 심층 분석하여 투자 인사이트를 제공합니다</p>
          </div>
        </div>
      </div>

      {recommendationsLoading ? (
        <div className="loading">
          <div className="loading-spinner"></div>
          <div className="loading-text">AI가 종목을 분석하고 있습니다...</div>
          <div className="loading-subtext">퀴트 지표 상위 종목을 심층 분석 중입니다</div>
        </div>
      ) : recommendations.length === 0 ? (
        <div className="empty-state">
          <p>AI 추천 종목이 없습니다.</p>
          <p className="empty-state-sub">잠시 후 다시 시도해주세요.</p>
        </div>
      ) : (
        <div className="recommendations-grid">
          {recommendations.map((rec, idx) => {
            const timeHorizonText = rec.timeHorizon === 'SHORT' ? '1-3개월' : 
                                   rec.timeHorizon === 'MEDIUM' ? '3-6개월' : '6개월 이상';
            
            return (
              <div key={rec.symbol} className="recommendation-card">
                <div className="rec-header">
                  <div className="rec-rank">#{idx + 1}</div>
                  <div className="rec-risk-badge" data-risk={rec.riskLevel.toLowerCase()}>
                    {rec.riskLevel === 'LOW' ? '안전' : rec.riskLevel === 'MEDIUM' ? '보통' : '위험'}
                  </div>
                </div>
                
                <div className="rec-company" 
                  style={{ cursor: 'pointer' }}
                  onClick={() => {
                    setSelectedStock({ 
                      name: rec.name, 
                      symbol: rec.symbol, 
                      market: selectedMarket,
                      display: `${rec.name} (${rec.symbol})`
                    });
                    setCurrentView('stocks');
                  }}
                >
                  <h4 style={{ textDecoration: 'underline' }}>{rec.name}</h4>
                  <span className="rec-symbol">({rec.symbol})</span>
                </div>

                <div className="rec-prices">
                  <div className="price-row">
                    <span>현재가</span>
                    <span className="current-price">{formatCurrency(rec.currentPrice)}</span>
                  </div>
                  <div className="price-row">
                    <span>예상가 ({timeHorizonText})</span>
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

                {rec.keyIndicators && (
                  <div className="rec-indicators">
                    <h5>핵심 지표</h5>
                    <div className="indicators-grid">
                      {rec.keyIndicators.PER && <span>PER: {rec.keyIndicators.PER}</span>}
                      {rec.keyIndicators.PBR && <span>PBR: {rec.keyIndicators.PBR}</span>}
                      {rec.keyIndicators.ROE && <span>ROE: {rec.keyIndicators.ROE}%</span>}
                      {rec.keyIndicators.quantScore && <span>퀴트: {rec.keyIndicators.quantScore}점</span>}
                    </div>
                  </div>
                )}

                <div className="rec-reasoning">
                  <h5>추천 이유</h5>
                  <ul>
                    {rec.reasoning.map((reason, reasonIdx) => (
                      <li key={reasonIdx}>{reason}</li>
                    ))}
                  </ul>
                </div>

                {rec.warnings && rec.warnings.length > 0 && (
                  <div className="rec-warnings">
                    <h5>주의사항</h5>
                    <ul>
                      {rec.warnings.map((warning, warningIdx) => (
                        <li key={warningIdx}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                )}

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
            );
          })}
        </div>
      )}
    </div>
  );

  return (
    <div className="quant-view">

      <div className="quant-tabs">
        <div className="tabs-container">
          <div className="tab-selector">
            <button
              className={`tab-btn ${activeTab === 'indicators' ? 'active' : ''}`}
              onClick={() => setActiveTab('indicators')}
              title="퀀트 지표 분석"
            >
              <Activity size={20} />
              <span>
                <div className="tab-title">퀀트 지표</div>
                <div className="tab-subtitle">정량적 분석</div>
              </span>
            </button>
            <button
              className={`tab-btn ${activeTab === 'backtest' ? 'active' : ''}`}
              onClick={() => setActiveTab('backtest')}
              title="백테스트 시뮬레이션"
            >
              <BarChart3 size={20} />
              <span>
                <div className="tab-title">백테스트</div>
                <div className="tab-subtitle">전략 검증</div>
              </span>
            </button>
            <button
              className={`tab-btn ${activeTab === 'recommendations' ? 'active' : ''}`}
              onClick={() => setActiveTab('recommendations')}
              title="AI 추천 종목"
            >
              <TrendingUp size={20} />
              <span>
                <div className="tab-title">AI 추천</div>
                <div className="tab-subtitle">예측 분석</div>
              </span>
            </button>
          </div>
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