import React from 'react';
import { Menu, Search, Bell, Sun, Moon, Settings } from 'lucide-react';
import { motion } from 'framer-motion';

import { useUIStore } from '../../store/uiStore';
import { useThemeStore } from '../../store/themeStore';
import StockSearch from '../Stock/StockSearch';

const Header: React.FC = () => {
  const { toggleSidebar } = useUIStore();
  const { theme, toggleTheme } = useThemeStore();

  return (
    <header className=\"bg-white dark:bg-gray-800 shadow-soft border-b border-gray-200 dark:border-gray-700\">
      <div className=\"px-4 sm:px-6 lg:px-8\">
        <div className=\"flex items-center justify-between h-16\">
          {/* Left side */}
          <div className=\"flex items-center space-x-4\">
            {/* Sidebar toggle */}
            <button
              onClick={toggleSidebar}
              className=\"p-2 rounded-lg text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors\"
              aria-label=\"Toggle sidebar\"
            >
              <Menu className=\"w-5 h-5\" />
            </button>
            
            {/* Logo/Title */}
            <div className=\"flex items-center space-x-3\">
              <div className=\"w-8 h-8 bg-gradient-to-r from-primary-500 to-primary-600 rounded-lg flex items-center justify-center\">
                <span className=\"text-white font-bold text-sm\">📈</span>
              </div>
              <h1 className=\"text-xl font-bold text-gray-900 dark:text-white hidden sm:block\">
                Stock Dashboard
              </h1>
            </div>
          </div>

          {/* Center - Search */}
          <div className=\"flex-1 max-w-md mx-4\">
            <StockSearch />
          </div>

          {/* Right side */}
          <div className=\"flex items-center space-x-2\">
            {/* Theme toggle */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={toggleTheme}
              className=\"p-2 rounded-lg text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors\"
              aria-label=\"Toggle theme\"
            >
              {theme === 'dark' ? (
                <Sun className=\"w-5 h-5\" />
              ) : (
                <Moon className=\"w-5 h-5\" />
              )}
            </motion.button>

            {/* Notifications */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className=\"p-2 rounded-lg text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors relative\"
              aria-label=\"Notifications\"
            >
              <Bell className=\"w-5 h-5\" />
              {/* Notification badge */}
              <span className=\"absolute -top-1 -right-1 w-3 h-3 bg-danger-500 rounded-full\"></span>
            </motion.button>

            {/* Settings */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className=\"p-2 rounded-lg text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors\"
              aria-label=\"Settings\"
            >
              <Settings className=\"w-5 h-5\" />
            </motion.button>

            {/* User profile */}
            <div className=\"relative ml-3\">
              <motion.div
                whileHover={{ scale: 1.05 }}
                className=\"w-8 h-8 bg-gradient-to-r from-primary-500 to-primary-600 rounded-full flex items-center justify-center cursor-pointer\"
              >
                <span className=\"text-white text-sm font-medium\">U</span>
              </motion.div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;