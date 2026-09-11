/**
 * MAJE API Client
 * Axios instance with JWT auth header.
 */
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL_KEY = 'maje_server_url';
const TOKEN_KEY    = 'maje_jwt_token';

export const DEFAULT_SERVER = 'http://localhost:8000';

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
  const base = await getServerUrl();
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
  async delete<T = any>(path: string): Promise<T> {
    const client = await getApiClient();
    const res = await client.delete<T>(path);
    return res.data;
  },
};
