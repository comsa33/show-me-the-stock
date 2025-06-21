import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface UIState {
  sidebarOpen: boolean;
  mobileMenuOpen: boolean;
  searchModalOpen: boolean;
  settingsModalOpen: boolean;
  
  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleMobileMenu: () => void;
  setMobileMenuOpen: (open: boolean) => void;
  toggleSearchModal: () => void;
  setSearchModalOpen: (open: boolean) => void;
  toggleSettingsModal: () => void;
  setSettingsModalOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      mobileMenuOpen: false,
      searchModalOpen: false,
      settingsModalOpen: false,
      
      toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      
      toggleMobileMenu: () => set((state) => ({ mobileMenuOpen: !state.mobileMenuOpen })),
      setMobileMenuOpen: (open) => set({ mobileMenuOpen: open }),
      
      toggleSearchModal: () => set((state) => ({ searchModalOpen: !state.searchModalOpen })),
      setSearchModalOpen: (open) => set({ searchModalOpen: open }),
      
      toggleSettingsModal: () => set((state) => ({ settingsModalOpen: !state.settingsModalOpen })),
      setSettingsModalOpen: (open) => set({ settingsModalOpen: open }),
    }),
    {
      name: 'ui-store',
      partialize: (state) => ({ 
        sidebarOpen: state.sidebarOpen 
      }),
    }
  )
);