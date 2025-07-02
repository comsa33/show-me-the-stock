import React, { createContext, useContext, useState, ReactNode, useCallback, useEffect } from 'react';
import { API_BASE } from '../config';
import NotificationService, { StockAlert } from '../services/NotificationService';

export type ViewType = 'dashboard' | 'stocks' | 'quant' | 'portfolio' | 'watchlist' | 'news' | 'reports';

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

interface Notification {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  symbol?: string;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  category?: 'price' | 'market' | 'news' | 'volume' | 'ai';
}

export interface MarketIndex {
  name: string;
  value: number;
  change: number;
  change_percent: number;
  current_price: number;
  symbol?: string;
  volume?: number;
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
  clearAllNotifications: () => void;
  isRealTimeEnabled: boolean;
  toggleRealTime: () => void;
  marketIndices: {
    korea: MarketIndex[];
    us: MarketIndex[];
  };
  marketIndicesLoading: boolean;
  fetchMarketIndices: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [currentView, setCurrentView] = useState<ViewType>('dashboard');
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(false);
  const [marketIndices, setMarketIndices] = useState<{ korea: MarketIndex[], us: MarketIndex[] }>({ korea: [], us: [] });
  const [marketIndicesLoading, setMarketIndicesLoading] = useState(true);

  const addNotification = (notification: Omit<Notification, 'id' | 'timestamp'>) => {
    const newNotification: Notification = {
      ...notification,
      id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date()
    };
    setNotifications(prev => [newNotification, ...prev]);
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const clearAllNotifications = () => {
    setNotifications([]);
  };

  const toggleRealTime = () => {
    setIsRealTimeEnabled(prev => {
      const newState = !prev;
      if (newState) {
        startRealTimeNotifications();
      } else {
        stopRealTimeNotifications();
      }
      return newState;
    });
  };

  // 실시간 알림 시작
  const startRealTimeNotifications = () => {
    const notificationService = NotificationService.getInstance();
    
    // 알림 콜백 등록
    notificationService.onAlert((alert: StockAlert) => {
      const notification = {
        type: mapAlertTypeToNotificationType(alert.type, alert.priority),
        title: alert.title,
        message: alert.message,
        symbol: alert.symbol,
        priority: alert.priority,
        category: alert.type
      };
      // addNotification이 자체적으로 고유 ID를 생성하도록 함
      addNotification(notification);
    });
    
    // 실시간 알림 시작
    notificationService.startRealTimeAlerts();
    
    // 환영 메시지
    addNotification({
      type: 'success',
      title: '📡 실시간 알림 활성화',
      message: '주식 시장의 실시간 알림을 받을 수 있습니다.',
      priority: 'medium',
      category: 'market'
    });
  };

  // 실시간 알림 중지
  const stopRealTimeNotifications = () => {
    const notificationService = NotificationService.getInstance();
    notificationService.stop();
    
    addNotification({
      type: 'info',
      title: '🔕 실시간 알림 비활성화',
      message: '실시간 알림이 중지되었습니다.',
      priority: 'low',
      category: 'market'
    });
  };

  // 알림 타입 매핑
  const mapAlertTypeToNotificationType = (alertType: string, priority: string): 'info' | 'success' | 'warning' | 'error' => {
    if (priority === 'critical') return 'error';
    if (priority === 'high') return 'warning';
    if (alertType === 'price' && priority === 'medium') return 'warning';
    if (alertType === 'market') return 'info';
    return 'success';
  };

  // 컴포넌트 마운트 시 기본 알림 추가
  useEffect(() => {
    const initNotifications = [
      {
        type: 'info' as const,
        title: '🌟 ShowMeTheStock에 오신 것을 환영합니다',
        message: '실시간 주식 알림을 받으려면 우상단 알림 버튼에서 실시간 알림을 활성화하세요.',
        priority: 'medium' as const,
        category: 'market' as const
      },
      {
        type: 'success' as const,
        title: '📊 데이터 동기화 완료',
        message: '최신 시장 데이터가 업데이트되었습니다.',
        priority: 'low' as const,
        category: 'market' as const
      }
    ];

    initNotifications.forEach(notification => {
      setTimeout(() => addNotification(notification), 1000);
    });
  }, []);

  const fetchMarketIndices = useCallback(async () => {
    setMarketIndicesLoading(true);
    try {
      const [koreanRes, usRes] = await Promise.all([
        fetch(`${API_BASE}/v1/indices/korean`),
        fetch(`${API_BASE}/v1/indices/us`)
      ]);

      const koreanData = koreanRes.ok ? await koreanRes.json() : { indices: [] };
      const usData = usRes.ok ? await usRes.json() : { indices: [] };

      const adaptData = (data: any[]): MarketIndex[] => {
        if (!Array.isArray(data)) return [];
        return data.map(item => ({
          ...item,
          current_price: item.value,
          symbol: item.name
        }));
      };

      setMarketIndices({
        korea: adaptData(koreanData.indices),
        us: adaptData(usData.indices),
      });

    } catch (error) {
      console.error("Failed to fetch market indices:", error);
      setMarketIndices({ korea: [], us: [] });
    } finally {
      setMarketIndicesLoading(false);
    }
  }, []);

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
      removeNotification,
      clearAllNotifications,
      isRealTimeEnabled,
      toggleRealTime,
      marketIndices,
      marketIndicesLoading,
      fetchMarketIndices,
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