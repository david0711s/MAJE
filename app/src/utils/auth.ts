/**
 * Auth token management & initial verification.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api, getToken, setToken, setServerUrl, getServerUrl } from '../api/client';

export interface AuthState {
  isAuthenticated: boolean;
  serverUrl: string;
  token: string | null;
}

export async function checkAuthStatus(): Promise<AuthState> {
  const serverUrl = await getServerUrl();
  const token = await getToken();

  if (!token) {
    return { isAuthenticated: false, serverUrl, token: null };
  }

  try {
    // Quick ping to verify token and server connectivity
    await api.get('/settings/');
    return { isAuthenticated: true, serverUrl, token };
  } catch (err: any) {
    // If 401 or network error
    if (err?.response?.status === 401) {
      await AsyncStorage.removeItem('maje_jwt_token');
      return { isAuthenticated: false, serverUrl, token: null };
    }
    // Server might just be down or warming up
    return { isAuthenticated: !!token, serverUrl, token };
  }
}

export async function loginWithToken(token: string, serverUrl?: string): Promise<boolean> {
  if (serverUrl) {
    await setServerUrl(serverUrl.trim().replace(/\/$/, ''));
  }
  await setToken(token.trim());
  return true;
}

export async function logout(): Promise<void> {
  await AsyncStorage.removeItem('maje_jwt_token');
}
