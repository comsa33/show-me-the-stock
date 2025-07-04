import React, { useEffect } from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { ThemeProvider } from './context/ThemeContext';
import Dashboard from './components/Dashboard';
import FloatingChatButton from './components/common/FloatingChatButton';
import './App.css';

const AppContent = () => {
  const { fetchMarketIndices } = useApp();

  useEffect(() => {
    fetchMarketIndices();
  }, [fetchMarketIndices]);

  return (
    <>
      <Dashboard />
      <FloatingChatButton />
    </>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AppProvider>
        <div className="App">
          <AppContent />
        </div>
      </AppProvider>
    </ThemeProvider>
  );
}

export default App;