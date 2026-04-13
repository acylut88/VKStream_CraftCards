import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8001',
  headers: {
    'Content-Type': 'application/json'
  }
});

export interface User {
  vk_id: string;
  nickname: string;
  stars: number;
  pa_charges: number;
  pa_active_today: number;
  std_boxes_today: number;
  elite_boxes_today: number;
  ac_balance: number;
  ac_today: number;
}

export interface LogEntry {
  timestamp: string;
  nickname: string;
  box_type: string;
  count: number;
  rare_drops: string;
  merges: string;
  ac_won: number;
}

export interface Analytics {
  total_users: number;
  active_users: number;
  total_boxes: number;
  box_stats: { std_count: number; elite_count: number };
  total_ac: number;
  avg_boxes_per_user: number;
  avg_ac_per_user: number;
  top_players: Array<{ nickname: string; ac: number; boxes: number }>;
  logs_count: number;
}

// Users
export const getUsers = () => API.get<User[]>('/api/users');
export const getUser = (vk_id: string) => API.get<User>(`/api/users/${vk_id}`);
export const updateUser = (vk_id: string, data: Partial<User>) =>
  API.post(`/api/users/${vk_id}/update`, data);
export const deleteUser = (vk_id: string) => API.delete(`/api/users/${vk_id}`);

// Boxes
export const giveBoxes = (vk_id: string, count: number, rarity: number, nickname?: string) =>
  API.post(`/api/users/${vk_id}/boxes`, { vk_id, nickname, count, rarity });

// Inventory
export const getUserInventory = (vk_id: string) =>
  API.get(`/api/users/${vk_id}/inventory`);

// Analytics
export const getAnalytics = () => API.get<Analytics>('/api/analytics');
export const getTimeline = (days?: number) =>
  API.get('/api/stats/timeline', { params: { days } });

// Logs
export const getLogs = (limit?: number) =>
  API.get<LogEntry[]>('/api/logs', { params: { limit } });

// Stream
export const finishStream = () => API.post('/api/stream/finish');
export const clearAllData = () => API.post('/api/stream/clear-all');

export default API;
