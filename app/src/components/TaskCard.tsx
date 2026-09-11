import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';
import { TaskItem } from '../store/taskStore';
import { formatEUR, formatRelativeTime } from '../utils/format';

interface TaskCardProps {
  task: TaskItem;
  onPress: () => void;
}

export const TaskCard: React.FC<TaskCardProps> = ({ task, onPress }) => {
  const getStatusColor = () => {
    switch (task.status) {
      case 'running':
        return Colors.accent.info;
      case 'completed':
        return Colors.accent.success;
      case 'failed':
        return Colors.accent.error;
      case 'stopped':
        return Colors.text.muted;
      default:
        return Colors.accent.warning;
    }
  };

  const statusColor = getStatusColor();

  return (
    <TouchableOpacity style={styles.card} onPress={onPress} activeOpacity={0.7}>
      <View style={styles.topRow}>
        <View style={[styles.statusBadge, { borderColor: statusColor, backgroundColor: `${statusColor}1A` }]}>
          <View style={[styles.statusDot, { backgroundColor: statusColor }]} />
          <Text style={[styles.statusText, { color: statusColor }]}>{task.status.toUpperCase()}</Text>
        </View>

        <Text style={styles.timeText}>{formatRelativeTime(task.created_at)}</Text>
      </View>

      <Text style={styles.description} numberOfLines={2}>
        {task.description}
      </Text>

      <View style={styles.footer}>
        <View style={styles.metaGroup}>
          <Text style={styles.modeTag}>{task.mode?.toUpperCase() || 'AGENT'}</Text>
          {task.steps_count !== undefined && (
            <Text style={styles.stepInfo}>{task.steps_count} Schritte</Text>
          )}
        </View>

        {task.total_cost_eur !== undefined && (
          <Text style={styles.costText}>{formatEUR(task.total_cost_eur)}</Text>
        )}
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.bg.surface,
    borderRadius: Spacing.radius.md,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.xs + 2,
    paddingVertical: 2,
    borderRadius: Spacing.radius.full,
    borderWidth: 1,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 4,
  },
  statusText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  timeText: {
    fontSize: Typography.size.xs,
    color: Colors.text.muted,
  },
  description: {
    fontSize: Typography.size.base,
    fontFamily: Typography.family.sans,
    color: Colors.text.primary,
    lineHeight: 20,
    marginBottom: Spacing.sm,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: Colors.border.subtle,
    paddingTop: Spacing.xs,
  },
  metaGroup: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs + 2,
  },
  modeTag: {
    color: Colors.accent.primary,
    fontSize: Typography.size.xs - 1,
    fontFamily: Typography.family.mono,
    fontWeight: '600',
  },
  stepInfo: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs - 1,
  },
  costText: {
    color: Colors.accent.warning,
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.mono,
    fontWeight: '600',
  },
});
