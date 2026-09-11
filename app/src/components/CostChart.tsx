import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';
import { formatEUR } from '../utils/format';

interface ModelCostItem {
  model: string;
  cost_eur: number;
  tokens?: number;
}

interface CostChartProps {
  todayTotalEur: number;
  dailyLimitEur: number;
  modelBreakdown: ModelCostItem[];
}

export const CostChart: React.FC<CostChartProps> = ({
  todayTotalEur,
  dailyLimitEur,
  modelBreakdown,
}) => {
  const percentUsed = Math.min(100, (todayTotalEur / (dailyLimitEur || 1)) * 100);

  const getProgressColor = () => {
    if (percentUsed > 90) return Colors.accent.error;
    if (percentUsed > 70) return Colors.accent.warning;
    return Colors.accent.success;
  };

  const progressColor = getProgressColor();

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title}>Kosten heute</Text>
        <Text style={styles.limitText}>Limit: {formatEUR(dailyLimitEur)}/Tag</Text>
      </View>

      <View style={styles.amountRow}>
        <Text style={styles.totalAmount}>{formatEUR(todayTotalEur)}</Text>
        <Text style={[styles.percentBadge, { color: progressColor }]}>
          {percentUsed.toFixed(1)}% verbraucht
        </Text>
      </View>

      {/* Progress Bar */}
      <View style={styles.progressBarTrack}>
        <View
          style={[
            styles.progressBarFill,
            { width: `${percentUsed}%`, backgroundColor: progressColor },
          ]}
        />
      </View>

      {/* Breakdown per model */}
      {modelBreakdown && modelBreakdown.length > 0 && (
        <View style={styles.breakdownList}>
          <Text style={styles.breakdownTitle}>Aufschlüsselung nach Modell:</Text>
          {modelBreakdown.map((item, idx) => {
            const itemPercent = todayTotalEur > 0 ? (item.cost_eur / todayTotalEur) * 100 : 0;
            return (
              <View key={idx} style={styles.breakdownRow}>
                <Text style={styles.modelName} numberOfLines={1}>
                  {item.model}
                </Text>
                <View style={styles.costValues}>
                  <Text style={styles.itemCost}>{formatEUR(item.cost_eur)}</Text>
                  <Text style={styles.itemPercent}>({itemPercent.toFixed(0)}%)</Text>
                </View>
              </View>
            );
          })}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.bg.surface,
    borderRadius: Spacing.radius.lg,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
    marginBottom: Spacing.md,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  title: {
    color: Colors.text.secondary,
    fontSize: Typography.size.sm,
    fontWeight: '500',
  },
  limitText: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.mono,
  },
  amountRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: Spacing.sm,
  },
  totalAmount: {
    color: Colors.text.primary,
    fontSize: Typography.size.xxl,
    fontWeight: '700',
    fontFamily: Typography.family.mono,
  },
  percentBadge: {
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.mono,
    fontWeight: '600',
  },
  progressBarTrack: {
    height: 6,
    backgroundColor: Colors.bg.overlay,
    borderRadius: 3,
    overflow: 'hidden',
    marginBottom: Spacing.md,
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  breakdownList: {
    borderTopWidth: 1,
    borderTopColor: Colors.border.subtle,
    paddingTop: Spacing.sm,
  },
  breakdownTitle: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs,
    marginBottom: Spacing.xs,
    fontWeight: '600',
  },
  breakdownRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 3,
  },
  modelName: {
    color: Colors.text.secondary,
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.mono,
    flex: 1,
  },
  costValues: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  itemCost: {
    color: Colors.text.primary,
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.mono,
  },
  itemPercent: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs - 2,
  },
});
