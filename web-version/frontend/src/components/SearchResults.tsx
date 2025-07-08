import React, { useState, useEffect, useMemo } from 'react';
import { useApp } from '../context/AppContext';
import { stockSearchService, StockSearchItem } from '../services/stockSearchService';
import './SearchResults.css';

interface SearchResult extends StockSearchItem {
  display: string;
}

interface SearchResultsProps {
  query: string;
  onClose: () => void;
}

const SearchResults: React.FC<SearchResultsProps> = ({ query, onClose }) => {
  const { setSelectedStock, setCurrentView } = useApp();
  const [allStocks, setAllStocks] = useState<StockSearchItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load all stocks on mount
  useEffect(() => {
    const loadStocks = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await stockSearchService.getAllStocks();
        setAllStocks(data.stocks);
      } catch (err) {
        console.error('Error loading stocks:', err);
        setError('Failed to load stock list');
      } finally {
        setLoading(false);
      }
    };

    loadStocks();
  }, []);

  // Filter stocks based on query
  const filteredResults = useMemo(() => {
    if (!query.trim()) return [];
    
    const searchResults = stockSearchService.searchStocks(allStocks, query);
    
    // Add display property
    return searchResults.map(stock => ({
      ...stock,
      display: stockSearchService.formatStockDisplay(stock)
    }));
  }, [allStocks, query]);

  const totalCount = filteredResults.length;

  const handleStockSelect = (stock: SearchResult) => {
    setSelectedStock({
      ...stock,
      market: stock.market
    });
    setCurrentView('stocks');
    onClose();
  };

  if (query.trim().length === 0) {
    return null;
  }

  return (
    <div className="search-results-overlay" onClick={onClose}>
      <div className="search-results-panel" onClick={(e) => e.stopPropagation()}>
        <div className="search-results-header">
          <h3>검색 결과</h3>
          <span className="search-query">"{query}"</span>
          <button className="close-button" onClick={onClose}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div className="search-results-content">
          {loading && allStocks.length === 0 ? (
            <div className="search-loading">
              <div className="loading-spinner"></div>
              <p>주식 목록 로딩 중...</p>
            </div>
          ) : error ? (
            <div className="search-empty">
              <div className="empty-icon">⚠️</div>
              <p>오류가 발생했습니다</p>
              <span>{error}</span>
            </div>
          ) : filteredResults.length === 0 ? (
            <div className="search-empty">
              <div className="empty-icon">🔍</div>
              <p>검색 결과가 없습니다</p>
              <span>다른 검색어를 시도해보세요</span>
            </div>
          ) : (
            <>
              <div className="search-results-info">
                <span>총 {totalCount}개 결과</span>
              </div>
              
              <div className="search-results-list">
                {filteredResults.slice(0, 50).map((result, index) => (
                  <div 
                    key={`${result.symbol}-${result.market}-${index}`}
                    className="search-result-item"
                    onClick={() => handleStockSelect(result)}
                  >
                    <div className="result-info">
                      <div className="result-name">{result.name}</div>
                      <div className="result-symbol">{result.symbol}</div>
                    </div>
                    <div className="result-market">
                      <span className={`market-badge ${result.market.toLowerCase()}`}>
                        {result.market === 'KR' ? '🇰🇷 한국' : '🇺🇸 미국'}
                      </span>
                    </div>
                  </div>
                ))}
              </div>

              {totalCount > 50 && (
                <div className="search-results-info">
                  <span>상위 50개 결과만 표시됩니다</span>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default SearchResults;