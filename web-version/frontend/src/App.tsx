import React, { Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Toaster } from 'react-hot-toast';

// Components
import Layout from './components/Layout/Layout';
import LoadingSpinner from './components/UI/LoadingSpinner';
import ErrorBoundary from './components/UI/ErrorBoundary';

// Pages (Lazy loaded for better performance)
const Dashboard = React.lazy(() => import('./pages/Dashboard'));
const Analytics = React.lazy(() => import('./pages/Analytics'));
const Favorites = React.lazy(() => import('./pages/Favorites'));
const Settings = React.lazy(() => import('./pages/Settings'));

// React Query client setup
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <Router>
          <div className=\"min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200\">
            <Layout>
              <Suspense 
                fallback={
                  <div className=\"flex items-center justify-center min-h-[60vh]\">
                    <LoadingSpinner size=\"large\" />
                  </div>
                }
              >
                <Routes>
                  <Route path=\"/\" element={<Dashboard />} />
                  <Route path=\"/analytics\" element={<Analytics />} />
                  <Route path=\"/favorites\" element={<Favorites />} />
                  <Route path=\"/settings\" element={<Settings />} />
                  {/* 404 fallback */}
                  <Route path=\"*\" element={
                    <div className=\"flex flex-col items-center justify-center min-h-[60vh] text-center\">
                      <h1 className=\"text-4xl font-bold text-gray-900 dark:text-white mb-4\">
                        404
                      </h1>
                      <p className=\"text-gray-600 dark:text-gray-400 mb-8\">
                        페이지를 찾을 수 없습니다.
                      </p>
                      <a 
                        href=\"/\" 
                        className=\"px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors\"
                      >
                        홈으로 돌아가기
                      </a>
                    </div>
                  } />
                </Routes>
              </Suspense>
            </Layout>
          </div>
          
          {/* Toast notifications */}
          <Toaster
            position=\"top-right\"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
                borderRadius: '8px',
              },
              success: {
                iconTheme: {
                  primary: '#22c55e',
                  secondary: '#fff',
                },
              },
              error: {
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </Router>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;