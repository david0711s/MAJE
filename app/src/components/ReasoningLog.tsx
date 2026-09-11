import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Colors } from '../theme/colors';
import { Typography } from '../theme/typography';
import { Spacing } from '../theme/spacing';

interface ReasoningStep {
  iteration: number;
  thought?: string;
  action?: string;
  action_input?: any;
  observation?: string;
  timestamp?: string;
}

interface ReasoningLogProps {
  steps: ReasoningStep[];
  defaultExpanded?: boolean;
}

export const ReasoningLog: React.FC<ReasoningLogProps> = ({ steps, defaultExpanded = false }) => {
  const [expanded, setExpanded] = useState(defaultExpanded);

  if (!steps || steps.length === 0) return null;

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={styles.header}
        onPress={() => setExpanded(!expanded)}
        activeOpacity={0.7}
      >
        <View style={styles.headerLeft}>
          <Text style={styles.stepBadge}>{steps.length} Schritte</Text>
          <Text style={styles.headerTitle}>ReAct Reasoning Log</Text>
        </View>
        <Text style={styles.expandIcon}>{expanded ? '▾' : '▸'}</Text>
      </TouchableOpacity>

      {expanded && (
        <View style={styles.stepsList}>
          {steps.map((step, idx) => (
            <View key={idx} style={styles.stepCard}>
              <View style={styles.stepHeader}>
                <Text style={styles.iterationText}>Iter #{step.iteration || idx + 1}</Text>
                {step.action && (
                  <View style={styles.actionBadge}>
                    <Text style={styles.actionText}>{step.action}</Text>
                  </View>
                )}
              </View>

              {step.thought && (
                <View style={styles.section}>
                  <Text style={styles.sectionLabel}>THOUGHT:</Text>
                  <Text style={styles.thoughtText}>{step.thought}</Text>
                </View>
              )}

              {step.action_input && (
                <View style={styles.section}>
                  <Text style={styles.sectionLabel}>INPUT:</Text>
                  <Text style={styles.codeText}>
                    {typeof step.action_input === 'object'
                      ? JSON.stringify(step.action_input, null, 2)
                      : String(step.action_input)}
                  </Text>
                </View>
              )}

              {step.observation && (
                <View style={styles.section}>
                  <Text style={styles.sectionLabel}>OBSERVATION:</Text>
                  <Text style={styles.obsText} numberOfLines={8}>
                    {step.observation}
                  </Text>
                </View>
              )}
            </View>
          ))}
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.bg.elevated,
    borderRadius: Spacing.radius.md,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
    marginVertical: Spacing.xs,
    overflow: 'hidden',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    backgroundColor: Colors.bg.surface,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  stepBadge: {
    backgroundColor: Colors.accent.primaryMuted,
    color: Colors.accent.primary,
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.mono,
    paddingHorizontal: Spacing.xs + 2,
    paddingVertical: 2,
    borderRadius: Spacing.radius.sm,
    marginRight: Spacing.sm,
    fontWeight: '600',
  },
  headerTitle: {
    color: Colors.text.secondary,
    fontSize: Typography.size.sm,
    fontFamily: Typography.family.sans,
    fontWeight: '500',
  },
  expandIcon: {
    color: Colors.text.muted,
    fontSize: Typography.size.md,
  },
  stepsList: {
    padding: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Colors.border.subtle,
  },
  stepCard: {
    backgroundColor: Colors.bg.base,
    borderRadius: Spacing.radius.sm,
    padding: Spacing.sm,
    marginBottom: Spacing.xs,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
  },
  stepHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  iterationText: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.mono,
  },
  actionBadge: {
    backgroundColor: 'rgba(56, 189, 248, 0.15)',
    paddingHorizontal: Spacing.xs + 2,
    paddingVertical: 1,
    borderRadius: Spacing.radius.sm,
  },
  actionText: {
    color: Colors.accent.info,
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.mono,
    fontWeight: '600',
  },
  section: {
    marginTop: Spacing.xxs,
  },
  sectionLabel: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs - 2,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  thoughtText: {
    color: Colors.text.secondary,
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.sans,
    lineHeight: 16,
  },
  codeText: {
    color: Colors.accent.warning,
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.mono,
    backgroundColor: 'rgba(0,0,0,0.3)',
    padding: Spacing.xs,
    borderRadius: Spacing.radius.sm,
  },
  obsText: {
    color: Colors.text.primary,
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.mono,
    backgroundColor: 'rgba(0,0,0,0.3)',
    padding: Spacing.xs,
    borderRadius: Spacing.radius.sm,
  },
});
