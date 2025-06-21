import React from 'react';
import StockList from './StockList';
import MarketOverview from './MarketOverview';
import { ApiData } from './Dashboard';
import './MainContent.css';

interface MainContentProps {
  apiData: ApiData;
  selectedMarket: 'KR' | 'US';
  onRefresh: () => void;
  currentPage?: number;
  totalPages?: number;
  totalCount?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
}

const MainContent: React.FC<MainContentProps> = ({ 
  apiData, 
  selectedMarket, 
  onRefresh, 
  currentPage, 
  totalPages, 
  totalCount, 
  pageSize, 
  onPageChange 
}) => {
  return (
    <main className="main-content">
      <div className="content-container">
        {/* Market Overview Section */}
        <section className="overview-section">
          <MarketOverview 
            selectedMarket={selectedMarket}
            interestRates={apiData.interestRates}
            onRefresh={onRefresh}
          />
        </section>

        {/* Stock List Section */}
        <section className="stocks-section">
          <StockList 
            stocks={apiData.stocks}
            selectedMarket={selectedMarket}
            loading={apiData.loading}
            error={apiData.error}
            onRefresh={onRefresh}
            currentPage={currentPage}
            totalPages={totalPages}
            totalCount={totalCount}
            pageSize={pageSize}
            onPageChange={onPageChange}
          />
        </section>
      </div>
    </main>
  );
};

export default MainContent;