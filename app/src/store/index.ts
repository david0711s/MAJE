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
  const addWSReasoningStep = useChatStore((s) => s.addWSReasoningStep);
  const finishTaskFromWS = useChatStore((s) => s.finishTaskFromWS);

  useEffect(() => {
    // 1. Load initial settings
    initSettings().then(() => {
      // 2. Connect WebSocket
      majeWS.connect();
    });

    // 3. Register WebSocket handlers
    const handleReasoning = (event: any) => {
      addWSReasoningStep(event);
    };

    const handleTaskFinished = (event: any) => {
      finishTaskFromWS(event);
    };

    majeWS.on('reasoning_step', handleReasoning);
    majeWS.on('task_finished', handleTaskFinished);

    return () => {
      majeWS.off('reasoning_step', handleReasoning);
      majeWS.off('task_finished', handleTaskFinished);
      majeWS.disconnect();
    };
  }, []);
}
