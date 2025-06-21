import React, { useState, useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { API_BASE } from '../config';
import './SearchResults.css';

interface SearchResult {
  name: string;
  symbol: string;
  display: string;
  market: 'KR' | 'US';
}

interface SearchResultsProps {
  query: string;
  onClose: () => void;
}

const SearchResults: React.FC<SearchResultsProps> = ({ query, onClose }) => {
  const { setSelectedStock, setCurrentView } = useApp();
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);

  useEffect(() => {
    if (query.trim().length > 0) {
      searchStocks(query, 1);
    } else {
      setResults([]);
      setTotalCount(0);
    }
  }, [query]);

  const searchStocks = async (searchQuery: string, pageNum: number = 1) => {
    if (searchQuery.trim().length === 0) return;

    setLoading(true);
    try {
      const response = await fetch(
        `${API_BASE}/v1/stocks/search?query=${encodeURIComponent(searchQuery)}&market=ALL&page=${pageNum}&limit=20`
      );
      const data = await response.json();

      if (pageNum === 1) {
        setResults(data.results || []);
      } else {
        setResults(prev => [...prev, ...(data.results || [])]);
      }
      
      setTotalCount(data.total_count || 0);
      setPage(pageNum);
      setHasMore(pageNum < (data.total_pages || 1));
    } catch (error) {
      console.error('검색 중 오류 발생:', error);
      setResults([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  };

  const loadMore = () => {
    if (!loading && hasMore) {
      searchStocks(query, page + 1);
    }
  };

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
          {loading && results.length === 0 ? (
            <div className="search-loading">
              <div className="loading-spinner"></div>
              <p>검색 중...</p>
            </div>
          ) : results.length === 0 ? (
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
                {results.map((result, index) => (
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

              {hasMore && (
                <div className="search-load-more">
                  <button 
                    className="load-more-btn"
                    onClick={loadMore}
                    disabled={loading}
                  >
                    {loading ? '로딩 중...' : '더 보기'}
                  </button>
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