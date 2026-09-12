import { useEffect } from 'react';
import { majeWS } from '../api/websocket';
import { useChatStore } from './chatStore';
import { useSettingsStore } from './settingsStore';

export * from './chatStore';
export * from './taskStore';
export * from './settingsStore';

/**
 * Global hook to initialize WebSocket and route events into Zustand stores.
 */
export function useInitializeMAJE() {
  const initSettings = useSettingsStore((s) => s.initSettings);
  const applyAgentEvent = useChatStore((s) => s.applyAgentEvent);

  useEffect(() => {
    // 1. Load initial settings, then connect the WebSocket
    initSettings().then(() => {
      majeWS.connect();
    });

    // 2. Route every backend event (reasoning/action/observation/completed/…) into the store
    const handleEvent = (event: any) => {
      applyAgentEvent(event);
    };

    majeWS.on('*', handleEvent);

    return () => {
      majeWS.off('*', handleEvent);
      majeWS.disconnect();
    };
  }, []);
}
