import React, { createContext, useContext, useState, ReactNode } from 'react';

export type ViewType = 'dashboard' | 'stocks' | 'portfolio' | 'watchlist' | 'news' | 'reports';

interface Stock {
  name: string;
  symbol: string;
  display: string;
  market: 'KR' | 'US';
  price?: number;
  change?: number;
  change_percent?: number;
  volume?: number | string;
}

interface AppContextType {
  currentView: ViewType;
  setCurrentView: (view: ViewType) => void;
  selectedStock: Stock | null;
  setSelectedStock: (stock: Stock | null) => void;
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  notifications: Notification[];
  addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
}

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [currentView, setCurrentView] = useState<ViewType>('dashboard');
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [notifications, setNotifications] = useState<Notification[]>([
    {
      id: '1',
      type: 'info',
      title: '시장 개장',
      message: '미국 증시가 곧 개장합니다.',
      timestamp: new Date()
    },
    {
      id: '2',
      type: 'success',
      title: '데이터 업데이트',
      message: '실시간 주가 데이터가 업데이트되었습니다.',
      timestamp: new Date()
    },
    {
      id: '3',
      type: 'warning',
      title: '급등 종목',
      message: 'NVIDIA(NVDA) 주가가 5% 이상 상승했습니다.',
      timestamp: new Date()
    }
  ]);

  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const newNotification: Notification = {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date()
    };
    setNotifications(prev => [newNotification, ...prev]);
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  return (
    <AppContext.Provider value={{
      currentView,
      setCurrentView,
      selectedStock,
      setSelectedStock,
      searchTerm,
      setSearchTerm,
      notifications,
      addNotification,
      removeNotification
    }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};