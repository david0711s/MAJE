import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';
import { api } from '../api/client';
import { useChatStore } from '../store/chatStore';

interface UIElement {
  id: string;
  element_type: 'button' | 'card' | 'stat' | 'text' | 'action';
  title: string;
  description?: string;
  payload?: any;
  created_at?: string;
}

export const MAJEScreen: React.FC<{ onNavigateToChat?: () => void }> = ({ onNavigateToChat }) => {
  const [elements, setElements] = useState<UIElement[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const sendMessage = useChatStore((s) => s.sendMessage);

  const fetchElements = async () => {
    setIsLoading(true);
    try {
      const data = await api.get('/ui/');
      const list = Array.isArray(data) ? data : Array.isArray(data?.elements) ? data.elements : [];
      setElements(list);
    } catch (e) {
      console.error('Failed to load MAJE UI elements:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchElements();
  }, []);

  const handleElementAction = async (el: UIElement) => {
    const prompt = el.payload?.prompt || `Führe die MAJE-Aktion aus: ${el.title}`;
    Alert.alert(
      'Aktion ausführen',
      `Möchtest du "${el.title}" an MAJE übergeben?`,
      [
        { text: 'Abbrechen', style: 'cancel' },
        {
          text: 'Ausführen',
          onPress: async () => {
            onNavigateToChat?.();
            await sendMessage(prompt);
          },
        },
      ]
    );
  };

  const handleClearElements = async () => {
    try {
      await api.delete('/ui/');
      setElements([]);
    } catch (e) {
      Alert.alert('Fehler', 'Konnte Dashboard nicht leeren.');
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <View>
          <Text style={styles.headerTitle}>Für MAJE Dashboard</Text>
          <Text style={styles.headerSubtitle}>Von MAJE selbst erstellte Widgets & Aktionen</Text>
        </View>
        <TouchableOpacity style={styles.refreshBtn} onPress={fetchElements}>
          <Text style={styles.refreshBtnText}>↻</Text>
        </TouchableOpacity>
      </View>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.accent.primary} />
        </View>
      ) : elements.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.emptyIcon}>✨</Text>
          <Text style={styles.emptyTitle}>Noch keine Widgets erstellt</Text>
          <Text style={styles.emptySubtitle}>
            MAJE kann selbstständig UI-Elemente, Shortcuts und Widgets hier ablegen, wenn er Tools wie "add_ui_button" nutzt.
          </Text>
        </View>
      ) : (
        <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
          <View style={styles.grid}>
            {elements.map((el, idx) => (
              <TouchableOpacity
                key={el.id || String(idx)}
                style={[
                  styles.elementCard,
                  el.element_type === 'action' && styles.actionCard,
                  el.element_type === 'stat' && styles.statCard,
                ]}
                onPress={() => handleElementAction(el)}
                activeOpacity={0.7}
              >
                <View style={styles.cardTop}>
                  <Text style={styles.cardType}>{(el.element_type || 'button').toUpperCase()}</Text>
                  <Text style={styles.cardArrow}>›</Text>
                </View>

                <Text style={styles.cardTitle}>{el.title || '(ohne Titel)'}</Text>

                {el.description && (
                  <Text style={styles.cardDesc} numberOfLines={3}>
                    {el.description}
                  </Text>
                )}
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity style={styles.clearBtn} onPress={handleClearElements}>
            <Text style={styles.clearBtnText}>Alle Widgets entfernen</Text>
          </TouchableOpacity>
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
  headerSubtitle: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs - 2,
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
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing.xl,
  },
  emptyIcon: {
    fontSize: 40,
    marginBottom: Spacing.sm,
  },
  emptyTitle: {
    color: Colors.text.primary,
    fontSize: Typography.size.md,
    fontWeight: '600',
    marginBottom: Spacing.xs,
  },
  emptySubtitle: {
    color: Colors.text.muted,
    fontSize: Typography.size.sm,
    textAlign: 'center',
    lineHeight: 20,
  },
  content: {
    flex: 1,
  },
  scrollContent: {
    padding: Spacing.md,
    paddingBottom: Spacing.huge,
  },
  grid: {
    gap: Spacing.sm,
  },
  elementCard: {
    backgroundColor: Colors.bg.surface,
    borderRadius: Spacing.radius.md,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
  },
  actionCard: {
    borderColor: 'rgba(99, 102, 241, 0.4)',
    backgroundColor: 'rgba(99, 102, 241, 0.05)',
  },
  statCard: {
    borderColor: 'rgba(56, 189, 248, 0.4)',
  },
  cardTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  cardType: {
    color: Colors.accent.primary,
    fontSize: Typography.size.xs - 2,
    fontFamily: Typography.family.mono,
    fontWeight: '700',
  },
  cardArrow: {
    color: Colors.text.muted,
    fontSize: Typography.size.md,
  },
  cardTitle: {
    color: Colors.text.primary,
    fontSize: Typography.size.base,
    fontWeight: '600',
    marginBottom: Spacing.xxs,
  },
  cardDesc: {
    color: Colors.text.secondary,
    fontSize: Typography.size.xs,
    lineHeight: 18,
  },
  clearBtn: {
    marginTop: Spacing.xl,
    paddingVertical: Spacing.sm,
    alignItems: 'center',
  },
  clearBtnText: {
    color: Colors.accent.error,
    fontSize: Typography.size.xs,
    fontWeight: '600',
  },
});
