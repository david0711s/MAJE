import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  Switch,
  TouchableOpacity,
  ScrollView,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';
import { api } from '../api/client';
import { formatEUR } from '../utils/format';

export const AutonomyScreen: React.FC = () => {
  const [isActive, setIsActive] = useState(false);
  const [currentFocus, setCurrentFocus] = useState('');
  const [dailyLimitEur, setDailyLimitEur] = useState('2.00');
  const [intervalMinutes, setIntervalMinutes] = useState('30');
  const [logs, setLogs] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);

  const fetchAutonomyState = async () => {
    setIsLoading(true);
    try {
      const data = await api.get('/autonomy/status');
      if (data) {
        setIsActive(!!data.is_running);
        setCurrentFocus(data.current_focus || '');
        setDailyLimitEur(String(data.cost_limit_eur || 2.0));
        setIntervalMinutes(String(data.interval_minutes || 30));
        setLogs(data.history || []);
      }
    } catch (e) {
      console.error('Failed to load autonomy state:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAutonomyState();
  }, []);

  const handleToggleAutonomy = async (value: boolean) => {
    setIsUpdating(true);
    try {
      if (value) {
        await api.post('/autonomy/start', {
          focus: currentFocus,
          cost_limit_eur: parseFloat(dailyLimitEur) || 2.0,
          interval_minutes: parseInt(intervalMinutes, 10) || 30,
        });
        setIsActive(true);
      } else {
        await api.post('/autonomy/stop');
        setIsActive(false);
      }
      fetchAutonomyState();
    } catch (e: any) {
      Alert.alert('Fehler', e?.response?.data?.detail || 'Konnte Autonomie-Modus nicht umschalten.');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleUpdateFocus = async () => {
    try {
      await api.post('/autonomy/focus', { focus: currentFocus });
      Alert.alert('Aktualisiert', 'Autonomer Fokus wurde für MAJE aktualisiert.');
    } catch (e: any) {
      Alert.alert('Fehler', 'Konnte Fokus nicht speichern.');
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Autonomie-Modus (Hintergrund)</Text>
        <TouchableOpacity style={styles.refreshBtn} onPress={fetchAutonomyState}>
          <Text style={styles.refreshBtnText}>↻</Text>
        </TouchableOpacity>
      </View>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.accent.primary} />
        </View>
      ) : (
        <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
          {/* Active Switch Card */}
          <View style={[styles.card, isActive && styles.activeCard]}>
            <View style={styles.switchRow}>
              <View style={styles.switchInfo}>
                <Text style={styles.switchTitle}>Autonome Ausführung</Text>
                <Text style={styles.switchDesc}>
                  MAJE analysiert regelmäßig Ziele, lernt und optimiert das System selbstständig.
                </Text>
              </View>
              <Switch
                value={isActive}
                onValueChange={handleToggleAutonomy}
                trackColor={{ false: Colors.border.strong, true: Colors.accent.primary }}
                thumbColor="#ffffff"
                disabled={isUpdating}
              />
            </View>
          </View>

          {/* Current Focus Card */}
          <View style={styles.card}>
            <Text style={styles.sectionLabel}>AKTUELLER FOKUS / ZIEL</Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              value={currentFocus}
              onChangeText={setCurrentFocus}
              placeholder="z.B. Erforsche Sicherheitslücken im Heimnetzwerk oder optimiere Python-Skripte..."
              placeholderTextColor={Colors.text.muted}
              multiline
              numberOfLines={3}
            />
            <TouchableOpacity style={styles.focusBtn} onPress={handleUpdateFocus}>
              <Text style={styles.focusBtnText}>Fokus an MAJE übermitteln</Text>
            </TouchableOpacity>
          </View>

          {/* Limits & Intervals */}
          <View style={styles.card}>
            <Text style={styles.sectionLabel}>SICHERHEITS-LIMITS</Text>
            <View style={styles.settingRow}>
              <Text style={styles.settingLabel}>Kostenlimit / Tag (€)</Text>
              <TextInput
                style={styles.numberInput}
                value={dailyLimitEur}
                onChangeText={setDailyLimitEur}
                keyboardType="decimal-pad"
              />
            </View>

            <View style={styles.settingRow}>
              <Text style={styles.settingLabel}>Prüfintervall (Minuten)</Text>
              <TextInput
                style={styles.numberInput}
                value={intervalMinutes}
                onChangeText={setIntervalMinutes}
                keyboardType="number-pad"
              />
            </View>
          </View>

          {/* Activity Log */}
          <Text style={styles.historyTitle}>Letzte autonome Aktionen:</Text>
          {logs.length === 0 ? (
            <Text style={styles.emptyLogs}>Noch keine autonomen Aktionen aufgezeichnet.</Text>
          ) : (
            logs.map((item, idx) => (
              <View key={idx} style={styles.logCard}>
                <View style={styles.logHeader}>
                  <Text style={styles.logAction}>{item.action || 'Iteration'}</Text>
                  <Text style={styles.logTime}>{item.timestamp || ''}</Text>
                </View>
                <Text style={styles.logDetail}>{item.summary || item.result || ''}</Text>
              </View>
            ))
          )}
        </ScrollView>
      )}
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
  refreshBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.bg.overlay,
    justifyContent: 'center',
    alignItems: 'center',
  },
  refreshBtnText: {
    color: Colors.text.primary,
    fontSize: 16,
  },
  content: {
    flex: 1,
  },
  scrollContent: {
    padding: Spacing.md,
    paddingBottom: Spacing.huge,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  card: {
    backgroundColor: Colors.bg.surface,
    padding: Spacing.md,
    borderRadius: Spacing.radius.md,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
    marginBottom: Spacing.md,
  },
  activeCard: {
    borderColor: 'rgba(99, 102, 241, 0.4)',
    backgroundColor: 'rgba(99, 102, 241, 0.05)',
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  switchInfo: {
    flex: 1,
    marginRight: Spacing.md,
  },
  switchTitle: {
    color: Colors.text.primary,
    fontSize: Typography.size.base,
    fontWeight: '600',
    marginBottom: 2,
  },
  switchDesc: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs,
    lineHeight: 16,
  },
  sectionLabel: {
    fontSize: Typography.size.xs - 1,
    color: Colors.text.muted,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: Spacing.xs,
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
  },
  textArea: {
    minHeight: 60,
    textAlignVertical: 'top',
  },
  focusBtn: {
    backgroundColor: Colors.accent.primary,
    paddingVertical: Spacing.xs + 2,
    borderRadius: Spacing.radius.sm,
    alignItems: 'center',
    marginTop: Spacing.sm,
  },
  focusBtnText: {
    color: '#fff',
    fontSize: Typography.size.xs,
    fontWeight: '600',
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: Spacing.xs,
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
    paddingVertical: Spacing.xxs,
    width: 80,
    textAlign: 'right',
  },
  historyTitle: {
    color: Colors.text.secondary,
    fontSize: Typography.size.sm,
    fontWeight: '600',
    marginTop: Spacing.sm,
    marginBottom: Spacing.xs,
  },
  emptyLogs: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs,
    fontStyle: 'italic',
  },
  logCard: {
    backgroundColor: Colors.bg.surface,
    padding: Spacing.sm,
    borderRadius: Spacing.radius.sm,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
    marginBottom: Spacing.xs,
  },
  logHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 2,
  },
  logAction: {
    color: Colors.accent.info,
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.mono,
    fontWeight: '600',
  },
  logTime: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs - 2,
  },
  logDetail: {
    color: Colors.text.primary,
    fontSize: Typography.size.xs,
  },
});
