/**
 * ================================================
 * 실시간 주식 알림 서비스
 * ================================================
 */

export interface StockAlert {
  id: string;
  type: 'price' | 'market' | 'news' | 'volume' | 'ai';
  priority: 'low' | 'medium' | 'high' | 'critical';
  symbol?: string;
  title: string;
  message: string;
  data?: {
    currentPrice?: number;
    previousPrice?: number;
    changePercent?: number;
    volume?: number;
    timestamp?: Date;
  };
  timestamp: Date;
}

export interface NotificationConfig {
  priceAlerts: {
    enabled: boolean;
    thresholds: {
      minor: number; // 3%
      major: number; // 5% 
      critical: number; // 10%
    };
  };
  marketAlerts: {
    enabled: boolean;
    vixThreshold: number; // 25
    indexThreshold: number; // 2%
  };
  volumeAlerts: {
    enabled: boolean;
    multiplier: number; // 3x average
  };
  aiAlerts: {
    enabled: boolean;
    quantScoreThreshold: number; // 70
  };
  watchlist: string[]; // 관심 종목
}

class NotificationService {
  private static instance: NotificationService;
  private ws: WebSocket | null = null;
  private config: NotificationConfig;
  private callbacks: ((alert: StockAlert) => void)[] = [];
  
  constructor() {
    this.config = this.getDefaultConfig();
  }

  static getInstance(): NotificationService {
    if (!NotificationService.instance) {
      NotificationService.instance = new NotificationService();
    }
    return NotificationService.instance;
  }

  private getDefaultConfig(): NotificationConfig {
    return {
      priceAlerts: {
        enabled: true,
        thresholds: {
          minor: 3,
          major: 5,
          critical: 10
        }
      },
      marketAlerts: {
        enabled: true,
        vixThreshold: 25,
        indexThreshold: 2
      },
      volumeAlerts: {
        enabled: true,
        multiplier: 3
      },
      aiAlerts: {
        enabled: true,
        quantScoreThreshold: 70
      },
      watchlist: ['005930', '000660', 'AAPL', 'MSFT', 'TSLA'] // 기본 관심종목
    };
  }

  // 실시간 알림 구독 시작
  public startRealTimeAlerts(): void {
    this.initWebSocket();
    this.startMarketMonitoring();
  }

  // WebSocket 연결
  private initWebSocket(): void {
    try {
      // 백엔드 WebSocket 서버에 연결
      const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/api/v1/stocks/realtime';
      this.ws = new WebSocket(wsUrl);
      
      this.ws.onopen = () => {
        console.log('📡 실시간 알림 WebSocket 연결 성공');
        this.subscribeToSymbols();
      };
      
      this.ws.onmessage = (event) => {
        this.handleWebSocketMessage(event);
      };
      
      this.ws.onerror = (error) => {
        console.error('❌ WebSocket 연결 오류:', error);
        // 시뮬레이션 모드로 전환하지 않고 재연결 시도
      };
      
      this.ws.onclose = () => {
        console.log('🔌 WebSocket 연결 종료, 5초 후 재연결 시도');
        setTimeout(() => this.initWebSocket(), 5000);
      };
    } catch (error) {
      console.error('WebSocket 초기화 오류:', error);
      // 5초 후 재시도
      setTimeout(() => this.initWebSocket(), 5000);
    }
  }

  // WebSocket 메시지 처리
  private handleWebSocketMessage(event: MessageEvent): void {
    try {
      const data = JSON.parse(event.data);
      
      if (data.type === 'price_alert') {
        this.processWebSocketAlert(data);
      } else if (data.type === 'market_alert') {
        this.processWebSocketAlert(data);
      } else if (data.type === 'welcome') {
        console.log('👋 WebSocket 서버 환영 메시지:', data.message);
      } else if (data.type === 'heartbeat') {
        // heartbeat는 로그하지 않음
      }
    } catch (error) {
      console.error('WebSocket 메시지 파싱 오류:', error);
    }
  }
  
  // WebSocket 알림 처리
  private processWebSocketAlert(data: any): void {
    const alert: StockAlert = {
      id: data.id,
      type: this.mapBackendAlertType(data.type),
      priority: data.alert_level as 'low' | 'medium' | 'high' | 'critical',
      symbol: data.symbol,
      title: data.title,
      message: data.message,
      data: data.data,
      timestamp: new Date(data.timestamp)
    };
    
    this.triggerAlert(alert);
  }
  
  // 백엔드 알림 타입 매핑
  private mapBackendAlertType(backendType: string): 'price' | 'market' | 'news' | 'volume' | 'ai' {
    switch (backendType) {
      case 'price_alert': return 'price';
      case 'market_alert': return 'market';
      case 'volume_alert': return 'volume';
      case 'news_alert': return 'news';
      case 'ai_alert': return 'ai';
      default: return 'market';
    }
  }

  // 관심 종목 구독
  private subscribeToSymbols(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const subscription = {
        action: 'subscribe',
        symbols: this.config.watchlist
      };
      this.ws.send(JSON.stringify(subscription));
    }
  }

  // WebSocket 대체 시뮬레이션
  private fallbackToPolling(): void {
    console.log('🔧 WebSocket 비활성화: 시뮬레이션 모드로 전환');
    // 시뮬레이션 모드에서만 가지 데이터 생성
    this.startSimulationMode();
  }

  // 시장 상황 모니터링
  private startMarketMonitoring(): void {
    // 장 시간 체크만 유지 (나머지는 백엔드에서 처리)
    setInterval(() => {
      this.checkMarketHours();
    }, 60000); // 1분마다 체크
  }


  // 주식 데이터 처리
  private processStockData(data: any): void {
    if (data.type === 'price_update') {
      this.checkPriceAlerts(data);
    } else if (data.type === 'volume_spike') {
      this.checkVolumeAlerts(data);
    } else if (data.type === 'news') {
      this.createNewsAlert(data);
    }
  }

  // 가격 알림 체크
  private checkPriceAlerts(data: any): void {
    if (!this.config.priceAlerts.enabled) return;

    const { symbol, currentPrice, previousPrice, uniqueId } = data;
    const changePercent = ((currentPrice - previousPrice) / previousPrice) * 100;
    const absChange = Math.abs(changePercent);

    let priority: 'low' | 'medium' | 'high' | 'critical' = 'low';
    let alertTitle = '';

    if (absChange >= this.config.priceAlerts.thresholds.critical) {
      priority = 'critical';
      alertTitle = changePercent > 0 ? '🚀 급등 알림' : '🔥 급락 알림';
    } else if (absChange >= this.config.priceAlerts.thresholds.major) {
      priority = 'high';
      alertTitle = changePercent > 0 ? '📈 상승 알림' : '📉 하락 알림';
    } else if (absChange >= this.config.priceAlerts.thresholds.minor) {
      priority = 'medium';
      alertTitle = changePercent > 0 ? '⬆️ 소폭 상승' : '⬇️ 소폭 하락';
    } else {
      return; // 임계값 미달
    }

    const alert: StockAlert = {
      id: uniqueId || `price_${symbol}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      type: 'price',
      priority,
      symbol,
      title: alertTitle,
      message: `${symbol}이(가) ${changePercent.toFixed(2)}% ${changePercent > 0 ? '상승' : '하락'}했습니다.`,
      data: {
        currentPrice,
        previousPrice,
        changePercent,
        timestamp: new Date()
      },
      timestamp: new Date()
    };

    this.triggerAlert(alert);
  }

  // 거래량 알림 체크
  private checkVolumeAlerts(data: any): void {
    if (!this.config.volumeAlerts.enabled) return;

    const { symbol, volume, averageVolume } = data;
    const volumeRatio = volume / averageVolume;

    if (volumeRatio >= this.config.volumeAlerts.multiplier) {
      const alert: StockAlert = {
        id: `volume_${symbol}_${Date.now()}`,
        type: 'volume',
        priority: volumeRatio >= 5 ? 'high' : 'medium',
        symbol,
        title: '📊 거래량 급증',
        message: `${symbol}의 거래량이 평균의 ${volumeRatio.toFixed(1)}배 증가했습니다.`,
        data: {
          volume,
          timestamp: new Date()
        },
        timestamp: new Date()
      };

      this.triggerAlert(alert);
    }
  }

  // 장 시간 체크
  private checkMarketHours(): void {
    const now = new Date();
    const kstHour = (now.getUTCHours() + 9) % 24; // KST 변환
    const usHour = now.getUTCHours() - 5; // EST 변환 (대략)

    // 한국 장 개장 (09:00)
    if (kstHour === 9 && now.getMinutes() === 0) {
      this.triggerAlert({
        id: `market_open_kr_${Date.now()}`,
        type: 'market',
        priority: 'medium',
        title: '🇰🇷 한국 증시 개장',
        message: '코스피/코스닥 장이 개장되었습니다.',
        timestamp: new Date()
      });
    }

    // 미국 장 개장 (09:30 EST)
    if (usHour === 9 && now.getMinutes() === 30) {
      this.triggerAlert({
        id: `market_open_us_${Date.now()}`,
        type: 'market',
        priority: 'medium',
        title: '🇺🇸 미국 증시 개장',
        message: 'NYSE/NASDAQ 장이 개장되었습니다.',
        timestamp: new Date()
      });
    }
  }



  // 시뮬레이션 모드 시작
  private startSimulationMode(): void {
    console.log('🎮 시뮬레이션 모드 시작: 가짜 데이터로 알림 생성');
    
    // 주기적으로 가짜 알림 생성
    setInterval(() => {
      this.generateSimulatedAlert();
    }, 45000); // 45초마다
  }
  
  // 가짜 알림 생성
  private generateSimulatedAlert(): void {
    const symbols = ['005930', '000660', 'AAPL', 'MSFT', 'TSLA'];
    const symbol = symbols[Math.floor(Math.random() * symbols.length)];
    const changePercent = (Math.random() - 0.5) * 20; // -10% ~ +10%
    
    if (Math.abs(changePercent) >= 3) { // 3% 이상만 알림 생성
      const alertData = {
        type: 'price_alert',
        id: `sim_${symbol}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        alert_level: Math.abs(changePercent) >= 8 ? 'critical' : Math.abs(changePercent) >= 5 ? 'high' : 'medium',
        symbol,
        title: changePercent > 0 ? '🚀 상승 알림' : '📉 하락 알림',
        message: `${symbol}이(가) ${changePercent.toFixed(2)}% ${changePercent > 0 ? '상승' : '하락'}했습니다. (시뮬레이션)`,
        data: {
          current_price: 100 * (1 + changePercent / 100),
          previous_price: 100,
          change_percent: changePercent
        },
        timestamp: new Date().toISOString()
      };
      
      this.processWebSocketAlert(alertData);
    }
  }

  // 알림 트리거
  private triggerAlert(alert: StockAlert): void {
    console.log('🔔 새 알림:', alert);
    this.callbacks.forEach(callback => callback(alert));
  }

  // 알림 콜백 등록
  public onAlert(callback: (alert: StockAlert) => void): void {
    this.callbacks.push(callback);
  }

  // 설정 업데이트
  public updateConfig(newConfig: Partial<NotificationConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  // 관심 종목 추가
  public addToWatchlist(symbol: string): void {
    if (!this.config.watchlist.includes(symbol)) {
      this.config.watchlist.push(symbol);
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          action: 'subscribe',
          symbols: [symbol]
        }));
      }
    }
  }

  // 뉴스 알림 생성
  private createNewsAlert(data: any): void {
    const { symbol, title, content, impact } = data;
    
    let priority: 'low' | 'medium' | 'high' | 'critical' = 'medium';
    if (impact === 'high') priority = 'high';
    if (impact === 'critical') priority = 'critical';
    
    const alert: StockAlert = {
      id: `news_${symbol}_${Date.now()}`,
      type: 'news',
      priority,
      symbol,
      title: `📰 ${title}`,
      message: content || `${symbol} 관련 중요 뉴스가 발표되었습니다.`,
      timestamp: new Date()
    };

    this.triggerAlert(alert);
  }

  // AI 분석 알림 생성
  private createAIAlert(symbol: string, analysisType: string, data: any): void {
    const alert: StockAlert = {
      id: `ai_${symbol}_${Date.now()}`,
      type: 'ai',
      priority: data.confidence > 0.8 ? 'high' : 'medium',
      symbol,
      title: `🤖 AI 분석 신호`,
      message: `${symbol}에서 ${analysisType} 패턴이 감지되었습니다. (신뢰도: ${(data.confidence * 100).toFixed(1)}%)`,
      data: {
        timestamp: new Date()
      },
      timestamp: new Date()
    };

    this.triggerAlert(alert);
  }

  // 서비스 중지
  public stop(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export default NotificationService;