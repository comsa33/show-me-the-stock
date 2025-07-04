import React from 'react';
import { useApp } from '../context/AppContext';
import { ApiData } from './Dashboard';
import WatchlistView from './views/WatchlistView';
import NewsView from './views/NewsView';
import ReportsView from './views/ReportsView';
import QuantView from './views/QuantView';
import ChatView from './views/ChatView';
import MainContent from './MainContent';
import StockDetail from './StockDetail';
import './ViewManager.css';

interface ViewManagerProps {
  apiData: ApiData;
  selectedMarket: 'KR' | 'US';
  onRefresh: () => void;
  currentPage?: number;
  totalPages?: number;
  totalCount?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
}

const ViewManager: React.FC<ViewManagerProps> = ({ 
  apiData, 
  selectedMarket, 
  onRefresh, 
  currentPage, 
  totalPages, 
  totalCount, 
  pageSize, 
  onPageChange 
}) => {
  const { currentView } = useApp();

  const content = (() => {
    switch (currentView) {
      case 'stocks':
        return <StockDetail />;
      case 'quant':
        return <QuantView selectedMarket={selectedMarket} />;
      case 'watchlist':
        return <WatchlistView selectedMarket={selectedMarket} />;
      case 'news':
        return <NewsView selectedMarket={selectedMarket} />;
      case 'reports':
        return <ReportsView selectedMarket={selectedMarket} />;
      case 'chat':
        return <ChatView />;
      case 'dashboard':
      default:
        return (
          <MainContent 
            apiData={apiData} 
            selectedMarket={selectedMarket} 
            onRefresh={onRefresh}
            currentPage={currentPage}
            totalPages={totalPages}
            totalCount={totalCount}
            pageSize={pageSize}
            onPageChange={onPageChange}
          />
        );
    }
  })();

  return (
    <div className={`view-container ${currentView === 'chat' ? 'chat-view-container' : ''}`}>
      {content}
    </div>
  );
};

export default ViewManager;