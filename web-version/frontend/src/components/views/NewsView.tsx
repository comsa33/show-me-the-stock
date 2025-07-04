import React, { useState, useEffect, useCallback } from 'react';
import { useApp } from '../../context/AppContext';
import { API_BASE } from '../../config';
import { RefreshCw, Calendar, ExternalLink, Search } from 'lucide-react';
import { stockCache } from '../../utils/stockCache';
import SearchableSelect from '../common/SearchableSelect';
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
  page_info?: {
    current_page: number;
    total_pages: number;
    items_per_page: number;
    total_items: number;
    start_index: number;
  };
}

interface CachedNews {
  data: NewsResponse;
  timestamp: number;
  query: string;
}

interface SimpleStock {
  symbol: string;
  name: string;
}

const NewsView: React.FC<NewsViewProps> = ({ selectedMarket }) => {
  const { selectedStock } = useApp();
  const [newsData, setNewsData] = useState<NewsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [displayCount, setDisplayCount] = useState<number>(10);
  const [currentPage, setCurrentPage] = useState(1);
  const [allStocks, setAllStocks] = useState<SimpleStock[]>([]);
  const [stocksLoading, setStocksLoading] = useState(false);
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

  // 도메인 추출 함수
  const extractDomain = (url: string): string => {
    try {
      const urlObj = new URL(url);
      let domain = urlObj.hostname;
      
      // www. 제거
      domain = domain.replace(/^www\./, '');
      
      // 전체 도메인 반환 (매핑 테이블에서 찾기 위해)
      return domain;
    } catch (error) {
      return 'Unknown';
    }
  };

  // 도메인별 표시 이름 매핑
  const getDomainDisplayName = (domain: string): string => {
    // 전체 도메인으로 먼저 매칭 시도
    const fullDomainMap: { [key: string]: string } = {
      'news.naver.com': '네이버',
      'n.news.naver.com': '네이버',
      'naver.com': '네이버',
      'daum.net': '다음',
      'news.daum.net': '다음',
      'hankyung.com': '한국경제',
      'mk.co.kr': '매일경제',
      'news.mt.co.kr': '머니투데이',
      'mt.co.kr': '머니투데이',
      'edaily.co.kr': '이데일리',
      'sedaily.com': '서울경제',
      'etnews.com': '전자신문',
      'chosun.com': '조선일보',
      'donga.com': '동아일보',
      'news.joins.com': '중앙일보',
      'joongang.co.kr': '중앙일보',
      'khan.co.kr': '경향신문',
      'hani.co.kr': '한겨레',
      'yna.co.kr': '연합뉴스',
      'yonhapnews.co.kr': '연합뉴스',
      'news.sbs.co.kr': 'SBS',
      'imnews.imbc.com': 'MBC',
      'news.kbs.co.kr': 'KBS',
      'news.jtbc.co.kr': 'JTBC',
      'ytn.co.kr': 'YTN',
      'sisunnews.co.kr': '시선뉴스',
      'fnnews.com': '파이낸셜뉴스',
      'newsis.com': '뉴시스',
      'news1.kr': '뉴스1',
      'asiae.co.kr': '아시아경제',
      'ajunews.com': '아주경제',
      'inews24.com': '아이뉴스24',
      'zdnet.co.kr': 'ZDNet',
      'bloter.net': '블로터',
      'thelec.kr': '더엘렉',
      'economist.co.kr': '이코노미스트'
    };
    
    // 전체 도메인으로 매칭
    if (fullDomainMap[domain.toLowerCase()]) {
      return fullDomainMap[domain.toLowerCase()];
    }
    
    // 도메인의 첫 부분으로 다시 시도
    const parts = domain.split('.');
    const mainPart = parts[0];
    
    const partialMap: { [key: string]: string } = {
      'naver': '네이버',
      'daum': '다음',
      'hankyung': '한국경제',
      'mk': '매일경제',
      'mt': '머니투데이',
      'edaily': '이데일리',
      'sedaily': '서울경제',
      'etnews': '전자신문',
      'chosun': '조선일보',
      'donga': '동아일보',
      'joongang': '중앙일보',
      'khan': '경향신문',
      'hani': '한겨레',
      'yonhap': '연합뉴스',
      'yna': '연합뉴스'
    };
    
    if (partialMap[mainPart.toLowerCase()]) {
      return partialMap[mainPart.toLowerCase()];
    }
    
    // 둘 다 실패하면 도메인의 주요 부분 반환
    if (parts.length >= 2) {
      // co.kr, .com 등을 제거하고 주요 부분만 반환
      const name = parts[0].replace(/news|www/, '');
      return name.toUpperCase();
    }
    
    return domain.split('.')[0].toUpperCase();
  };

  // 종목 목록 가져오기
  const fetchStocks = useCallback(async () => {
    const cacheKey = `stocks_simple_${selectedMarket}`;
    
    // 캐시 확인
    const cached = stockCache.get<SimpleStock[]>(cacheKey);
    if (cached) {
      setAllStocks(cached);
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
      const stocks = data.stocks || data;
      setAllStocks(stocks);
      
      // 캐시에 저장 (24시간)
      stockCache.set(cacheKey, stocks);
    } catch (error) {
      console.error('Failed to fetch stocks:', error);
      // 실패 시 인기 종목만 사용
      setAllStocks([]);
    } finally {
      setStocksLoading(false);
    }
  }, [selectedMarket]);

  // 선택된 주식이 있으면 해당 주식으로 설정
  useEffect(() => {
    if (selectedStock) {
      setSelectedSymbol(selectedStock.symbol);
    }
  }, [selectedStock]);

  // 종목 목록 가져오기
  useEffect(() => {
    fetchStocks();
  }, [fetchStocks]);

  // 뉴스 가져오기
  const fetchNews = useCallback(async (forceRefresh: boolean = false, page: number = 1) => {
    if (!selectedSymbol) return;

    const cacheKey = `${selectedSymbol}-${displayCount}-${page}`;
    const cached = newsCache.get(cacheKey);

    // 캐시 확인
    if (!forceRefresh && cached && Date.now() - cached.timestamp < CACHE_DURATION) {
      setNewsData(cached.data);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // allStocks와 popularStocks에서 중복 없이 찾기
      const stock = allStocks.find(s => s.symbol === selectedSymbol) || 
                   popularStocks.find(s => s.symbol === selectedSymbol);
      const query = stock ? encodeURIComponent(stock.name) : encodeURIComponent(selectedSymbol);
      
      const response = await fetch(`${API_BASE}/v1/news/search?query=${query}&display=${displayCount}&page=${page}&sort=sim`);

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
  }, [selectedSymbol, displayCount, newsCache, popularStocks, allStocks, CACHE_DURATION]);

  // 심볼, 페이지, 표시 개수 변경 시 뉴스 자동 로드
  useEffect(() => {
    if (selectedSymbol) {
      fetchNews(false, currentPage);
    }
  }, [selectedSymbol, displayCount, currentPage, fetchNews]);

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
          <div className="header-left-section">
            <div className="header-text">
              <h2>실시간 뉴스</h2>
              <p>주식 관련 최신 뉴스를 확인하세요</p>
            </div>
          </div>
          
          <div className="header-controls">
            <div className="control-item stock-selector-wrapper">
              <SearchableSelect
                options={(() => {
                  // allStocks가 비어있으면 popularStocks만 사용
                  if (allStocks.length === 0) {
                    return popularStocks.filter(s => s.market === selectedMarket).map(stock => ({
                      value: stock.symbol,
                      label: stock.name,
                      subLabel: stock.symbol
                    }));
                  }
                  // allStocks가 있으면 allStocks만 사용 (중복 제거)
                  return allStocks.map(stock => ({
                    value: stock.symbol,
                    label: stock.name,
                    subLabel: stock.symbol
                  }));
                })()}
                value={selectedSymbol}
                onChange={(value) => {
                  setSelectedSymbol(value);
                  setCurrentPage(1);
                }}
                placeholder="종목명 또는 코드로 검색..."
                loading={stocksLoading}
                disabled={stocksLoading}
              />
            </div>

            <div className="control-item count-selector-wrapper">
              <select 
                className="count-selector"
                value={displayCount}
                onChange={(e) => {
                  setDisplayCount(Number(e.target.value));
                  setCurrentPage(1);
                }}
              >
                <option value={10}>10개씩</option>
                <option value={20}>20개씩</option>
                <option value={30}>30개씩</option>
                <option value={50}>50개씩</option>
              </select>
            </div>

            <button 
              className="refresh-button icon-only"
              onClick={() => fetchNews(true, currentPage)}
              disabled={loading || !selectedSymbol}
              title="새로고침"
            >
              <RefreshCw className={loading ? 'spinning' : ''} />
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
                {newsData.items.map((item, index) => {
                  const domain = extractDomain(item.originallink);
                  const domainName = getDomainDisplayName(domain);
                  
                  return (
                    <article key={index} className="news-item">
                      <div className="news-source-badge">
                        <span className="domain-full">{domain}</span>
                        <span className="domain-name">{domainName}</span>
                      </div>
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
                    </article>
                  );
                })}
              </div>

              {/* 페이지네이션 */}
              {newsData && newsData.page_info && newsData.page_info.total_pages > 1 && (
                <div className="pagination">
                  <button
                    className="pagination-btn"
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                  >
                    이전
                  </button>
                  
                  <div className="pagination-numbers">
                    {(() => {
                      const totalPages = newsData.page_info.total_pages;
                      const pageNumbers = [];
                      let startPage = Math.max(1, currentPage - 2);
                      let endPage = Math.min(totalPages, currentPage + 2);
                      
                      // 첫 페이지
                      if (startPage > 1) {
                        pageNumbers.push(
                          <button
                            key={1}
                            className={`pagination-number ${currentPage === 1 ? 'active' : ''}`}
                            onClick={() => setCurrentPage(1)}
                          >
                            1
                          </button>
                        );
                        if (startPage > 2) {
                          pageNumbers.push(<span key="dots1" className="pagination-dots">...</span>);
                        }
                      }
                      
                      // 중간 페이지들
                      for (let i = startPage; i <= endPage; i++) {
                        pageNumbers.push(
                          <button
                            key={i}
                            className={`pagination-number ${currentPage === i ? 'active' : ''}`}
                            onClick={() => setCurrentPage(i)}
                          >
                            {i}
                          </button>
                        );
                      }
                      
                      // 마지막 페이지
                      if (endPage < totalPages) {
                        if (endPage < totalPages - 1) {
                          pageNumbers.push(<span key="dots2" className="pagination-dots">...</span>);
                        }
                        pageNumbers.push(
                          <button
                            key={totalPages}
                            className={`pagination-number ${currentPage === totalPages ? 'active' : ''}`}
                            onClick={() => setCurrentPage(totalPages)}
                          >
                            {totalPages}
                          </button>
                        );
                      }
                      
                      return pageNumbers;
                    })()}
                  </div>
                  
                  <button
                    className="pagination-btn"
                    onClick={() => setCurrentPage(prev => Math.min(newsData.page_info!.total_pages, prev + 1))}
                    disabled={currentPage === newsData.page_info.total_pages}
                  >
                    다음
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

export default NewsView;