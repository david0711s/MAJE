/**
 * MAJE – Speech (Text-to-Speech) helper
 * Uses on-device TTS (expo-speech) on native and the Web Speech API in the browser.
 * Completely free – no cloud calls.
 */
let ExpoSpeech: any = null;
try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  ExpoSpeech = require('expo-speech');
} catch {
  ExpoSpeech = null;
}

export function isTtsAvailable(): boolean {
  if (ExpoSpeech) return true;
  return typeof globalThis !== 'undefined' && !!(globalThis as any).speechSynthesis;
}

/** Strip markdown/code so TTS sounds natural. */
export function cleanForSpeech(text: string): string {
  return (text || '')
    .replace(/```[\s\S]*?```/g, ' (Codeblock ) ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/[*_#>~]/g, '')
    .replace(/\[(.*?)\]\((.*?)\)/g, '$1')
    .replace(/\n{2,}/g, '. ')
    .slice(0, 800)
    .trim();
}

export function speak(text: string, language: string = 'de-DE'): void {
  const clean = cleanForSpeech(text);
  if (!clean) return;
  try {
    if (ExpoSpeech) {
      ExpoSpeech.speak(clean, { language, rate: 1.0, pitch: 1.0 });
      return;
    }
    const synth = (globalThis as any).speechSynthesis;
    if (synth) {
      synth.cancel();
      const utter = new (globalThis as any).SpeechSynthesisUtterance(clean);
      utter.lang = language;
      synth.speak(utter);
    }
  } catch {
    // ignore – TTS is a nice-to-have
  }
}

export function stopSpeaking(): void {
  try {
    if (ExpoSpeech) {
      ExpoSpeech.stop();
      return;
    }
    (globalThis as any).speechSynthesis?.cancel();
  } catch {
    // ignore
  }
}
