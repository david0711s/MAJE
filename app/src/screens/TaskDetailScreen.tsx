import React, { useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  ActivityIndicator,
} from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';
import { useTaskStore } from '../store/taskStore';
import { ReasoningLog } from '../components/ReasoningLog';
import { formatEUR, formatDateTime } from '../utils/format';

interface TaskDetailScreenProps {
  taskId: string;
  onBack: () => void;
}

export const TaskDetailScreen: React.FC<TaskDetailScreenProps> = ({ taskId, onBack }) => {
  const { currentTask, fetchTaskDetail, stopTask, deleteTask, isLoading } = useTaskStore();

  useEffect(() => {
    fetchTaskDetail(taskId);
    const interval = setInterval(() => {
      fetchTaskDetail(taskId);
    }, 2000);
    return () => clearInterval(interval);
  }, [taskId]);

  const task = currentTask;

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack} style={styles.backButton}>
          <Text style={styles.backText}>‹ Zurück</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle} numberOfLines={1}>
          Task #{taskId.slice(0, 8)}
        </Text>
        <View style={styles.headerActions}>
          {task?.status === 'running' && (
            <TouchableOpacity
              style={styles.stopButton}
              onPress={() => stopTask(taskId)}
            >
              <Text style={styles.stopText}>STOP</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {isLoading && !task ? (
        <View style={styles.loaderCenter}>
          <ActivityIndicator size="large" color={Colors.accent.primary} />
        </View>
      ) : !task ? (
        <View style={styles.loaderCenter}>
          <Text style={styles.emptyText}>Task nicht gefunden.</Text>
        </View>
      ) : (
        <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
          {/* Status Header Banner */}
          <View style={styles.summaryCard}>
            <View style={styles.statusRow}>
              <View
                style={[
                  styles.statusBadge,
                  task.status === 'completed'
                    ? styles.statusGreen
                    : task.status === 'running'
                    ? styles.statusBlue
                    : styles.statusRed,
                ]}
              >
                <Text style={styles.statusBadgeText}>{task.status.toUpperCase()}</Text>
              </View>

              <Text style={styles.modeText}>{task.mode.toUpperCase()} MODE</Text>
            </View>

            <Text style={styles.taskDesc}>{task.description}</Text>

            <View style={styles.statsGrid}>
              <View style={styles.statItem}>
                <Text style={styles.statLabel}>Erstellt</Text>
                <Text style={styles.statValue}>{formatDateTime(task.created_at)}</Text>
              </View>

              <View style={styles.statItem}>
                <Text style={styles.statLabel}>Kosten</Text>
                <Text style={styles.statValue}>
                  {formatEUR(task.total_cost_eur || 0)}
                </Text>
              </View>

              <View style={styles.statItem}>
                <Text style={styles.statLabel}>Schritte</Text>
                <Text style={styles.statValue}>
                  {task.steps?.length || task.steps_count || 0}
                </Text>
              </View>
            </View>
          </View>

          {/* Final Result / Error */}
          {task.result && (
            <View style={styles.resultCard}>
              <Text style={styles.sectionTitle}>Ergebnis:</Text>
              <Text style={styles.resultText}>{task.result}</Text>
            </View>
          )}

          {task.error && (
            <View style={styles.errorCard}>
              <Text style={styles.errorTitle}>Fehler:</Text>
              <Text style={styles.errorText}>{task.error}</Text>
            </View>
          )}

          {/* Reasoning Steps */}
          <Text style={styles.sectionTitle}>ReAct Iterationen:</Text>
          {task.steps && task.steps.length > 0 ? (
            <ReasoningLog steps={task.steps} defaultExpanded={true} />
          ) : (
            <Text style={styles.emptySteps}>Keine Schritte aufgezeichnet.</Text>
          )}

          <TouchableOpacity
            style={styles.deleteButton}
            onPress={async () => {
              await deleteTask(taskId);
              onBack();
            }}
          >
            <Text style={styles.deleteText}>Task löschen</Text>
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
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: Colors.border.subtle,
    backgroundColor: Colors.bg.surface,
  },
  backButton: {
    paddingVertical: Spacing.xs,
  },
  backText: {
    color: Colors.accent.primary,
    fontSize: Typography.size.base,
    fontWeight: '600',
  },
  headerTitle: {
    fontSize: Typography.size.base,
    color: Colors.text.primary,
    fontWeight: '600',
    fontFamily: Typography.family.mono,
  },
  headerActions: {
    width: 60,
    alignItems: 'flex-end',
  },
  stopButton: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xxs + 2,
    borderRadius: Spacing.radius.sm,
  },
  stopText: {
    color: Colors.accent.error,
    fontSize: Typography.size.xs,
    fontWeight: '700',
  },
  loaderCenter: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emptyText: {
    color: Colors.text.muted,
    fontSize: Typography.size.sm,
  },
  content: {
    flex: 1,
  },
  scrollContent: {
    padding: Spacing.md,
    paddingBottom: Spacing.huge,
  },
  summaryCard: {
    backgroundColor: Colors.bg.surface,
    borderRadius: Spacing.radius.md,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
    marginBottom: Spacing.md,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  statusBadge: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: Spacing.radius.full,
  },
  statusGreen: {
    backgroundColor: 'rgba(34, 197, 94, 0.2)',
  },
  statusBlue: {
    backgroundColor: 'rgba(56, 189, 248, 0.2)',
  },
  statusRed: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
  },
  statusBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: Colors.text.primary,
  },
  modeText: {
    color: Colors.accent.primary,
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.mono,
  },
  taskDesc: {
    color: Colors.text.primary,
    fontSize: Typography.size.md,
    fontWeight: '500',
    marginVertical: Spacing.sm,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderTopWidth: 1,
    borderTopColor: Colors.border.subtle,
    paddingTop: Spacing.sm,
  },
  statItem: {
    alignItems: 'flex-start',
  },
  statLabel: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs - 2,
    marginBottom: 2,
  },
  statValue: {
    color: Colors.text.secondary,
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.mono,
  },
  sectionTitle: {
    color: Colors.text.secondary,
    fontSize: Typography.size.sm,
    fontWeight: '600',
    marginVertical: Spacing.xs,
  },
  resultCard: {
    backgroundColor: 'rgba(34, 197, 94, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(34, 197, 94, 0.2)',
    borderRadius: Spacing.radius.md,
    padding: Spacing.md,
    marginBottom: Spacing.md,
  },
  resultText: {
    color: Colors.text.primary,
    fontSize: Typography.size.sm,
    lineHeight: 20,
    marginTop: Spacing.xs,
  },
  errorCard: {
    backgroundColor: 'rgba(239, 68, 68, 0.05)',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.2)',
    borderRadius: Spacing.radius.md,
    padding: Spacing.md,
    marginBottom: Spacing.md,
  },
  errorTitle: {
    color: Colors.accent.error,
    fontSize: Typography.size.sm,
    fontWeight: '600',
  },
  errorText: {
    color: Colors.accent.error,
    fontSize: Typography.size.sm,
    marginTop: Spacing.xs,
  },
  emptySteps: {
    color: Colors.text.muted,
    fontSize: Typography.size.sm,
    fontStyle: 'italic',
    marginVertical: Spacing.sm,
  },
  deleteButton: {
    marginTop: Spacing.xl,
    padding: Spacing.md,
    borderRadius: Spacing.radius.md,
    borderWidth: 1,
    borderColor: Colors.border.strong,
    alignItems: 'center',
  },
  deleteText: {
    color: Colors.accent.error,
    fontSize: Typography.size.sm,
    fontWeight: '600',
  },
});
