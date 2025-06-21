import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'light' | 'dark' | 'system';

interface ThemeState {
  theme: Theme;
  actualTheme: 'light' | 'dark';
  
  // Actions
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

// 시스템 테마 감지
const getSystemTheme = (): 'light' | 'dark' => {
  if (typeof window !== 'undefined') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return 'light';
};

// 실제 테마 계산
const getActualTheme = (theme: Theme): 'light' | 'dark' => {
  return theme === 'system' ? getSystemTheme() : theme;
};

// 테마 적용
const applyTheme = (actualTheme: 'light' | 'dark') => {
  if (typeof window !== 'undefined') {
    const root = window.document.documentElement;
    
    if (actualTheme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'system',
      actualTheme: getSystemTheme(),
      
      setTheme: (theme: Theme) => {
        const actualTheme = getActualTheme(theme);
        applyTheme(actualTheme);
        set({ theme, actualTheme });
      },
      
      toggleTheme: () => {
        const currentActualTheme = get().actualTheme;
        const newTheme = currentActualTheme === 'light' ? 'dark' : 'light';
        applyTheme(newTheme);
        set({ theme: newTheme, actualTheme: newTheme });
      },
    }),
    {
      name: 'theme-store',
      onRehydrateStorage: () => (state) => {
        if (state) {
          // 초기화 시 테마 적용
          const actualTheme = getActualTheme(state.theme);
          applyTheme(actualTheme);
          state.actualTheme = actualTheme;
          
          // 시스템 테마 변경 감지
          if (typeof window !== 'undefined' && state.theme === 'system') {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            const handleChange = () => {
              const newActualTheme = getSystemTheme();
              applyTheme(newActualTheme);
              useThemeStore.setState({ actualTheme: newActualTheme });
            };
            
            mediaQuery.addEventListener('change', handleChange);
            
            // 클린업 함수 등록
            return () => mediaQuery.removeEventListener('change', handleChange);
          }
        }
      },
    }
  )
);