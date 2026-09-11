/**
 * MAJE WebSocket Client
 * Connects to the backend WS endpoint and dispatches live agent events.
 */
import { getServerUrl, getToken } from './client';

type WSEvent = {
  type: string;
  task_id?: string;
  [key: string]: any;
};

type EventHandler = (event: WSEvent) => void;

class MAJEWebSocket {
  private ws: WebSocket | null = null;
  private handlers: Map<string, Set<EventHandler>> = new Map();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private subscribedTaskIds: Set<string> = new Set();
  private connected = false;

  async connect() {
    const base = await getServerUrl();
    const token = await getToken();
    const wsBase = base.replace('http://', 'ws://').replace('https://', 'wss://');
    const url = `${wsBase}/chat/ws${token ? `?token=${token}` : ''}`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.connected = true;
      console.log('[WS] Connected to MAJE backend');
      // Re-subscribe to all tracked tasks
      this.subscribedTaskIds.forEach(id => this._send({ action: 'subscribe', task_id: id }));
      this._emit({ type: 'connected' });
    };

    this.ws.onmessage = (event) => {
      try {
        const data: WSEvent = JSON.parse(event.data);
        this._emit(data);
      } catch {}
    };

    this.ws.onerror = (e) => {
      console.error('[WS] Error:', e);
    };

    this.ws.onclose = () => {
      this.connected = false;
      this._emit({ type: 'disconnected' });
      // Auto-reconnect after 3s
      this.reconnectTimer = setTimeout(() => this.connect(), 3000);
    };
  }

  disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.connected = false;
  }

  subscribeTask(taskId: string) {
    this.subscribedTaskIds.add(taskId);
    this._send({ action: 'subscribe', task_id: taskId });
  }

  sendStop(taskId: string) {
    this._send({ action: 'stop', task_id: taskId });
  }

  on(eventType: string, handler: EventHandler) {
    if (!this.handlers.has(eventType)) this.handlers.set(eventType, new Set());
    this.handlers.get(eventType)!.add(handler);
  }

  off(eventType: string, handler: EventHandler) {
    this.handlers.get(eventType)?.delete(handler);
  }

  private _send(data: object) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  private _emit(event: WSEvent) {
    // Emit to specific type handlers
    this.handlers.get(event.type)?.forEach(h => h(event));
    // Emit to wildcard handlers
    this.handlers.get('*')?.forEach(h => h(event));
  }

  get isConnected() {
    return this.connected;
  }
}

// Singleton
export const majeWS = new MAJEWebSocket();
