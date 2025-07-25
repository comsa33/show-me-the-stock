import React, { useEffect } from 'react';
import { AppProvider, useApp } from './context/AppContext';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import Dashboard from './components/Dashboard';
import FloatingChatButton from './components/common/FloatingChatButton';
import SessionDebug from './components/debug/SessionDebug';
import './App.css';

const AppContent = () => {
  const { fetchMarketIndices, setCurrentView } = useApp();

  useEffect(() => {
    // Check if this is an auth callback
    if (window.location.pathname === '/auth/callback') {
      setCurrentView('auth-callback');
    }
  }, [setCurrentView]);

  useEffect(() => {
    fetchMarketIndices();
  }, [fetchMarketIndices]);

  return (
    <>
      <Dashboard />
      <FloatingChatButton />
      {/* Temporary debug component - remove after fixing loading issue */}
      <SessionDebug />
    </>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppProvider>
          <div className="App">
            <AppContent />
          </div>
        </AppProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;