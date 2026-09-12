import React, { useState } from 'react';
import {
  ActivityIndicator,
  ScrollView,
  StyleSheet,
  SafeAreaView,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';
import { useSettingsStore } from '../store/settingsStore';
import { ApiKeysCard } from '../components/ApiKeysCard';

interface SetupScreenProps {
  onDone: () => void;
}

/**
 * Einrichtungs-Assistent: erscheint automatisch, solange keine Verbindung besteht.
 * Schritt 1 = Server-URL + Token, Schritt 2 = API-Keys direkt hier eintragen.
 */
export const SetupScreen: React.FC<SetupScreenProps> = ({ onDone }) => {
  const { serverUrl, token, updateServerUrl, updateToken, checkConnection } = useSettingsStore();

  const [url, setUrl] = useState(serverUrl);
  const [tok, setTok] = useState(token);
  const [busy, setBusy] = useState(false);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConnect = async () => {
    setBusy(true);
    setError(null);
    try {
      await updateServerUrl(url);
      await updateToken(tok);
      const ok = await checkConnection();
      setConnected(ok);
      if (!ok) {
        setError('Verbindung fehlgeschlagen. Läuft das Backend? Stimmt URL & Token?');
      }
    } catch (e: any) {
      setError(e?.message || 'Unbekannter Fehler');
    } finally {
      setBusy(false);
    }
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <Text style={styles.logo}>MAJE</Text>
        <Text style={styles.subtitle}>Einrichtung – in 2 Schritten fertig</Text>

        <View style={styles.card}>
          <Text style={styles.step}>SCHRITT 1 · SERVER VERBINDEN</Text>

          <Text style={styles.label}>SERVER-URL</Text>
          <TextInput
            style={styles.input}
            value={url}
            onChangeText={setUrl}
            autoCapitalize="none"
            autoCorrect={false}
            placeholder="https://maje.deinedomain.de"
            placeholderTextColor={Colors.text.muted}
          />

          <Text style={styles.label}>ZUGANGS-TOKEN</Text>
          <TextInput
            style={styles.input}
            value={tok}
            onChangeText={setTok}
            autoCapitalize="none"
            autoCorrect={false}
            secureTextEntry
            placeholder="JWT-Token einfügen"
            placeholderTextColor={Colors.text.muted}
          />

          <Text style={styles.hint}>
            Token auf dem Server erzeugen:{'\n'}
            curl -s http://127.0.0.1:8000/settings/token
          </Text>

          <TouchableOpacity style={styles.btn} onPress={handleConnect} disabled={busy} activeOpacity={0.8}>
            {busy ? <ActivityIndicator color="#fff" /> : <Text style={styles.btnText}>Verbinden</Text>}
          </TouchableOpacity>

          {connected && <Text style={styles.ok}>✓ Verbunden</Text>}
          {error && <Text style={styles.err}>{error}</Text>}
        </View>

        <View style={styles.card}>
          <Text style={styles.step}>SCHRITT 2 · API-KEYS</Text>
          <Text style={styles.hintSmall}>
            Trage mindestens einen kostenlosen Key ein (Gemini oder Groq). Groq wird zusätzlich
            für die Spracheingabe (Whisper) genutzt. Keys werden sofort übernommen.
          </Text>
          <ApiKeysCard />
        </View>

        <TouchableOpacity onPress={onDone} style={styles.skip} activeOpacity={0.8}>
          <Text style={styles.skipText}>{connected ? 'Weiter zur App →' : 'Später einrichten'}</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.bg.base },
  scroll: { padding: Spacing.md, paddingBottom: Spacing.huge },
  logo: {
    color: Colors.text.primary,
    fontSize: Typography.size.hero,
    fontWeight: '800',
    letterSpacing: 2,
    textAlign: 'center',
    marginTop: Spacing.xl,
  },
  subtitle: {
    color: Colors.text.muted,
    fontSize: Typography.size.sm,
    textAlign: 'center',
    marginBottom: Spacing.lg,
  },
  card: {
    backgroundColor: Colors.bg.surface,
    padding: Spacing.md,
    borderRadius: Spacing.radius.md,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
    marginBottom: Spacing.md,
  },
  step: {
    fontSize: Typography.size.xs - 1,
    color: Colors.accent.primary,
    fontWeight: '700',
    letterSpacing: 0.6,
    marginBottom: Spacing.sm,
  },
  label: {
    color: Colors.text.secondary,
    fontSize: Typography.size.xs,
    marginBottom: 4,
    marginTop: Spacing.xs,
  },
  input: {
    backgroundColor: Colors.bg.base,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
    borderRadius: Spacing.radius.sm,
    color: Colors.text.primary,
    fontSize: Typography.size.sm,
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs + 2,
    marginBottom: Spacing.xs,
  },
  hint: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs - 1,
    fontFamily: Typography.family.mono,
    marginTop: Spacing.xs,
    lineHeight: 15,
  },
  hintSmall: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs,
    marginBottom: Spacing.sm,
    lineHeight: 16,
  },
  btn: {
    backgroundColor: Colors.accent.primary,
    paddingVertical: Spacing.sm,
    borderRadius: Spacing.radius.sm,
    alignItems: 'center',
    marginTop: Spacing.sm,
  },
  btnText: { color: '#fff', fontSize: Typography.size.sm, fontWeight: '700' },
  ok: { color: Colors.accent.success, fontSize: Typography.size.sm, marginTop: Spacing.sm, fontWeight: '600' },
  err: { color: Colors.accent.error, fontSize: Typography.size.xs, marginTop: Spacing.sm, lineHeight: 16 },
  skip: { alignItems: 'center', paddingVertical: Spacing.md },
  skipText: { color: Colors.accent.primary, fontSize: Typography.size.sm, fontWeight: '600' },
});

