import { create } from 'zustand';
import { api } from '../api/client';
import { majeWS } from '../api/websocket';

export type ChatMode = 'chat' | 'agent';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  mode?: ChatMode;
  taskId?: string;
  model_used?: string;
  cost_eur?: number;
  tokens?: { prompt: number; completion: number };
  reasoningSteps?: Array<{
    iteration: number;
    thought?: string;
    action?: string;
    action_input?: any;
    observation?: string;
  }>;
}

interface ChatState {
  messages: ChatMessage[];
  mode: ChatMode;
  isLoading: boolean;
  activeTaskId: string | null;
  error: string | null;

  setMode: (mode: ChatMode) => void;
  sendMessage: (text: string) => Promise<void>;
  stopActiveTask: () => Promise<void>;
  clearMessages: () => void;
  addWSReasoningStep: (step: any) => void;
  finishTaskFromWS: (data: any) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hallo David! Ich bin MAJE, dein persönlicher AI-Agent. Wie kann ich dir heute helfen?',
      timestamp: new Date().toISOString(),
      mode: 'chat',
    },
  ],
  mode: 'chat',
  isLoading: false,
  activeTaskId: null,
  error: null,

  setMode: (mode) => set({ mode }),

  clearMessages: () => set({ messages: [] }),

  sendMessage: async (text: string) => {
    if (!text.trim()) return;

    const userMsgId = `msg-${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
      mode: get().mode,
    };

    set((state) => ({
      messages: [...state.messages, userMsg],
      isLoading: true,
      error: null,
    }));

    try {
      if (get().mode === 'chat') {
        // Chat Mode: fast conversational response
        const res = await api.post('/chat/message', { message: text });
        const assistantMsg: ChatMessage = {
          id: `reply-${Date.now()}`,
          role: 'assistant',
          content: res.reply,
          timestamp: new Date().toISOString(),
          mode: 'chat',
          model_used: res.model_used,
          cost_eur: res.cost_eur,
        };
        set((state) => ({
          messages: [...state.messages, assistantMsg],
          isLoading: false,
        }));
      } else {
        // Agent Mode: starts autonomous ReAct loop
        const res = await api.post('/chat/agent', { task: text });
        const taskId = res.task_id;

        const agentMsg: ChatMessage = {
          id: taskId,
          role: 'assistant',
          content: 'Ich analysiere die Aufgabe und beginne mit der Ausführung...',
          timestamp: new Date().toISOString(),
          mode: 'agent',
          taskId,
          reasoningSteps: [],
        };

        set((state) => ({
          messages: [...state.messages, agentMsg],
          activeTaskId: taskId,
          isLoading: true,
        }));

        // Subscribe to WS updates for this task
        majeWS.subscribeTask(taskId);
      }
    } catch (err: any) {
      const errMsg = err?.response?.data?.detail || err?.message || 'Fehler beim Senden der Nachricht';
      set((state) => ({
        error: errMsg,
        isLoading: false,
        activeTaskId: null,
      }));
    }
  },

  stopActiveTask: async () => {
    const taskId = get().activeTaskId;
    if (!taskId) return;
    try {
      await api.delete(`/chat/stop/${taskId}`);
      majeWS.sendStop(taskId);
    } catch (e) {
      console.error('Failed to stop task:', e);
    } finally {
      set({ isLoading: false, activeTaskId: null });
    }
  },

  addWSReasoningStep: (data: any) => {
    const { task_id, step } = data;
    if (!task_id || !step) return;

    set((state) => {
      const messages = state.messages.map((msg) => {
        if (msg.taskId === task_id) {
          const steps = [...(msg.reasoningSteps || []), step];
          return {
            ...msg,
            reasoningSteps: steps,
            content: step.observation
              ? `Letzte Aktion: ${step.action}\n${step.observation.slice(0, 150)}...`
              : `Denke nach: ${step.thought || '...'}`
          };
        }
        return msg;
      });
      return { messages };
    });
  },

  finishTaskFromWS: (data: any) => {
    const { task_id, result, total_cost_eur, error } = data;
    set((state) => {
      const messages = state.messages.map((msg) => {
        if (msg.taskId === task_id) {
          return {
            ...msg,
            content: error ? `Fehler aufgetreten:\n${error}` : (result || 'Aufgabe erfolgreich abgeschlossen.'),
            cost_eur: total_cost_eur,
          };
        }
        return msg;
      });
      return {
        messages,
        isLoading: state.activeTaskId === task_id ? false : state.isLoading,
        activeTaskId: state.activeTaskId === task_id ? null : state.activeTaskId,
      };
    });
  },
}));
