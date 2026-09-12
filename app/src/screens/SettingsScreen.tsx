import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  Switch,
  ScrollView,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';
import { useSettingsStore } from '../store/settingsStore';
import { ApiStatusBadge } from '../components/ApiStatusBadge';
import { ApiKeysCard } from '../components/ApiKeysCard';

export const SettingsScreen: React.FC = () => {
  const {
    serverUrl,
    token,
    isConnected,
    whitelist,
    sandbox,
    apiKeysStatus,
    updateServerUrl,
    updateToken,
    checkConnection,
    saveWhitelist,
    saveSandbox,
    fetchSettings,
  } = useSettingsStore();

  const [inputUrl, setInputUrl] = useState(serverUrl);
  const [inputToken, setInputToken] = useState(token);
  const [testingConn, setTestingConn] = useState(false);

  // Whitelist local state
  const [wlActive, setWlActive] = useState(whitelist.active);
  const [wlNumbers, setWlNumbers] = useState(whitelist.allowed_numbers.join(', '));
  const [wlCodes, setWlCodes] = useState(whitelist.allowed_passcodes.join(', '));

  // Sandbox local state
  const [memMb, setMemMb] = useState(String(sandbox.max_memory_mb));
  const [cpuQuota, setCpuQuota] = useState(String(sandbox.cpu_quota));
  const [timeoutSec, setTimeoutSec] = useState(String(sandbox.timeout_seconds));

  const handleTestConnection = async () => {
    setTestingConn(true);
    await updateServerUrl(inputUrl);
    await updateToken(inputToken);
    const ok = await checkConnection();
    setTestingConn(false);
    if (ok) {
      await fetchSettings();
      Alert.alert('Erfolg', 'Verbindung zum MAJE-Server hergestellt!');
    } else {
      Alert.alert('Fehler', 'Konnte keine Verbindung zum MAJE-Server aufbauen.');
    }
  };

  const handleSaveSecurity = async () => {
    await saveWhitelist({
      active: wlActive,
      allowed_numbers: wlNumbers.split(',').map((s) => s.trim()).filter(Boolean),
      allowed_passcodes: wlCodes.split(',').map((s) => s.trim()).filter(Boolean),
    });

    await saveSandbox({
      max_memory_mb: parseInt(memMb, 10) || 512,
      cpu_quota: parseFloat(cpuQuota) || 1.0,
      timeout_seconds: parseInt(timeoutSec, 10) || 60,
      allowed_root: '/maje',
    });

    Alert.alert('Gespeichert', 'Sicherheits- und Sandbox-Einstellungen gespeichert.');
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Einstellungen</Text>
        <View style={styles.statusGroup}>
          <View style={[styles.dot, isConnected ? styles.dotGreen : styles.dotRed]} />
          <Text style={styles.statusLabel}>{isConnected ? 'Verbunden' : 'Getrennt'}</Text>
        </View>
      </View>

      <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
        {/* Server Connection */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>IONOS SERVER VERBINDUNG</Text>
          <Text style={styles.inputLabel}>SERVER URL</Text>
          <TextInput
            style={styles.input}
            value={inputUrl}
            onChangeText={setInputUrl}
            placeholder="http://deine-server-ip:8000"
            placeholderTextColor={Colors.text.muted}
            autoCapitalize="none"
          />

          <Text style={styles.inputLabel}>JWT AUTH TOKEN</Text>
          <TextInput
            style={[styles.input, styles.monoText]}
            value={inputToken}
            onChangeText={setInputToken}
            placeholder="MAJE Bearer Token einfügen..."
            placeholderTextColor={Colors.text.muted}
            secureTextEntry
          />

          <TouchableOpacity
            style={styles.testBtn}
            onPress={handleTestConnection}
            disabled={testingConn}
          >
            {testingConn ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Text style={styles.testBtnText}>Verbindung testen & speichern</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* API Keys Provider Status */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>KONFIGURIERTE KI-MODELLE & KEYS</Text>
          <Text style={styles.cardSubtitle}>
            Keys werden zentral in config/api_keys.py verwaltet.
          </Text>
          <View style={styles.badgeWrap}>
            {apiKeysStatus && apiKeysStatus.length > 0 ? (
              apiKeysStatus.map((item, idx) => (
                <ApiStatusBadge
                  key={idx}
                  provider={item.provider}
                  configured={item.configured}
                />
              ))
            ) : (
              <Text style={styles.emptyNote}>Keine Statusinformationen verfügbar.</Text>
            )}
          </View>
        </View>

        {/* Central API-Key management */}
        <ApiKeysCard />

        {/* Whitelist Security */}
        <View style={styles.card}>
          <View style={styles.rowBetween}>
            <Text style={styles.cardTitle}>ZUGRIFFS-WHITELIST</Text>
            <Switch
              value={wlActive}
              onValueChange={setWlActive}
              trackColor={{ false: Colors.border.strong, true: Colors.accent.primary }}
              thumbColor="#ffffff"
            />
          </View>

          <Text style={styles.inputLabel}>ERLAUBTE TELEFONNUMMERN (KOMMAGETRENNT)</Text>
          <TextInput
            style={styles.input}
            value={wlNumbers}
            onChangeText={setWlNumbers}
            placeholder="+491701234567, +491719876543"
            placeholderTextColor={Colors.text.muted}
          />

          <Text style={styles.inputLabel}>ERLAUBTE PASSCODES / TOKENS</Text>
          <TextInput
            style={styles.input}
            value={wlCodes}
            onChangeText={setWlCodes}
            placeholder="maje-master-passcode-1234"
            placeholderTextColor={Colors.text.muted}
          />
        </View>

        {/* Sandbox Limits */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>DOCKER SANDBOX RESSOURCEN-LIMITS</Text>

          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>Max. RAM (MB)</Text>
            <TextInput
              style={styles.numberInput}
              value={memMb}
              onChangeText={setMemMb}
              keyboardType="number-pad"
            />
          </View>

          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>CPU Quota (Cores)</Text>
            <TextInput
              style={styles.numberInput}
              value={cpuQuota}
              onChangeText={setCpuQuota}
              keyboardType="decimal-pad"
            />
          </View>

          <View style={styles.settingRow}>
            <Text style={styles.settingLabel}>Befehls-Timeout (Sekunden)</Text>
            <TextInput
              style={styles.numberInput}
              value={timeoutSec}
              onChangeText={setTimeoutSec}
              keyboardType="number-pad"
            />
          </View>

          <TouchableOpacity style={styles.saveBtn} onPress={handleSaveSecurity}>
            <Text style={styles.saveBtnText}>Sicherheits-Limits speichern</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: Colors.bg.base,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.subtle,
    backgroundColor: Colors.bg.surface,
  },
  headerTitle: {
    color: Colors.text.primary,
    fontSize: Typography.size.base,
    fontWeight: '600',
  },
  statusGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
  },
  dotGreen: {
    backgroundColor: Colors.accent.success,
  },
  dotRed: {
    backgroundColor: Colors.accent.error,
  },
  statusLabel: {
    color: Colors.text.secondary,
    fontSize: Typography.size.xs,
  },
  content: {
    flex: 1,
  },
  scrollContent: {
    padding: Spacing.md,
    paddingBottom: Spacing.huge,
  },
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
  },
  inputLabel: {
    color: Colors.text.secondary,
    fontSize: Typography.size.xs,
    marginTop: Spacing.xs,
    marginBottom: 4,
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
  monoText: {
    fontFamily: Typography.family.mono,
  },
  testBtn: {
    backgroundColor: Colors.accent.primary,
    paddingVertical: Spacing.sm,
    borderRadius: Spacing.radius.sm,
    alignItems: 'center',
    marginTop: Spacing.xs,
  },
  testBtnText: {
    color: '#fff',
    fontSize: Typography.size.xs,
    fontWeight: '600',
  },
  badgeWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.xs,
  },
  emptyNote: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs,
    fontStyle: 'italic',
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: Spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.subtle,
  },
  settingLabel: {
    color: Colors.text.secondary,
    fontSize: Typography.size.sm,
  },
  numberInput: {
    backgroundColor: Colors.bg.base,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
    borderRadius: Spacing.radius.sm,
    color: Colors.text.primary,
    fontFamily: Typography.family.mono,
    fontSize: Typography.size.sm,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    width: 80,
    textAlign: 'right',
  },
  saveBtn: {
    backgroundColor: Colors.bg.overlay,
    borderWidth: 1,
    borderColor: Colors.border.strong,
    paddingVertical: Spacing.sm,
    borderRadius: Spacing.radius.sm,
    alignItems: 'center',
    marginTop: Spacing.md,
  },
  saveBtnText: {
    color: Colors.text.primary,
    fontSize: Typography.size.xs,
    fontWeight: '600',
  },
});
