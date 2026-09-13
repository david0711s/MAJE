import React, { useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { api } from '../api/client';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';

interface ProviderInfo {
  provider_id: string;
  name: string;
  label: string;
  configured: boolean;
  count: number;
  keys: string[];
  is_free_tier?: boolean;
  enabled?: boolean;
}

interface EncryptionInfo {
  available: boolean;
  enabled: boolean;
  key_configured: boolean;
}

export const ApiKeysCard: React.FC = () => {
  const [providers, setProviders] = useState<ProviderInfo[]>([]);
  const [encryption, setEncryption] = useState<EncryptionInfo | null>(null);
  const [inputs, setInputs] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  const fetchKeys = async () => {
    setIsLoading(true);
    try {
      const data = await api.get('/settings/keys');
      setProviders(data.providers || []);
      setEncryption(data.encryption || null);
    } catch {
      // server not reachable – leave empty
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchKeys();
  }, []);

  const addKey = async (pid: string) => {
    const raw = (inputs[pid] || '').trim();
    if (!raw) return;
    // Mehrere Keys erlaubt: durch Komma, Semikolon, Leerzeichen oder Zeilenumbruch getrennt
    const keys = raw.split(/[\s,;]+/).map((k) => k.trim()).filter(Boolean);
    if (!keys.length) return;
    setBusy(pid);
    try {
      await api.post('/settings/keys', { provider_id: pid, keys });
      setInputs((s) => ({ ...s, [pid]: '' }));
      await fetchKeys();
    } catch (e: any) {
      Alert.alert('Fehler', e?.response?.data?.detail || 'Key konnte nicht gespeichert werden.');
    } finally {
      setBusy(null);
    }
  };

  const removeKeys = async (pid: string) => {
    try {
      await api.delete(`/settings/keys/${pid}`);
      await fetchKeys();
    } catch {
      Alert.alert('Fehler', 'Löschen fehlgeschlagen.');
    }
  };

  const removeOneKey = async (pid: string, index: number) => {
    try {
      await api.delete(`/settings/keys/${pid}`, { params: { index } });
      await fetchKeys();
    } catch {
      Alert.alert('Fehler', 'Key konnte nicht entfernt werden.');
    }
  };

  const toggleEncryption = async () => {
    if (!encryption) return;
    try {
      await api.post('/settings/keys/encryption', { enabled: !encryption.enabled });
      await fetchKeys();
    } catch (e: any) {
      Alert.alert('Verschlüsselung', e?.response?.data?.detail || 'Fehler');
    }
  };

  const makeKey = async () => {
    try {
      const d = await api.get('/settings/keys/newkey');
      Alert.alert('MAJE_KEYS_KEY', `Diese Zeile in die .env auf dem Server eintragen:\n\n${d.env_line}`);
    } catch (e: any) {
      Alert.alert('Fehler', e?.response?.data?.detail || 'Fehler');
    }
  };

  return (
    <View style={styles.card}>
      <Text style={styles.cardTitle}>API-KEYS (ZENTRAL & SKALIERBAR)</Text>
      <Text style={styles.cardSubtitle}>
        Beliebig viele Keys pro Anbieter – mehrere mit Komma oder neuer Zeile einfügen.
        Sie werden sofort übernommen und sind danach nur als Punkte sichtbar.
      </Text>

      {isLoading ? (
        <ActivityIndicator size="small" color={Colors.accent.primary} />
      ) : (
        providers.map((p) => (
          <View key={p.provider_id} style={styles.providerRow}>
            <View style={styles.providerHeader}>
              <View style={styles.providerInfo}>
                <Text style={styles.providerName}>{p.name}</Text>
                <Text style={[styles.providerState, p.configured ? styles.ok : styles.missing]}>
                  {p.configured ? `● ${p.count} Key(s) gespeichert` : '○ kein Key'}
                </Text>
              </View>
              {p.configured && (
                <TouchableOpacity onPress={() => removeKeys(p.provider_id)} hitSlop={8}>
                  <Text style={styles.remove}>alle ✕</Text>
                </TouchableOpacity>
              )}
            </View>

            {p.configured && (
              <View style={styles.keyList}>
                {p.keys.map((k, i) => (
                  <View key={i} style={styles.keyChip}>
                    <Text style={styles.keyChipText}>
                      Key {i + 1}:  {k}
                    </Text>
                    <TouchableOpacity onPress={() => removeOneKey(p.provider_id, i)} hitSlop={8}>
                      <Text style={styles.keyRemove}>✕</Text>
                    </TouchableOpacity>
                  </View>
                ))}
              </View>
            )}

            <View style={styles.inputRow}>
              <TextInput
                style={[styles.input, styles.inputMulti]}
                value={inputs[p.provider_id] || ''}
                onChangeText={(t) => setInputs((s) => ({ ...s, [p.provider_id]: t }))}
                placeholder={`Key(s) für ${p.name} – mehrere mit Komma oder neuer Zeile`}
                placeholderTextColor={Colors.text.muted}
                autoCapitalize="none"
                autoCorrect={false}
                secureTextEntry
                multiline
              />
              <TouchableOpacity
                style={styles.addBtn}
                onPress={() => addKey(p.provider_id)}
                disabled={busy === p.provider_id}
              >
                {busy === p.provider_id ? (
                  <ActivityIndicator size="small" color="#fff" />
                ) : (
                  <Text style={styles.addBtnText}>+</Text>
                )}
              </TouchableOpacity>
            </View>
          </View>
        ))
      )}

      {encryption && (
        <View style={styles.encBox}>
          <Text style={styles.encText}>
            Datei-Verschlüsselung: {encryption.enabled ? 'AN 🔒' : 'AUS'}
            {!encryption.available ? ' (cryptography fehlt)' : ''}
          </Text>
          <View style={styles.encActions}>
            <TouchableOpacity
              style={styles.encBtn}
              onPress={toggleEncryption}
              disabled={!encryption.available}
            >
              <Text style={styles.encBtnText}>{encryption.enabled ? 'Deaktivieren' : 'Aktivieren'}</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.encBtn} onPress={makeKey}>
              <Text style={styles.encBtnText}>Key erzeugen</Text>
            </TouchableOpacity>
          </View>
          {!encryption.key_configured && (
            <Text style={styles.hint}>
              Für Aktivierung: „Key erzeugen“ → Wert als MAJE_KEYS_KEY in /opt/MAJE/.env eintragen → Container neu starten.
            </Text>
          )}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.bg.surface,
    padding: Spacing.md,
    borderRadius: Spacing.radius.md,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
    marginBottom: Spacing.md,
  },
  cardTitle: {
    fontSize: Typography.size.xs - 1,
    color: Colors.text.muted,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: Spacing.xs,
  },
  cardSubtitle: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs,
    marginBottom: Spacing.sm,
    lineHeight: 16,
  },
  providerRow: {
    borderTopWidth: 1,
    borderTopColor: Colors.border.subtle,
    paddingTop: Spacing.xs,
    marginTop: Spacing.xs,
  },
  providerHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  providerInfo: {
    flex: 1,
  },
  providerName: {
    color: Colors.text.primary,
    fontSize: Typography.size.sm,
    fontWeight: '600',
  },
  providerState: {
    fontSize: Typography.size.xs - 1,
    fontFamily: Typography.family.mono,
  },
  ok: {
    color: Colors.accent.success,
  },
  missing: {
    color: Colors.text.muted,
  },
  remove: {
    color: Colors.accent.error,
    fontSize: 14,
    paddingHorizontal: Spacing.xs,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
    marginTop: Spacing.xs,
  },
  input: {
    flex: 1,
    backgroundColor: Colors.bg.base,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
    borderRadius: Spacing.radius.sm,
    color: Colors.text.primary,
    fontSize: Typography.size.xs,
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs + 2,
  },
  addBtn: {
    width: 36,
    height: 36,
    borderRadius: Spacing.radius.sm,
    backgroundColor: Colors.accent.primary,
    justifyContent: 'center',
    alignItems: 'center',
  },
  addBtnText: {
    color: '#fff',
    fontSize: 20,
    fontWeight: '700',
  },
  encBox: {
    marginTop: Spacing.md,
    paddingTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Colors.border.subtle,
  },
  encText: {
    color: Colors.text.secondary,
    fontSize: Typography.size.xs,
    fontWeight: '600',
  },
  encActions: {
    flexDirection: 'row',
    gap: Spacing.xs,
    marginTop: Spacing.xs,
  },
  encBtn: {
    backgroundColor: Colors.bg.overlay,
    borderWidth: 1,
    borderColor: Colors.border.strong,
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    borderRadius: Spacing.radius.sm,
  },
  encBtnText: {
    color: Colors.text.primary,
    fontSize: Typography.size.xs,
    fontWeight: '600',
  },
  hint: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs - 1,
    marginTop: Spacing.xs,
    lineHeight: 15,
  },
  keyList: {
    marginTop: Spacing.xs,
    gap: 4,
  },
  keyChip: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: Colors.bg.base,
    borderRadius: Spacing.radius.sm,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
  },
  keyChipText: {
    color: Colors.text.secondary,
    fontFamily: Typography.family.mono,
    fontSize: Typography.size.xs,
    flex: 1,
  },
  keyRemove: {
    color: Colors.accent.error,
    fontSize: 13,
    paddingLeft: Spacing.sm,
  },
  inputMulti: {
    minHeight: 40,
    textAlignVertical: 'top',
  },
});

