import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
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

export const SoulScreen: React.FC = () => {
  const [name, setName] = useState('MAJE');
  const [persona, setPersona] = useState('');
  const [tone, setTone] = useState('');
  const [coreValues, setCoreValues] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const fetchSoul = async () => {
    setIsLoading(true);
    try {
      const data = await api.get('/soul/');
      if (data) {
        setName(data.name || 'MAJE');
        setPersona(data.persona || '');
        setTone(data.tone || 'Präzise, hilfsbereit, proaktiv');
        setCoreValues(
          Array.isArray(data.core_values)
            ? data.core_values.join(', ')
            : data.core_values || ''
        );
        setSystemPrompt(data.custom_instructions || '');
      }
    } catch (e) {
      console.error('Failed to load soul:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSoul();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const valuesArray = coreValues
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);

      await api.post('/soul/', {
        name,
        persona,
        tone,
        core_values: valuesArray,
        custom_instructions: systemPrompt,
      });
      Alert.alert('Gespeichert', 'MAJEs Persönlichkeit ("Soul") wurde erfolgreich aktualisiert.');
    } catch (e: any) {
      Alert.alert('Fehler', e?.response?.data?.detail || 'Konnte Soul nicht speichern.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>MAJE Soul & Persönlichkeit</Text>
        <TouchableOpacity
          style={[styles.saveBtn, isSaving && styles.btnDisabled]}
          onPress={handleSave}
          disabled={isSaving}
        >
          {isSaving ? (
            <ActivityIndicator size="small" color="#fff" />
          ) : (
            <Text style={styles.saveBtnText}>Speichern</Text>
          )}
        </TouchableOpacity>
      </View>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.accent.primary} />
        </View>
      ) : (
        <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
          <View style={styles.card}>
            <Text style={styles.fieldLabel}>NAME DES AGENTEN</Text>
            <TextInput
              style={styles.input}
              value={name}
              onChangeText={setName}
              placeholder="MAJE"
              placeholderTextColor={Colors.text.muted}
            />
          </View>

          <View style={styles.card}>
            <Text style={styles.fieldLabel}>TONFALL & STIL</Text>
            <TextInput
              style={styles.input}
              value={tone}
              onChangeText={setTone}
              placeholder="z.B. Direkt, professionell, humorvoll"
              placeholderTextColor={Colors.text.muted}
            />
          </View>

          <View style={styles.card}>
            <Text style={styles.fieldLabel}>KERNWERTE (Kommagetrennt)</Text>
            <TextInput
              style={styles.input}
              value={coreValues}
              onChangeText={setCoreValues}
              placeholder="z.B. Autonomie, Datenschutz, Effizienz"
              placeholderTextColor={Colors.text.muted}
            />
          </View>

          <View style={styles.card}>
            <Text style={styles.fieldLabel}>PERSONA BESCHREIBUNG</Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              value={persona}
              onChangeText={setPersona}
              placeholder="Beschreibe MAJEs Identität, Hintergrund und Rolle..."
              placeholderTextColor={Colors.text.muted}
              multiline
              numberOfLines={4}
            />
          </View>

          <View style={styles.card}>
            <Text style={styles.fieldLabel}>BENUTZERDEFINIERTE SYSTEM-PROMPT ANWEISUNGEN</Text>
            <TextInput
              style={[styles.input, styles.textArea, styles.monoText]}
              value={systemPrompt}
              onChangeText={setSystemPrompt}
              placeholder="Zusätzliche permanente Instruktionen für das LLM..."
              placeholderTextColor={Colors.text.muted}
              multiline
              numberOfLines={6}
            />
          </View>
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
  saveBtn: {
    backgroundColor: Colors.accent.primary,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.xs,
    borderRadius: Spacing.radius.sm,
  },
  btnDisabled: {
    opacity: 0.6,
  },
  saveBtnText: {
    color: '#ffffff',
    fontSize: Typography.size.xs,
    fontWeight: '600',
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
  fieldLabel: {
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
    fontSize: Typography.size.base,
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs + 4,
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  monoText: {
    fontFamily: Typography.family.mono,
    fontSize: Typography.size.xs,
  },
});
