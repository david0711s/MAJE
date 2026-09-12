import React, { useCallback, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Platform,
  StyleSheet,
  Text,
  TouchableOpacity,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';
import { transcribeAudio } from '../api/client';

// expo-audio is included in Expo Go. Load defensively so a missing module
// never crashes the app (e.g. on web where we use the Web Speech API instead).
let AudioMod: any = null;
try {
  AudioMod = require('expo-audio');
} catch {
  AudioMod = null;
}

interface VoiceControlsProps {
  onTranscript: (text: string) => void;
  disabled?: boolean;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({ onTranscript, disabled }) => {
  // Hook order is stable: AudioMod never changes at runtime.
  const recorder = AudioMod?.useAudioRecorder
    ? AudioMod.useAudioRecorder(AudioMod.RecordingPresets?.HIGH_QUALITY)
    : null;

  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const recognitionRef = useRef<any>(null);

  const webSpeech =
    Platform.OS === 'web' &&
    typeof globalThis !== 'undefined' &&
    !!((globalThis as any).SpeechRecognition || (globalThis as any).webkitSpeechRecognition);

  const startWeb = () => {
    const SR = (globalThis as any).SpeechRecognition || (globalThis as any).webkitSpeechRecognition;
    const rec = new SR();
    rec.lang = 'de-DE';
    rec.continuous = false;
    rec.interimResults = false;
    rec.onresult = (e: any) => {
      const t = e.results?.[0]?.[0]?.transcript || '';
      if (t) onTranscript(t);
    };
    rec.onerror = () => setRecording(false);
    rec.onend = () => setRecording(false);
    recognitionRef.current = rec;
    rec.start();
    setRecording(true);
  };

  const stopWeb = () => {
    recognitionRef.current?.stop?.();
    setRecording(false);
  };

  const startNative = async () => {
    if (!AudioMod || !recorder) {
      Alert.alert(
        'Spracheingabe',
        'Aufnahmen sind hier nicht verfügbar. Nutze die Web-App (PWA) oder einen Dev-Build für die Sprachsteuerung.',
      );
      return;
    }
    try {
      const perm = await AudioMod.AudioModule?.requestRecordingPermissionsAsync?.();
      if (perm && perm.granted === false) {
        Alert.alert('Mikrofon', 'Berechtigung verweigert.');
        return;
      }
      await AudioMod.setAudioModeAsync?.({ allowsRecording: true, playsInSilentMode: true });
      await recorder.prepareToRecordAsync();
      recorder.record();
      setRecording(true);
    } catch (e: any) {
      Alert.alert('Fehler', e?.message || 'Aufnahme konnte nicht gestartet werden.');
    }
  };

  const stopNative = async () => {
    setBusy(true);
    try {
      await recorder?.stop?.();
      const uri = recorder?.uri;
      setRecording(false);
      if (uri) {
        const res = await transcribeAudio(uri, 'voice.m4a', 'audio/m4a', 'de');
        if (res?.text) onTranscript(res.text);
      }
    } catch (e: any) {
      Alert.alert('Transkription', e?.response?.data?.detail || e?.message || 'Transkription fehlgeschlagen.');
    } finally {
      setBusy(false);
    }
  };

  const toggle = useCallback(() => {
    if (busy) return;
    if (recording) {
      if (Platform.OS === 'web' && webSpeech) stopWeb();
      else stopNative();
    } else if (Platform.OS === 'web' && webSpeech) {
      startWeb();
    } else {
      startNative();
    }
  }, [recording, busy, webSpeech]);

  return (
    <TouchableOpacity
      style={[styles.button, recording && styles.buttonActive]}
      onPress={toggle}
      disabled={disabled || busy}
      activeOpacity={0.8}
    >
      {busy ? (
        <ActivityIndicator size="small" color="#fff" />
      ) : (
        <Text style={styles.icon}>{recording ? '⏹' : '🎤'}</Text>
      )}
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  button: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: Colors.bg.overlay,
    borderWidth: 1,
    borderColor: Colors.border.strong,
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonActive: {
    backgroundColor: Colors.accent.error,
    borderColor: Colors.accent.error,
  },
  icon: {
    fontSize: 18,
    color: Colors.text.primary,
  },
});
