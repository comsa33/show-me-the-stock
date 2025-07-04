import React, { useState, useEffect, useCallback } from 'react';
import { useApp } from '../../context/AppContext';
import { API_BASE } from '../../config';
import { Newspaper, RefreshCw, Calendar, ExternalLink, Search } from 'lucide-react';
import './NewsView.css';

interface NewsViewProps {
  selectedMarket: 'KR' | 'US';
}

interface NewsItem {
  title: string;
  originallink: string;
  link: string;
  description: string;
  pubDate: string;
}

interface NewsResponse {
  lastBuildDate: string;
  total: number;
  start: number;
  display: number;
  items: NewsItem[];
}

interface CachedNews {
  data: NewsResponse;
  timestamp: number;
  query: string;
}

const NewsView: React.FC<NewsViewProps> = ({ selectedMarket }) => {
  const { selectedStock } = useApp();
  const [newsData, setNewsData] = useState<NewsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [displayCount, setDisplayCount] = useState<number>(10);
  const [popularStocks] = useState([
    // 한국 주식
    { symbol: '005930', name: '삼성전자', market: 'KR' },
    { symbol: '000660', name: 'SK하이닉스', market: 'KR' },
    { symbol: '035420', name: 'NAVER', market: 'KR' },
    { symbol: '035720', name: '카카오', market: 'KR' },
    { symbol: '051910', name: 'LG화학', market: 'KR' },
    { symbol: '005380', name: '현대차', market: 'KR' },
    { symbol: '207940', name: '삼성바이오로직스', market: 'KR' },
    { symbol: '068270', name: '셀트리온', market: 'KR' },
    // 미국 주식
    { symbol: 'AAPL', name: 'Apple', market: 'US' },
    { symbol: 'MSFT', name: 'Microsoft', market: 'US' },
    { symbol: 'GOOGL', name: 'Alphabet', market: 'US' },
    { symbol: 'AMZN', name: 'Amazon', market: 'US' },
    { symbol: 'TSLA', name: 'Tesla', market: 'US' },
    { symbol: 'META', name: 'Meta', market: 'US' },
    { symbol: 'NVDA', name: 'NVIDIA', market: 'US' },
    { symbol: 'NFLX', name: 'Netflix', market: 'US' }
  ]);

  // 캐시 관련
  const CACHE_DURATION = 5 * 60 * 1000; // 5분
  const [newsCache, setNewsCache] = useState<Map<string, CachedNews>>(new Map());

  // 선택된 주식이 있으면 해당 주식으로 설정
  useEffect(() => {
    if (selectedStock) {
      setSelectedSymbol(selectedStock.symbol);
    }
  }, [selectedStock]);

  // 뉴스 가져오기
  const fetchNews = useCallback(async (forceRefresh: boolean = false) => {
    if (!selectedSymbol) return;

    const cacheKey = `${selectedSymbol}-${displayCount}`;
    const cached = newsCache.get(cacheKey);

    // 캐시 확인
    if (!forceRefresh && cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      setNewsData(cached.data);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const stock = popularStocks.find(s => s.symbol === selectedSymbol);
      const query = stock ? encodeURIComponent(stock.name) : encodeURIComponent(selectedSymbol);
      
      const response = await fetch(`${API_BASE}/v1/news/search?query=${query}&display=${displayCount}&sort=sim`);

      if (!response.ok) {
        throw new Error('뉴스를 불러오는데 실패했습니다.');
      }

      const data: NewsResponse = await response.json();
      
      // 캐시에 저장
      const newCache = new Map(newsCache);
      newCache.set(cacheKey, {
        data,
        timestamp: Date.now(),
        query: selectedSymbol
      });
      setNewsCache(newCache);
      setNewsData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  }, [selectedSymbol, displayCount, newsCache, popularStocks, CACHE_DURATION]);

  // 심볼 변경 시 뉴스 자동 로드
  useEffect(() => {
    if (selectedSymbol) {
      fetchNews();
    }
  }, [selectedSymbol, displayCount, fetchNews]);

  // 날짜 포맷팅
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    
    if (hours < 1) {
      const minutes = Math.floor(diff / (1000 * 60));
      return `${minutes}분 전`;
    } else if (hours < 24) {
      return `${hours}시간 전`;
    } else {
      const days = Math.floor(hours / 24);
      return `${days}일 전`;
    }
  };

  // HTML 태그 제거
  const stripHtml = (html: string) => {
    const tmp = document.createElement('div');
    tmp.innerHTML = html;
    return tmp.textContent || tmp.innerText || '';
  };

  return (
    <div className="news-view">
      {/* 헤더 영역 - 스크롤 영역에서 제외 */}
      <div className="news-header">
        <div className="news-header-inner">
          <div className="header-title-section">
            <div className="header-icon">
              <Newspaper />
            </div>
            <div className="header-text">
              <h2>실시간 뉴스</h2>
              <p>주식 관련 최신 뉴스를 확인하세요</p>
            </div>
          </div>
          
          <div className="header-controls">
            <select 
              className="stock-selector"
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
            >
              <option value="">종목 선택</option>
              <optgroup label="한국 주식">
                {popularStocks.filter(s => s.market === 'KR').map(stock => (
                  <option key={stock.symbol} value={stock.symbol}>
                    {stock.name} ({stock.symbol})
                  </option>
                ))}
              </optgroup>
              <optgroup label="미국 주식">
                {popularStocks.filter(s => s.market === 'US').map(stock => (
                  <option key={stock.symbol} value={stock.symbol}>
                    {stock.name} ({stock.symbol})
                  </option>
                ))}
              </optgroup>
            </select>

            <select 
              className="count-selector"
              value={displayCount}
              onChange={(e) => setDisplayCount(Number(e.target.value))}
            >
              <option value={10}>10개</option>
              <option value={20}>20개</option>
              <option value={30}>30개</option>
              <option value={50}>50개</option>
            </select>

            <button 
              className="refresh-button"
              onClick={() => fetchNews(true)}
              disabled={loading || !selectedSymbol}
              title="새로고침"
            >
              <RefreshCw className={loading ? 'spinning' : ''} />
              <span>새로고침</span>
            </button>
          </div>
        </div>
      </div>

      {/* 메인 콘텐츠 영역 - 스크롤 가능 */}
      <div className="news-body">
        <div className="news-content">
          {!selectedSymbol && (
            <div className="empty-state">
              <Search />
              <h3>종목을 선택하세요</h3>
              <p>뉴스를 확인하고 싶은 종목을 선택해주세요</p>
            </div>
          )}

          {loading && (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>뉴스를 불러오는 중...</p>
            </div>
          )}

          {error && (
            <div className="error-state">
              <p>{error}</p>
              <button onClick={() => fetchNews(true)}>다시 시도</button>
            </div>
          )}

          {newsData && !loading && (
            <>
              {/* 뉴스 통계 - sticky 헤더 */}
              <div className="news-stats">
                <div className="news-stats-inner">
                  <div className="stat-item">
                    <span className="stat-label">총 검색결과</span>
                    <span className="stat-value">{newsData.total.toLocaleString()}건</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">표시 중</span>
                    <span className="stat-value">{newsData.items.length}건</span>
                  </div>
                  <div className="stat-item">
                    <span className="stat-label">마지막 업데이트</span>
                    <span className="stat-value">{new Date(newsData.lastBuildDate).toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>

              {/* 뉴스 리스트 */}
              <div className="news-list">
                {newsData.items.map((item, index) => (
                  <article key={index} className="news-item">
                    <div className="news-main">
                      <h3 className="news-title">
                        <a 
                          href={item.originallink} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          dangerouslySetInnerHTML={{ __html: item.title }}
                        />
                      </h3>
                      <p className="news-description">
                        {stripHtml(item.description)}
                      </p>
                      <div className="news-meta">
                        <Calendar />
                        <span>{formatDate(item.pubDate)}</span>
                        <span className="separator">•</span>
                        <a 
                          href={item.originallink} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="news-link"
                        >
                          원문 보기
                          <ExternalLink />
                        </a>
                      </div>
                    </div>
                    <div className="news-index">
                      {index + 1}
                    </div>
                  </article>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default NewsView;