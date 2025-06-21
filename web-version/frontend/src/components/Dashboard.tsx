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
      const allStocksURL = `${API_BASE}/v1/stocks/all/${selectedMarket}?page=${page}&limit=${pageSize}`;
      const pricesURL = `${API_BASE}/v1/stocks/prices/${selectedMarket}?page=${page}&limit=${pageSize}`;

      // 전체 종목 리스트 가져오기 (가격 정보 포함)
      let stocksRes = await fetch(pricesURL);
      let stocksData = await stocksRes.json();

      // 가격 정보가 없으면 전체 종목 리스트만 가져오기
      if (!stocksData.stocks?.length) {
        console.warn('Price API empty → fallback to all stocks list');
        stocksRes = await fetch(allStocksURL);
        stocksData = await stocksRes.json();
      }

      /* 2) 금리 호출 ---------------------------------------------------- */
      const ratesRes = await fetch(`${API_BASE}/v1/interest-rates/current`);
      const rates    = await ratesRes.json();

      /* 3) 상태 반영 ---------------------------------------------------- */
      setApiData({
        stocks:        stocksData.stocks || [],
        interestRates: rates.current_rates,
        loading:       false,
        error:         null,
      });
      setTotalPages(stocksData.total_pages || 1);
      setTotalCount(stocksData.total_count || 0);
      setCurrentPage(stocksData.page || page);
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