import React, { useState, useEffect } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import ViewManager from './ViewManager';
import { API_BASE } from '../config';
import './Dashboard.css';

interface Stock {
  name: string;
  symbol: string;
  display: string;
  market?: 'KR' | 'US';
  price?: number;
  change?: number;
  change_percent?: number;
  volume?: number;
}

interface InterestRate {
  rate: number;
  description: string;
}

export interface ApiData {
  stocks: Stock[];
  interestRates: {
    korea: InterestRate;
    usa: InterestRate;
  };
  loading: boolean;
  error: string | null;
}

const Dashboard: React.FC = () => {
  // ---------- UI 상태 ----------
  const [sidebarOpen, setSidebarOpen]       = useState(false);
  const [selectedMarket, setSelectedMarket] = useState<'KR' | 'US'>('KR');
  const [currentPage, setCurrentPage]       = useState(1);
  const [pageSize]                          = useState(20);
  const [totalPages, setTotalPages]         = useState(1);
  const [totalCount, setTotalCount]         = useState(0);

  // ---------- API 데이터 ----------
  const [apiData, setApiData] = useState<ApiData>({
    stocks: [],
    interestRates: {
      korea: { rate: 0, description: '' },
      usa:   { rate: 0, description: '' },
    },
    loading: true,
    error: null,
  });

  /** 주식·금리 데이터 요청 */
  const fetchData = async (page: number = currentPage) => {
    setApiData(prev => ({ ...prev, loading: true, error: null }));

    try {
      /* 1) 주가 호출 ---------------------------------------------------- */
      const marketParam  = selectedMarket === 'KR' ? 'KOSPI' : 'US';
      const v2URL = `${API_BASE}/v1/stocks/v2/market/prices/${marketParam}?page=${page}&limit=${pageSize}`;
      const v1URL = `${API_BASE}/v1/stocks/prices/${selectedMarket}?limit=${pageSize}`;

      let stocksRes  = await fetch(v2URL);
      let stocksData = await stocksRes.json();

      // v2가 비어 있으면 v1로 재시도
      if (!stocksData.stocks?.length || stocksData.stocks.every((s: any) => s.price === 0)) {
        console.warn('v2 API empty → fallback to v1');
        stocksRes  = await fetch(v1URL);
        const v1   = await stocksRes.json();

        // v1 응답을 v2 포맷으로 가공
        stocksData = {
          stocks:      v1.stocks || [],
          page:        page,
          total_pages: Math.ceil((v1.total_available || 0) / pageSize),
          total_count: v1.total_available || 0,
        };
      }

      /* 2) 금리 호출 ---------------------------------------------------- */
      const ratesRes = await fetch(`${API_BASE}/v1/interest-rates/current`);
      const rates    = await ratesRes.json();

      /* 3) 상태 반영 ---------------------------------------------------- */
      setApiData({
        stocks:        stocksData.stocks,
        interestRates: rates.current_rates,
        loading:       false,
        error:         null,
      });
      setTotalPages(stocksData.total_pages);
      setTotalCount(stocksData.total_count);
      setCurrentPage(stocksData.page);
    } catch (err) {
      console.error('Error fetching data:', err);
      setApiData(prev => ({ ...prev, loading: false, error: '서버 통신 실패' }));
    }
  };

  /* ------- 마켓·페이지 전환 핸들러 ------- */
  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    fetchData(page);
  };

  /* ------- 첫 로드 & 마켓 변경 시 ------- */
  useEffect(() => {
    setCurrentPage(1);
    fetchData(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedMarket]);

  return (
    <div className="dashboard">
      <Header onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />

      <div className="dashboard-body">
        <Sidebar
          isOpen={sidebarOpen}
          selectedMarket={selectedMarket}
          onMarketChange={setSelectedMarket}
          interestRates={apiData.interestRates}
        />

        <ViewManager
          apiData={apiData}
          selectedMarket={selectedMarket}
          onRefresh={fetchData}
          currentPage={currentPage}
          totalPages={totalPages}
          totalCount={totalCount}
          pageSize={pageSize}
          onPageChange={handlePageChange}
        />
      </div>
    </div>
  );
};

export default Dashboard;