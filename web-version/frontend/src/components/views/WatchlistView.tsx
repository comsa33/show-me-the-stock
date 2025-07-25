import React, { useState, useEffect, useCallback } from 'react';
import { useApp } from '../../context/AppContext';
import { useAuth } from '../../context/AuthContext';
import { watchlistService, WatchlistItem } from '../../services/watchlistService';
import { API_BASE } from '../../config';
import './WatchlistView.css';

interface WatchlistViewProps {
  selectedMarket: 'KR' | 'US';
}

interface StockData {
  symbol: string;
  name: string;
  price: number;
  change: number;
  change_percent: number;
  volume: number;
  market: 'KR' | 'US';
}

const WatchlistView: React.FC<WatchlistViewProps> = ({ selectedMarket }) => {
  const { setCurrentView, setSelectedStock } = useApp();
  const { user } = useAuth();
  const [watchlist, setWatchlist] = useState<WatchlistItem[]>([]);
  const [stockData, setStockData] = useState<Map<string, StockData>>(new Map());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [removingItems, setRemovingItems] = useState<Set<string>>(new Set());

  const loadStockDataForItems = useCallback(async (items: WatchlistItem[]) => {
    if (items.length === 0) return;
    
    try {
      const stockMap = new Map<string, StockData>();
      
      // First, try to get data from prices API for better performance
      const response = await fetch(`${API_BASE}/v1/stocks/prices/${selectedMarket}?page=1&limit=100`);
      if (response.ok) {
        const data = await response.json();
        
        // Map stock data for watchlist items
        data.stocks.forEach((stock: any) => {
          if (items.some(item => item.stock_symbol === stock.symbol)) {
            stockMap.set(stock.symbol, {
              symbol: stock.symbol,
              name: stock.name,
              price: stock.price || 0,
              change: stock.change || 0,
              change_percent: stock.change_percent || 0,
              volume: stock.volume || 0,
              market: selectedMarket
            });
          }
        });
      }
      
      // For any missing stocks, use search API to get their info
      const missingItems = items.filter(item => !stockMap.has(item.stock_symbol));
      
      for (const item of missingItems) {
        try {
          // First, get the stock name using search API
          const searchResponse = await fetch(`${API_BASE}/v1/stocks/search?query=${item.stock_symbol}&market=${selectedMarket}`);
          if (searchResponse.ok) {
            const searchData = await searchResponse.json();
            if (searchData.results && searchData.results.length > 0) {
              const stockInfo = searchData.results[0];
              
              // Get detailed stock info including price
              let priceData = {
                price: 0,
                change: 0,
                change_percent: 0,
                volume: 0
              };
              
              try {
                const detailResponse = await fetch(`${API_BASE}/v1/stocks/v2/detail/${item.stock_symbol}?market=${selectedMarket}`);
                if (detailResponse.ok) {
                  const detailData = await detailResponse.json();
                  if (detailData.basic_info) {
                    priceData = {
                      price: detailData.basic_info.current_price || 0,
                      change: detailData.basic_info.change || 0,
                      change_percent: detailData.basic_info.change_percent || 0,
                      volume: detailData.trading_info?.current_volume || 0
                    };
                  }
                }
              } catch (detailErr) {
                console.error(`Failed to fetch detail for ${item.stock_symbol}:`, detailErr);
              }
              
              stockMap.set(item.stock_symbol, {
                symbol: item.stock_symbol,
                name: stockInfo.name,
                price: priceData.price,
                change: priceData.change,
                change_percent: priceData.change_percent,
                volume: priceData.volume,
                market: selectedMarket
              });
            }
          }
        } catch (err) {
          console.error(`Failed to fetch data for ${item.stock_symbol}:`, err);
          // Add basic info even if API calls fail
          stockMap.set(item.stock_symbol, {
            symbol: item.stock_symbol,
            name: item.stock_symbol, // Use symbol as fallback name
            price: 0,
            change: 0,
            change_percent: 0,
            volume: 0,
            market: selectedMarket
          });
        }
      }
      
      setStockData(stockMap);
    } catch (error) {
      console.error('Failed to fetch stock data:', error);
    }
  }, [selectedMarket]);

  useEffect(() => {
    const loadData = async () => {
      if (user) {
        try {
          setLoading(true);
          const items = await watchlistService.getAll();
          const filteredItems = items.filter(item => item.market === selectedMarket);
          setWatchlist(filteredItems);
          
          // Load stock data immediately after setting watchlist
          if (filteredItems.length > 0) {
            await loadStockDataForItems(filteredItems);
          }
        } catch (error) {
          console.error('Failed to load watchlist:', error);
          setError('관심종목을 불러오는데 실패했습니다.');
        } finally {
          setLoading(false);
        }
      } else {
        setCurrentView('login');
      }
    };
    
    loadData();
  }, [user, setCurrentView, selectedMarket, loadStockDataForItems]);


  const loadWatchlist = async () => {
    try {
      setLoading(true);
      const items = await watchlistService.getAll();
      const filteredItems = items.filter(item => item.market === selectedMarket);
      setWatchlist(filteredItems);
      
      // Load stock data immediately after setting watchlist
      if (filteredItems.length > 0) {
        await loadStockDataForItems(filteredItems);
      }
    } catch (error) {
      console.error('Failed to load watchlist:', error);
      setError('관심종목을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const removeFromWatchlist = async (item: WatchlistItem) => {
    const key = `${item.stock_symbol}-${item.market}`;
    setRemovingItems(prev => new Set(prev).add(key));

    try {
      await watchlistService.remove(item.stock_symbol, item.market);
      setWatchlist(prev => prev.filter(w => w.id !== item.id));
    } catch (error) {
      console.error('Failed to remove from watchlist:', error);
    } finally {
      setRemovingItems(prev => {
        const newSet = new Set(prev);
        newSet.delete(key);
        return newSet;
      });
    }
  };

  const handleStockClick = (stock: StockData) => {
    setSelectedStock({
      name: stock.name,
      symbol: stock.symbol,
      display: stock.name,
      market: stock.market
    });
    setCurrentView('stocks');
  };

  const formatPrice = (price: number) => {
    if (selectedMarket === 'KR') {
      return `₩${price.toLocaleString()}`;
    }
    return `$${price.toFixed(2)}`;
  };

  const formatVolume = (volume: number): string => {
    if (volume >= 1000000) return `${(volume / 1000000).toFixed(1)}M`;
    if (volume >= 1000) return `${(volume / 1000).toFixed(1)}K`;
    return volume.toString();
  };

  if (!user) {
    return null;
  }

  if (loading) {
    return (
      <div className="watchlist-view">
        <div className="watchlist-header">
          <div className="header-title">
            <h2>관심종목</h2>
            <p>즐겨찾기한 종목들을 관리하고 모니터링하세요</p>
          </div>
        </div>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>관심종목을 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="watchlist-view">
        <div className="watchlist-header">
          <div className="header-title">
            <h2>관심종목</h2>
            <p>즐겨찾기한 종목들을 관리하고 모니터링하세요</p>
          </div>
        </div>
        <div className="error-container">
          <div className="error-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
              <line x1="12" y1="9" x2="12" y2="13"></line>
              <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
          </div>
          <p>{error}</p>
          <button className="btn-primary" onClick={loadWatchlist}>
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  if (watchlist.length === 0) {
    return (
      <div className="watchlist-view">
        <div className="watchlist-header">
          <div className="header-title">
            <h2>관심종목</h2>
            <p>즐겨찾기한 종목들을 관리하고 모니터링하세요</p>
          </div>
        </div>
        
        <div className="watchlist-content">
          <div className="empty-state">
            <div className="empty-icon">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polygon points="12,2 15.09,8.26 22,9.27 17,14.14 18.18,21.02 12,17.77 5.82,21.02 7,14.14 2,9.27 8.91,8.26"></polygon>
              </svg>
            </div>
            <h3>관심종목이 없습니다</h3>
            <p>주식 목록에서 별표 버튼을 눌러 관심종목을 추가하세요</p>
            <button className="btn-primary" onClick={() => setCurrentView('dashboard')}>
              주식 목록 보기
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="watchlist-view">
      <div className="watchlist-header">
        <div className="header-title">
          <h2>관심종목</h2>
          <p>
            {selectedMarket === 'KR' ? '🇰🇷 한국 주식' : '🇺🇸 미국 주식'} 
            <span className="watchlist-count">({watchlist.length})</span>
          </p>
        </div>
        <button className="refresh-btn" onClick={loadWatchlist} title="새로고침">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M1 4v6h6"></path>
            <path d="M23 20v-6h-6"></path>
            <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
          </svg>
        </button>
      </div>
      
      <div className="watchlist-content">
        <div className="watchlist-grid">
          {watchlist.map((item) => {
            const stock = stockData.get(item.stock_symbol);
            const isRemoving = removingItems.has(`${item.stock_symbol}-${item.market}`);
            
            return (
              <div key={item.id} className="watchlist-card">
                <div className="watchlist-card-header">
                  <div className="stock-info" onClick={() => {
                    if (stock) {
                      handleStockClick(stock);
                    } else {
                      setSelectedStock({
                        name: item.stock_symbol,
                        symbol: item.stock_symbol,
                        display: item.stock_symbol,
                        market: item.market
                      });
                      setCurrentView('stocks');
                    }
                  }}>
                    <h4>{stock?.name || item.stock_symbol}</h4>
                    <span className="stock-symbol">{item.stock_symbol}</span>
                  </div>
                  <button
                    className="remove-btn"
                    onClick={() => removeFromWatchlist(item)}
                    disabled={isRemoving}
                    title="관심종목에서 제거"
                  >
                    {isRemoving ? (
                      <div className="loading-spinner-small"></div>
                    ) : (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                      </svg>
                    )}
                  </button>
                </div>
                
                {stock && (
                  <div className="watchlist-card-body">
                    <div className="price-info">
                      <span className="current-price">{formatPrice(stock.price)}</span>
                      <span className={`price-change ${
                        stock.change_percent > 0 ? 'positive' : 
                        stock.change_percent < 0 ? 'negative' : 'neutral'
                      }`}>
                        {stock.change_percent > 0 ? '+' : ''}{stock.change_percent.toFixed(2)}%
                      </span>
                    </div>
                    <div className="volume-info">
                      <span className="label">거래량</span>
                      <span className="value">{formatVolume(stock.volume)}</span>
                    </div>
                  </div>
                )}
                
                <div className="watchlist-card-actions">
                  <button 
                    className="btn-primary"
                    onClick={() => {
                      if (stock) {
                        handleStockClick(stock);
                      } else {
                        // If stock data is not loaded yet, use the basic info from watchlist
                        setSelectedStock({
                          name: item.stock_symbol,
                          symbol: item.stock_symbol,
                          display: item.stock_symbol,
                          market: item.market
                        });
                        setCurrentView('stocks');
                      }
                    }}
                  >
                    분석
                  </button>
                  <button 
                    className="btn-secondary"
                    onClick={() => {
                      if (stock) {
                        setSelectedStock({
                          name: stock.name,
                          symbol: stock.symbol,
                          display: stock.name,
                          market: stock.market
                        });
                      } else {
                        // If stock data is not loaded yet, use the basic info from watchlist
                        setSelectedStock({
                          name: item.stock_symbol,
                          symbol: item.stock_symbol,
                          display: item.stock_symbol,
                          market: item.market
                        });
                      }
                      setCurrentView('news');
                    }}
                  >
                    뉴스
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default WatchlistView;