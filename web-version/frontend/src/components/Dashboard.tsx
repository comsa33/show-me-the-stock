import React, { useState, useEffect } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import ViewManager from './ViewManager';
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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedMarket, setSelectedMarket] = useState<'KR' | 'US'>('KR');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [apiData, setApiData] = useState<ApiData>({
    stocks: [],
    interestRates: {
      korea: { rate: 0, description: '' },
      usa: { rate: 0, description: '' }
    },
    loading: true,
    error: null
  });

  const fetchData = async (page: number = currentPage) => {
    setApiData(prev => ({ ...prev, loading: true, error: null }));
    
    try {
      // Fetch stocks data with pagination using v2 API
      const marketParam = selectedMarket === 'KR' ? 'KOSPI' : 'US';
      const stocksResponse = await fetch(
        `http://localhost:8000/api/v1/stocks/v2/market/prices/${marketParam}?page=${page}&limit=${pageSize}`
      );
      const stocksData = await stocksResponse.json();

      // Fetch interest rates
      const ratesResponse = await fetch('http://localhost:8000/api/v1/interest-rates/current');
      const ratesData = await ratesResponse.json();

      setApiData({
        stocks: stocksData.stocks || [],
        interestRates: ratesData.current_rates || {
          korea: { rate: 0, description: '' },
          usa: { rate: 0, description: '' }
        },
        loading: false,
        error: null
      });
      
      // Update pagination info
      setTotalPages(stocksData.total_pages || 1);
      setTotalCount(stocksData.total_count || 0);
      setCurrentPage(stocksData.page || 1);
      
    } catch (error) {
      console.error('Error fetching data:', error);
      setApiData(prev => ({
        ...prev,
        loading: false,
        error: 'Failed to fetch data from server'
      }));
    }
  };

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    fetchData(page);
  };

  useEffect(() => {
    setCurrentPage(1);  // 시장 변경시 첫 페이지로
    fetchData(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedMarket]);

  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <div className="dashboard">
      <Header onToggleSidebar={toggleSidebar} />
      
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