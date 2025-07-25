import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { useAuth } from '../context/AuthContext';
import { watchlistService } from '../services/watchlistService';
import Pagination from './Pagination';
import './StockList.css';

interface Stock {
  name: string;
  symbol: string;
  display: string;
  market?: 'KR' | 'US';
  price?: number;
  change?: number;
  change_percent?: number;
  volume?: number | string;
  data_date?: string;
}

interface StockListProps {
  stocks: Stock[];
  selectedMarket: 'KR' | 'US';
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
  currentPage?: number;
  totalPages?: number;
  totalCount?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
}

const StockList: React.FC<StockListProps> = ({ 
  stocks, 
  selectedMarket, 
  loading, 
  error, 
  onRefresh,
  currentPage = 1,
  totalPages = 1,
  totalCount = 0,
  pageSize = 20,
  onPageChange
}) => {
  const { searchTerm, setCurrentView, setSelectedStock } = useApp();
  const { user } = useAuth();
  const [localSearchTerm, setLocalSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<'name' | 'symbol'>('name');
  const [lastUpdateTime, setLastUpdateTime] = useState<string>(new Date().toLocaleString('ko-KR'));
  const [watchlist, setWatchlist] = useState<Set<string>>(new Set());
  const [watchlistLoading, setWatchlistLoading] = useState<Set<string>>(new Set());

  // Helper function to format volume
  const formatVolume = (volume: number | string): string => {
    if (typeof volume === 'string') return volume;
    if (volume >= 1000000) return `${(volume / 1000000).toFixed(1)}M`;
    if (volume >= 1000) return `${(volume / 1000).toFixed(1)}K`;
    return volume.toString();
  };

  // Sync local search with global search
  useEffect(() => {
    setLocalSearchTerm(searchTerm);
  }, [searchTerm]);

  // Update timestamp when stocks change
  useEffect(() => {
    if (stocks.length > 0) {
      // Use data_date from the first stock if available
      const dataDate = stocks[0]?.data_date;
      if (dataDate) {
        const date = new Date(dataDate);
        setLastUpdateTime(`${dataDate} (${date.toLocaleDateString('ko-KR', { weekday: 'long' })})`);
      } else {
        setLastUpdateTime(new Date().toLocaleString('ko-KR'));
      }
    }
  }, [stocks]);

  // Load user's watchlist
  useEffect(() => {
    if (user) {
      loadWatchlist();
    } else {
      setWatchlist(new Set());
    }
  }, [user]);

  const loadWatchlist = async () => {
    try {
      const items = await watchlistService.getAll();
      const watchlistSet = new Set(items.map(item => `${item.stock_symbol}-${item.market}`));
      setWatchlist(watchlistSet);
    } catch (error) {
      console.error('Failed to load watchlist:', error);
    }
  };

  const toggleWatchlist = async (stock: Stock) => {
    if (!user) {
      setCurrentView('login');
      return;
    }

    const key = `${stock.symbol}-${selectedMarket}`;
    setWatchlistLoading(prev => new Set(prev).add(key));

    try {
      if (watchlist.has(key)) {
        await watchlistService.remove(stock.symbol, selectedMarket);
        setWatchlist(prev => {
          const newSet = new Set(prev);
          newSet.delete(key);
          return newSet;
        });
      } else {
        await watchlistService.add(stock.symbol, selectedMarket);
        setWatchlist(prev => new Set(prev).add(key));
      }
    } catch (error) {
      console.error('Failed to update watchlist:', error);
    } finally {
      setWatchlistLoading(prev => {
        const newSet = new Set(prev);
        newSet.delete(key);
        return newSet;
      });
    }
  };

  const effectiveSearchTerm = localSearchTerm || searchTerm;
  
  const filteredStocks = stocks.filter(stock =>
    stock.name.toLowerCase().includes(effectiveSearchTerm.toLowerCase()) ||
    stock.symbol.toLowerCase().includes(effectiveSearchTerm.toLowerCase())
  );

  const sortedStocks = [...filteredStocks].sort((a, b) => {
    if (sortBy === 'name') {
      return a.name.localeCompare(b.name);
    }
    return a.symbol.localeCompare(b.symbol);
  });

  const getStockData = (stock: Stock) => {
    return {
      price: stock.price || 0,
      change: stock.change || 0,
      change_percent: stock.change_percent || 0,
      volume: stock.volume || 0
    };
  };

  const handleStockAnalysis = (stock: Stock) => {
    setSelectedStock({ ...stock, market: selectedMarket });
    setCurrentView('stocks');
  };

  const handleStockNews = (stock: Stock) => {
    setSelectedStock({ ...stock, market: selectedMarket });
    setCurrentView('news');
  };

  if (loading) {
    return (
      <div className="stock-list-container">
        <div className="stock-list-header">
          <h3>주식 목록</h3>
        </div>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>주식 데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="stock-list-container">
        <div className="stock-list-header">
          <h3>주식 목록</h3>
        </div>
        <div className="error-container">
          <div className="error-icon">⚠️</div>
          <p>{error}</p>
          <button className="btn-primary" onClick={onRefresh}>
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="stock-list-container slide-up">
      <div className="stock-list-header">
        <div className="header-title-group">
          <h3>
            {selectedMarket === 'KR' ? '🇰🇷 한국 주식' : '🇺🇸 미국 주식'} 
            <span className="stock-count">({stocks.length})</span>
          </h3>
          <span className="update-time">데이터 기준: {lastUpdateTime}</span>
        </div>
        
        <div className="header-controls">
          <div className="search-container-small">
            <svg className="search-icon-small" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8"></circle>
              <path d="m21 21-4.35-4.35"></path>
            </svg>
            <input
              type="text"
              placeholder="주식 검색..."
              value={localSearchTerm}
              onChange={(e) => setLocalSearchTerm(e.target.value)}
              className="search-input-small"
            />
          </div>
          
          <select 
            value={sortBy} 
            onChange={(e) => setSortBy(e.target.value as 'name' | 'symbol')}
            className="sort-select"
          >
            <option value="name">이름순</option>
            <option value="symbol">심볼순</option>
          </select>
        </div>
      </div>

      <div className="stock-grid">
        {sortedStocks.map((stock, index) => {
          const stockData = getStockData(stock);
          const isPositive = stockData.change_percent > 0;
          const isNegative = stockData.change_percent < 0;
          
          return (
            <div 
              key={stock.symbol} 
              className="stock-card"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className="stock-header">
                <div className="stock-info">
                  <h4 className="stock-name">{stock.name}</h4>
                  <span className="stock-symbol">{stock.symbol}</span>
                </div>
                <button 
                  className={`favorite-btn ${watchlist.has(`${stock.symbol}-${selectedMarket}`) ? 'active' : ''}`} 
                  aria-label={watchlist.has(`${stock.symbol}-${selectedMarket}`) ? 'Remove from watchlist' : 'Add to watchlist'}
                  onClick={() => toggleWatchlist(stock)}
                  disabled={watchlistLoading.has(`${stock.symbol}-${selectedMarket}`)}
                >
                  {watchlistLoading.has(`${stock.symbol}-${selectedMarket}`) ? (
                    <div className="loading-spinner-small"></div>
                  ) : (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill={watchlist.has(`${stock.symbol}-${selectedMarket}`) ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2">
                      <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"></polygon>
                    </svg>
                  )}
                </button>
              </div>

              <div className="stock-metrics">
                <div className="metric">
                  <span className="metric-label">현재가</span>
                  <span className="metric-value">
                    {stockData.price > 0 ? (
                      selectedMarket === 'KR' 
                        ? `₩${stockData.price.toLocaleString()}` 
                        : `$${stockData.price.toFixed(2)}`
                    ) : (
                      '로딩중...'
                    )}
                  </span>
                </div>

                <div className="metric">
                  <span className="metric-label">등락율</span>
                  <span className={`metric-value ${
                    isPositive ? 'status-positive' : 
                    isNegative ? 'status-negative' : 'status-neutral'
                  }`}>
                    {stockData.change_percent !== 0 ? (
                      `${isPositive ? '+' : ''}${stockData.change_percent.toFixed(2)}%`
                    ) : (
                      '0.00%'
                    )}
                  </span>
                </div>

                <div className="metric">
                  <span className="metric-label">거래량</span>
                  <span className="metric-value">
                    {stockData.volume ? formatVolume(stockData.volume) : '0'}
                  </span>
                </div>
              </div>

              <div className="stock-actions">
                <button 
                  className="btn-primary stock-btn"
                  onClick={() => handleStockAnalysis(stock)}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="12" y1="5" x2="12" y2="19"></line>
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                  </svg>
                  분석
                </button>
                <button 
                  className="btn-secondary stock-btn"
                  onClick={() => handleStockNews(stock)}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M2 3h20v14a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V3z"></path>
                    <path d="M2 3h20v5H2z"></path>
                    <path d="M12 12h8"></path>
                    <path d="M12 16h8"></path>
                    <path d="M6 12h2"></path>
                    <path d="M6 16h2"></path>
                  </svg>
                  뉴스보기
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {sortedStocks.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">🔍</div>
          <p>검색 결과가 없습니다.</p>
          <span>다른 검색어를 시도해보세요.</span>
        </div>
      )}
      
      {/* Pagination */}
      {onPageChange && totalPages > 1 && (
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          totalCount={totalCount}
          pageSize={pageSize}
          onPageChange={onPageChange}
        />
      )}
    </div>
  );
};

export default StockList;