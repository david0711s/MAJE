/**
 * MAJE API Client
 * Axios instance with JWT auth header.
 */
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL_KEY = 'maje_server_url';
const TOKEN_KEY    = 'maje_jwt_token';

// Kann beim (Web-)Build vorbelegt werden, damit die Server-URL nicht getippt werden muss:
//   EXPO_PUBLIC_DEFAULT_SERVER=https://maje-xxxx.ts.net npm run build:web
// (oder in Netlify unter Site configuration -> Environment variables)
export const DEFAULT_SERVER: string =
  process.env.EXPO_PUBLIC_DEFAULT_SERVER || 'http://localhost:8000';

export async function getServerUrl(): Promise<string> {
  return (await AsyncStorage.getItem(BASE_URL_KEY)) ?? DEFAULT_SERVER;
}

export async function setServerUrl(url: string) {
  await AsyncStorage.setItem(BASE_URL_KEY, url);
}

export async function getToken(): Promise<string | null> {
  return AsyncStorage.getItem(TOKEN_KEY);
}

export async function setToken(token: string) {
  await AsyncStorage.setItem(TOKEN_KEY, token);
}

/** Create a fresh axios instance pointing to current server */
export async function getApiClient() {
  // Normalize: strip trailing slashes so "/chat/message" never becomes "//chat/message"
  const base = (await getServerUrl()).replace(/\/+$/, '');
  const token = await getToken();

  return axios.create({
    baseURL: base,
    timeout: 30000,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
}

/** Convenience wrappers */
export const api = {
  async get<T = any>(path: string): Promise<T> {
    const client = await getApiClient();
    const res = await client.get<T>(path);
    return res.data;
  },
  async post<T = any>(path: string, data?: any): Promise<T> {
    const client = await getApiClient();
    const res = await client.post<T>(path, data);
    return res.data;
  },
  async put<T = any>(path: string, data?: any): Promise<T> {
    const client = await getApiClient();
    const res = await client.put<T>(path, data);
    return res.data;
  },
  async delete<T = any>(path: string, config?: any): Promise<T> {
    const client = await getApiClient();
    const res = await client.delete<T>(path, config);
    return res.data;
  },
};

/** Human-friendly error text (incl. network/CORS hints). */
export function describeError(err: any): string {
  const status = err?.response?.status;
  const detail = err?.response?.data?.detail;
  if (status) return `Server-Fehler ${status}${detail ? `: ${detail}` : ''}`;
  const msg = err?.message || '';
  if (msg === 'Network Error' || err?.code === 'ERR_NETWORK') {
    return 'Server nicht erreichbar (Network Error). Prüfe: Server-URL korrekt? Backend läuft? Falls die Seite https ist, muss das Backend auch https sein.';
  }
  return msg || 'Unbekannter Fehler';
}

/**
 * Upload a picked/recorded file to the backend.
 * Works both in React Native (uri) and on web (File object).
 */
export async function uploadFile(
  file: { uri?: string; file?: any; name: string; mimeType?: string },
  subdir: string = 'files',
  taskId?: string,
): Promise<any> {
  const base = await getServerUrl();
  const token = await getToken();

  const form = new FormData();
  if (file.file) {
    // Web: real File object
    form.append('file', file.file, file.name);
  } else {
    // React Native: { uri, name, type }
    form.append('file', {
      uri: file.uri,
      name: file.name,
      type: file.mimeType || 'application/octet-stream',
    } as any);
  }
  form.append('subdir', subdir);
  if (taskId) form.append('task_id', taskId);

  const res = await axios.post(`${base}/files/upload`, form, {
    headers: {
      'Content-Type': 'multipart/form-data',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    timeout: 180000,
  });
  return res.data;
}

/** Transcribe an audio recording via the backend (Groq Whisper, free tier). */
export async function transcribeAudio(
  uri: string,
  name: string = 'recording.m4a',
  mimeType: string = 'audio/m4a',
  language?: string,
): Promise<{ text: string; provider?: string }> {
  const base = await getServerUrl();
  const token = await getToken();

  const form = new FormData();
  form.append('file', { uri, name, type: mimeType } as any);
  if (language) form.append('language', language);

  const res = await axios.post(`${base}/voice/transcribe`, form, {
    headers: {
      'Content-Type': 'multipart/form-data',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    timeout: 120000,
  });
  return res.data;
}

/** Read a text file from the backend for preview. */
export async function readRemoteFile(path: string): Promise<{ content: string; name: string; size: number }> {
  const client = await getApiClient();
  const res = await client.get('/files/view', { params: { path } });
  return res.data;
}

