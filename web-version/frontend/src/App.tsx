import React from 'react';
import { AppProvider } from './context/AppContext';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  return (
    <AppProvider>
      <div className="App">
        <Dashboard />
      </div>
    </AppProvider>
  );
}

export default App;