import React, { useEffect, useState } from 'react';
import './App.css';

interface ApiStatus {
  backend: boolean;
  stocks: boolean;
  market: boolean;
}

function App() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>({
    backend: false,
    stocks: false,
    market: false
  });

  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        // Check backend health
        const healthResponse = await fetch('http://localhost:8000/health');
        setApiStatus(prev => ({ ...prev, backend: healthResponse.ok }));

        // Check stocks endpoint
        const stocksResponse = await fetch('http://localhost:8000/api/v1/stocks');
        setApiStatus(prev => ({ ...prev, stocks: stocksResponse.ok }));

        // Check market status endpoint
        const marketResponse = await fetch('http://localhost:8000/api/v1/market/status');
        setApiStatus(prev => ({ ...prev, market: marketResponse.ok }));
      } catch (error) {
        console.error('API status check failed:', error);
      }
    };

    checkApiStatus();
  }, []);

  const getStatusText = (status: boolean) => {
    return status ? '✅ 연결됨' : '❌ 연결 실패';
  };

  const getStatusClass = (status: boolean) => {
    return status ? 'status-card success' : 'status-card error';
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🚀 Stock Dashboard</h1>
        <p>AI 기반 주식 분석 대시보드 - Modern Web Architecture</p>
        
        <div className="status-grid">
          <div className={getStatusClass(apiStatus.backend)}>
            <h3>Backend API</h3>
            <p>{getStatusText(apiStatus.backend)}</p>
            <small>FastAPI 서버 상태</small>
          </div>
          
          <div className={getStatusClass(apiStatus.stocks)}>
            <h3>Stock Data</h3>
            <p>{getStatusText(apiStatus.stocks)}</p>
            <small>주식 데이터 API</small>
          </div>
          
          <div className={getStatusClass(apiStatus.market)}>
            <h3>Market Status</h3>
            <p>{getStatusText(apiStatus.market)}</p>
            <small>시장 상태 API</small>
          </div>
        </div>
        
        <div className="info-section">
          <h2>시스템 정보</h2>
          <ul>
            <li>Frontend: React 19 + TypeScript</li>
            <li>Backend: FastAPI + Python</li>
            <li>Cache: Redis</li>
            <li>Deployment: Kubernetes + Helm</li>
          </ul>
        </div>
        
        <p className="version">Version 2.0.0 - Ready for Kubernetes Deployment</p>
      </header>
    </div>
  );
}

export default App;