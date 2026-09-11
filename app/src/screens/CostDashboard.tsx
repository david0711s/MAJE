import React, { useState, useEffect } from 'react';
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
import { api } from '../api/client';
import { CostChart } from '../components/CostChart';
import { formatEUR } from '../utils/format';

export const CostDashboard: React.FC = () => {
  const [todayData, setTodayData] = useState<any>(null);
  const [monthData, setMonthData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchCosts = async () => {
    setIsLoading(true);
    try {
      const [today, month] = await Promise.all([
        api.get('/costs/today').catch(() => null),
        api.get('/costs/month').catch(() => null),
      ]);
      setTodayData(today);
      setMonthData(month);
    } catch (e) {
      console.error('Error fetching cost metrics:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchCosts();
  }, []);

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Kosten & Token-Verbrauch</Text>
        <TouchableOpacity style={styles.refreshBtn} onPress={fetchCosts}>
          <Text style={styles.refreshBtnText}>↻</Text>
        </TouchableOpacity>
      </View>

      {isLoading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={Colors.accent.primary} />
        </View>
      ) : (
        <ScrollView style={styles.content} contentContainerStyle={styles.scrollContent}>
          {/* Today Cost Card with Visual Chart */}
          <CostChart
            todayTotalEur={todayData?.total_eur || 0}
            dailyLimitEur={todayData?.daily_limit_eur || 5.0}
            modelBreakdown={todayData?.by_model || []}
          />

          {/* Monthly Overview Card */}
          <View style={styles.monthCard}>
            <Text style={styles.monthTitle}>Monatsübersicht</Text>
            <View style={styles.monthRow}>
              <View>
                <Text style={styles.monthAmount}>
                  {formatEUR(monthData?.total_eur || 0)}
                </Text>
                <Text style={styles.monthLimit}>
                  Limit: {formatEUR(monthData?.monthly_limit_eur || 50.0)}
                </Text>
              </View>

              <View style={styles.tokenBox}>
                <Text style={styles.tokenCount}>
                  {(monthData?.total_tokens || 0).toLocaleString()}
                </Text>
                <Text style={styles.tokenLabel}>Tokens gesamt</Text>
              </View>
            </View>
          </View>

          {/* Token Breakdown */}
          <View style={styles.tokenBreakdownCard}>
            <Text style={styles.breakdownHeader}>Token-Verteilung (Heute)</Text>
            <View style={styles.tokenGrid}>
              <View style={styles.tokenCell}>
                <Text style={styles.tokenCellNumber}>
                  {(todayData?.prompt_tokens || 0).toLocaleString()}
                </Text>
                <Text style={styles.tokenCellLabel}>Prompt (Input)</Text>
              </View>

              <View style={styles.tokenCell}>
                <Text style={styles.tokenCellNumber}>
                  {(todayData?.completion_tokens || 0).toLocaleString()}
                </Text>
                <Text style={styles.tokenCellLabel}>Completion (Output)</Text>
              </View>
            </View>
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
  monthCard: {
    backgroundColor: Colors.bg.surface,
    padding: Spacing.md,
    borderRadius: Spacing.radius.lg,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
    marginBottom: Spacing.md,
  },
  monthTitle: {
    color: Colors.text.secondary,
    fontSize: Typography.size.sm,
    fontWeight: '600',
    marginBottom: Spacing.xs,
  },
  monthRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  monthAmount: {
    color: Colors.text.primary,
    fontSize: Typography.size.xl,
    fontFamily: Typography.family.mono,
    fontWeight: '700',
  },
  monthLimit: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs,
    fontFamily: Typography.family.mono,
    marginTop: 2,
  },
  tokenBox: {
    alignItems: 'flex-end',
  },
  tokenCount: {
    color: Colors.accent.info,
    fontSize: Typography.size.lg,
    fontFamily: Typography.family.mono,
    fontWeight: '600',
  },
  tokenLabel: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs - 2,
  },
  tokenBreakdownCard: {
    backgroundColor: Colors.bg.surface,
    padding: Spacing.md,
    borderRadius: Spacing.radius.lg,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
  },
  breakdownHeader: {
    color: Colors.text.secondary,
    fontSize: Typography.size.sm,
    fontWeight: '600',
    marginBottom: Spacing.sm,
  },
  tokenGrid: {
    flexDirection: 'row',
    gap: Spacing.sm,
  },
  tokenCell: {
    flex: 1,
    backgroundColor: Colors.bg.base,
    padding: Spacing.sm,
    borderRadius: Spacing.radius.sm,
    borderWidth: 1,
    borderColor: Colors.border.subtle,
  },
  tokenCellNumber: {
    color: Colors.text.primary,
    fontSize: Typography.size.md,
    fontFamily: Typography.family.mono,
    fontWeight: '600',
    marginBottom: 2,
  },
  tokenCellLabel: {
    color: Colors.text.muted,
    fontSize: Typography.size.xs - 2,
  },
});
