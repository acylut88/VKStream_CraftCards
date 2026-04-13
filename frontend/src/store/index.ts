import { create } from 'zustand';
import { User, Analytics, LogEntry } from '../services/api';

interface AppStore {
  users: User[];
  analytics: Analytics | null;
  logs: LogEntry[];
  loading: boolean;
  selectedUserId: string | null;
  notification: { type: 'success' | 'error' | 'info'; message: string } | null;

  // Actions
  setUsers: (users: User[]) => void;
  setAnalytics: (analytics: Analytics | null) => void;
  setLogs: (logs: LogEntry[]) => void;
  setLoading: (loading: boolean) => void;
  selectUser: (vk_id: string | null) => void;
  showNotification: (type: 'success' | 'error' | 'info', message: string) => void;
  clearNotification: () => void;
  updateUser: (user: User) => void;
}

export const useAppStore = create<AppStore>((set) => ({
  users: [],
  analytics: null,
  logs: [],
  loading: false,
  selectedUserId: null,
  notification: null,

  setUsers: (users) => set({ users }),
  setAnalytics: (analytics) => set({ analytics }),
  setLogs: (logs) => set({ logs }),
  setLoading: (loading) => set({ loading }),
  selectUser: (vk_id) => set({ selectedUserId: vk_id }),
  showNotification: (type, message) =>
    set({ notification: { type, message } }),
  clearNotification: () => set({ notification: null }),
  updateUser: (user) =>
    set((state) => ({
      users: state.users.map((u) => (u.vk_id === user.vk_id ? user : u)),
    })),
}));
