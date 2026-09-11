import { create } from 'zustand';
import { api } from '../api/client';

export interface TaskItem {
  id: string;
  description: string;
  mode: 'chat' | 'agent' | 'autonomy';
  status: 'pending' | 'running' | 'completed' | 'failed' | 'stopped';
  created_at: string;
  finished_at?: string;
  total_cost_eur?: number;
  error?: string;
  result?: string;
  steps_count?: number;
  steps?: Array<{
    iteration: number;
    thought?: string;
    action?: string;
    action_input?: any;
    observation?: string;
    timestamp?: string;
  }>;
}

interface TaskState {
  tasks: TaskItem[];
  currentTask: TaskItem | null;
  isLoading: boolean;
  error: string | null;

  fetchTasks: () => Promise<void>;
  fetchTaskDetail: (taskId: string) => Promise<void>;
  stopTask: (taskId: string) => Promise<void>;
  deleteTask: (taskId: string) => Promise<void>;
}

export const useTaskStore = create<TaskState>((set) => ({
  tasks: [],
  currentTask: null,
  isLoading: false,
  error: null,

  fetchTasks: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await api.get('/tasks/');
      set({ tasks: data, isLoading: false });
    } catch (err: any) {
      set({
        error: err?.response?.data?.detail || err?.message || 'Fehler beim Laden der Tasks',
        isLoading: false,
      });
    }
  },

  fetchTaskDetail: async (taskId: string) => {
    set({ isLoading: true, error: null });
    try {
      const data = await api.get(`/tasks/${taskId}`);
      set({ currentTask: data, isLoading: false });
    } catch (err: any) {
      set({
        error: err?.response?.data?.detail || err?.message || 'Fehler beim Laden des Task-Details',
        isLoading: false,
      });
    }
  },

  stopTask: async (taskId: string) => {
    try {
      await api.delete(`/chat/stop/${taskId}`);
      // Refresh task detail and list
      const updated = await api.get(`/tasks/${taskId}`).catch(() => null);
      set((state) => ({
        tasks: state.tasks.map((t) => (t.id === taskId ? { ...t, status: 'stopped' } : t)),
        currentTask: updated || state.currentTask,
      }));
    } catch (e) {
      console.error('Error stopping task:', e);
    }
  },

  deleteTask: async (taskId: string) => {
    try {
      await api.delete(`/tasks/${taskId}`);
      set((state) => ({
        tasks: state.tasks.filter((t) => t.id !== taskId),
        currentTask: state.currentTask?.id === taskId ? null : state.currentTask,
      }));
    } catch (e) {
      console.error('Error deleting task:', e);
    }
  },
}));
