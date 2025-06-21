import React from 'react';
import { useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';

import Header from './Header';
import Sidebar from './Sidebar';
import { useUIStore } from '../../store/uiStore';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const { sidebarOpen } = useUIStore();

  return (
    <div className=\"flex h-screen bg-gray-50 dark:bg-gray-900\">
      {/* Sidebar */}
      <Sidebar />
      
      {/* Main content area */}
      <div className={`flex-1 flex flex-col overflow-hidden transition-all duration-300 ${
        sidebarOpen ? 'lg:ml-64' : 'lg:ml-16'
      }`}>
        {/* Header */}
        <Header />
        
        {/* Page content */}
        <main className=\"flex-1 overflow-x-hidden overflow-y-auto bg-gray-50 dark:bg-gray-900\">
          <div className=\"container mx-auto px-4 sm:px-6 lg:px-8 py-6\">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3, ease: 'easeInOut' }}
            >
              {children}
            </motion.div>
          </div>
        </main>
      </div>
      
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className=\"fixed inset-0 z-20 bg-black bg-opacity-50 lg:hidden\"
          onClick={() => useUIStore.getState().toggleSidebar()}
        />
      )}
    </div>
  );
};

export default Layout;