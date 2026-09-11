import { create } from 'zustand';
import { api, getServerUrl, setServerUrl, getToken, setToken } from '../api/client';

interface WhitelistConfig {
  active: boolean;
  allowed_numbers: string[];
  allowed_passcodes: string[];
}

interface SandboxConfig {
  max_memory_mb: number;
  cpu_quota: number;
  timeout_seconds: number;
  allowed_root: string;
}

interface SettingsState {
  serverUrl: string;
  token: string;
  isConnected: boolean;
  whitelist: WhitelistConfig;
  sandbox: SandboxConfig;
  apiKeysStatus: Array<{ provider: string; configured: boolean }>;
  isLoading: boolean;
  error: string | null;

  initSettings: () => Promise<void>;
  updateServerUrl: (url: string) => Promise<void>;
  updateToken: (token: string) => Promise<void>;
  checkConnection: () => Promise<boolean>;
  fetchSettings: () => Promise<void>;
  saveWhitelist: (whitelist: WhitelistConfig) => Promise<void>;
  saveSandbox: (sandbox: SandboxConfig) => Promise<void>;
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  serverUrl: 'http://localhost:8000',
  token: '',
  isConnected: false,
  whitelist: {
    active: true,
    allowed_numbers: [],
    allowed_passcodes: [],
  },
  sandbox: {
    max_memory_mb: 512,
    cpu_quota: 1.0,
    timeout_seconds: 60,
    allowed_root: '/maje',
  },
  apiKeysStatus: [],
  isLoading: false,
  error: null,

  initSettings: async () => {
    const url = await getServerUrl();
    const token = (await getToken()) || '';
    set({ serverUrl: url, token });
    await get().checkConnection();
    if (get().isConnected) {
      await get().fetchSettings();
    }
  },

  updateServerUrl: async (url: string) => {
    const cleanUrl = url.trim().replace(/\/$/, '');
    await setServerUrl(cleanUrl);
    set({ serverUrl: cleanUrl });
    await get().checkConnection();
  },

  updateToken: async (token: string) => {
    const cleanToken = token.trim();
    await setToken(cleanToken);
    set({ token: cleanToken });
    await get().checkConnection();
  },

  checkConnection: async () => {
    try {
      await api.get('/settings/');
      set({ isConnected: true, error: null });
      return true;
    } catch {
      set({ isConnected: false });
      return false;
    }
  },

  fetchSettings: async () => {
    set({ isLoading: true });
    try {
      const data = await api.get('/settings/');
      if (data) {
        set({
          whitelist: data.whitelist || get().whitelist,
          sandbox: data.sandbox || get().sandbox,
          apiKeysStatus: data.api_keys_status || [],
          isLoading: false,
        });
      }
    } catch (err: any) {
      set({
        error: err?.response?.data?.detail || 'Fehler beim Laden der Einstellungen',
        isLoading: false,
      });
    }
  },

  saveWhitelist: async (whitelist: WhitelistConfig) => {
    try {
      await api.post('/settings/whitelist', whitelist);
      set({ whitelist });
    } catch (err: any) {
      set({ error: err?.response?.data?.detail || 'Whitelist konnte nicht gespeichert werden' });
    }
  },

  saveSandbox: async (sandbox: SandboxConfig) => {
    try {
      await api.post('/settings/sandbox', sandbox);
      set({ sandbox });
    } catch (err: any) {
      set({ error: err?.response?.data?.detail || 'Sandbox-Limits konnten nicht gespeichert werden' });
    }
  },
}));
