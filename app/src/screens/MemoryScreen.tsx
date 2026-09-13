import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';
import { api } from '../api/client';
import { formatDateTime } from '../utils/format';

interface MemoryItem {
  id: string;
  content: string;
  tags?: string;
  created_at?: string;
}

export const MemoryScreen: React.FC = () => {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);

  const fetchMemories = async () => {
    setIsLoading(true);
    try {
      const data = await api.get('/soul/memory');
      setMemories(Array.isArray(data?.entries) ? data.entries : []);
    } catch (e) {
      console.error('Failed to load memories:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, []);

  const handleAddMemory = async () => {
    if (!newKey.trim() || !newValue.trim()) return;
    try {
      await api.post('/soul/memory', { content: newValue.trim(), tags: newKey.trim() });
      setNewKey('');
      setNewValue('');
      setShowAddForm(false);
      fetchMemories();
    } catch (e: any) {
      Alert.alert('Fehler', e?.response?.data?.detail || 'Konnte Gedächtniseintrag nicht speichern.');
    }
  };

  const handleDeleteMemory = async (id: string) => {
    try {
      await api.delete(`/soul/memory/${encodeURIComponent(id)}`);
      setMemories((prev) => prev.filter((m) => m.id !== id));
    } catch (e: any) {
      Alert.alert('Fehler', 'Konnte Eintrag nicht löschen.');
    }
  };

  const filteredMemories = memories.filter(
    (m) =>
      (m.content || '').toLowerCase().includes(search.toLowerCase()) ||
      (m.tags || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Langzeitgedächtnis ({memories.length})</Text>
        <TouchableOpacity
          style={styles.addBtn}
          onPress={() => setShowAddForm(!showAddForm)}
        >
          <Text style={styles.addBtnText}>{showAddForm ? '✕ Schließen' : '+ Neuer Eintrag'}</Text>
        </TouchableOpacity>
      </View>

      {/* Add Memory Modal/Box */}
      {showAddForm && (
        <View style={styles.addForm}>
          <Text style={styles.formTitle}>Neuen Fakt für MAJE speichern</Text>
          <TextInput
            style={styles.input}
            placeholder="Schlüssel / Thema (z.B. user_birthday)"
            placeholderTextColor={Colors.text.muted}
            value={newKey}
            onChangeText={setNewKey}
          />
          <TextInput
            style={[styles.input, styles.textArea]}
            placeholder="Inhalt / Information (z.B. David hat am 15. März Geburtstag)"
            placeholderTextColor={Colors.text.muted}
            value={newValue}
            onChangeText={setNewValue}
            multiline
          />
          <TouchableOpacity style={styles.submitBtn} onPress={handleAddMemory}>
            <Text style={styles.submitBtnText}>In Gedächtnis einprägen</Text>
          </TouchableOpacity>
        </View>
      )}

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Gedächtnis durchsuchen..."
          placeholderTextColor={Colors.text.muted}
          value={search}
          onChangeText={setSearch}
        />
      </View>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.accent.primary} />
        </View>
      ) : filteredMemories.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.emptyText}>Keine passenden Gedächtniseinträge vorhanden.</Text>
        </View>
      ) : (
        <FlatList
          data={filteredMemories}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          renderItem={({ item }) => (
            <View style={styles.memoryCard}>
              <View style={styles.cardHeader}>
                <Text style={styles.memoryKey}>{item.tags || 'Notiz'}</Text>
                <TouchableOpacity onPress={() => handleDeleteMemory(item.id)}>
                  <Text style={styles.deleteIcon}>✕</Text>
                </TouchableOpacity>
              </View>
              <Text style={styles.memoryValue}>{item.content}</Text>
              {item.created_at && (
                <Text style={styles.memoryDate}>{formatDateTime(item.created_at)}</Text>
              )}
            </View>
          )}
        />
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
  addBtn: {
    backgroundColor: Colors.accent.primary,
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    borderRadius: Spacing.radius.sm,
  },
  addBtnText: {
    color: '#fff',
    fontSize: Typography.size.xs,
    fontWeight: '600',
  },
  addForm: {
    backgroundColor: Colors.bg.surface,
    padding: Spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.subtle,
  },
  formTitle: {
    color: Colors.text.primary,
    fontSize: Typography.size.sm,
    fontWeight: '600',
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
    marginBottom: Spacing.xs,
  },
  textArea: {
    minHeight: 60,
    textAlignVertical: 'top',
  },
  submitBtn: {
    backgroundColor: Colors.accent.primary,
    paddingVertical: Spacing.xs + 2,
    borderRadius: Spacing.radius.sm,
    alignItems: 'center',
    marginTop: Spacing.xs,
  },
  submitBtnText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: Typography.size.xs,
  },
  searchContainer: {
    padding: Spacing.sm,
    backgroundColor: Colors.bg.surface,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.subtle,
  },
  searchInput: {
    backgroundColor: Colors.bg.base,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
    borderRadius: Spacing.radius.md,
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    color: Colors.text.primary,
    fontSize: Typography.size.sm,
  },
  list: {
    padding: Spacing.md,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyText: {
    color: Colors.text.muted,
    fontSize: Typography.size.sm,
  },
  memoryCard: {
    backgroundColor: Colors.bg.surface,
    borderRadius: Spacing.radius.md,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
    marginBottom: Spacing.sm,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  memoryKey: {
    color: Colors.accent.info,
    fontFamily: Typography.family.mono,
    fontSize: Typography.size.sm,
    fontWeight: '600',
  },
  deleteIcon: {
    color: Colors.text.muted,
    fontSize: 14,
    padding: 2,
  },
  memoryValue: {
    color: Colors.text.primary,
    fontSize: Typography.size.sm,
    lineHeight: 20,
  },
  memoryDate: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs - 2,
    marginTop: Spacing.xs,
  },
});
