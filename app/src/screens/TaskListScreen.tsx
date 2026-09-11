import React, { useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';
import { useTaskStore } from '../store/taskStore';
import { TaskCard } from '../components/TaskCard';

interface TaskListScreenProps {
  onSelectTask: (taskId: string) => void;
}

export const TaskListScreen: React.FC<TaskListScreenProps> = ({ onSelectTask }) => {
  const { tasks, fetchTasks, isLoading } = useTaskStore();

  useEffect(() => {
    fetchTasks();
  }, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Tasks & Agenten-Logs ({tasks.length})</Text>
        <TouchableOpacity style={styles.refreshBtn} onPress={fetchTasks}>
          <Text style={styles.refreshText}>↻</Text>
        </TouchableOpacity>
      </View>

      {isLoading && tasks.length === 0 ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.accent.primary} />
        </View>
      ) : tasks.length === 0 ? (
        <View style={styles.center}>
          <Text style={styles.emptyIcon}>📋</Text>
          <Text style={styles.emptyTitle}>Keine Tasks vorhanden</Text>
          <Text style={styles.emptySubtitle}>
            Starte im Chat-Modus eine Aufgabe mit "⚡ Agent", um autonome ReAct-Abläufe auszulösen.
          </Text>
        </View>
      ) : (
        <FlatList
          data={tasks}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.list}
          renderItem={({ item }) => (
            <TaskCard task={item} onPress={() => onSelectTask(item.id)} />
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
  refreshBtn: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: Colors.bg.overlay,
    justifyContent: 'center',
    alignItems: 'center',
  },
  refreshText: {
    color: Colors.text.primary,
    fontSize: 16,
  },
  list: {
    padding: Spacing.md,
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
});
