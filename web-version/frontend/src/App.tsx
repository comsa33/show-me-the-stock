import React from 'react';
import { AppProvider } from './context/AppContext';
import { ThemeProvider } from './context/ThemeContext';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  return (
    <ThemeProvider>
      <AppProvider>
        <div className="App">
          <Dashboard />
        </div>
      </AppProvider>
    </ThemeProvider>
  );
}

export default App;