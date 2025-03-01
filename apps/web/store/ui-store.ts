'use client';

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface SidebarState {
  collapsed: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;
}

interface NotificationState {
  unreadCount: number;
  notifications: Notification[];
  markAsRead: (id: string) => void;
  addNotification: (notification: Notification) => void;
  clearAllNotifications: () => void;
}

interface Notification {
  id: string;
  title: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  read: boolean;
  timestamp: number;
}

interface UIState extends SidebarState, NotificationState {
  isComposerOpen: boolean;
  activeModal: string | null;
  setComposerOpen: (isOpen: boolean) => void;
  openModal: (modalId: string) => void;
  closeModal: () => void;
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      // Sidebar state
      collapsed: false,
      toggleSidebar: () => set((state) => ({ collapsed: !state.collapsed })),
      setSidebarCollapsed: (collapsed) => set({ collapsed }),

      // Notifications state
      unreadCount: 0,
      notifications: [],
      markAsRead: (id) =>
        set((state) => {
          const updatedNotifications = state.notifications.map((notification) =>
            notification.id === id ? { ...notification, read: true } : notification
          );
          const unreadCount = updatedNotifications.filter((n) => !n.read).length;
          return { notifications: updatedNotifications, unreadCount };
        }),
      addNotification: (notification) =>
        set((state) => ({
          notifications: [notification, ...state.notifications].slice(0, 50), // Keep last 50
          unreadCount: state.unreadCount + 1,
        })),
      clearAllNotifications: () => set({ notifications: [], unreadCount: 0 }),

      // Composer & modal state
      isComposerOpen: false,
      activeModal: null,
      setComposerOpen: (isOpen) => set({ isComposerOpen: isOpen }),
      openModal: (modalId) => set({ activeModal: modalId }),
      closeModal: () => set({ activeModal: null }),
    }),
    {
      name: 'maily-ui-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        collapsed: state.collapsed,
        notifications: state.notifications,
        unreadCount: state.unreadCount,
      }),
    }
  )
);
