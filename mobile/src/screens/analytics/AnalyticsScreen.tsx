/**
 * AnalyticsScreen - Revenue charts and KPIs with glassmorphism
 */

import React from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl, Dimensions } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Ionicons';
import { GlassCard } from '@components/glass';
import { StatCard, CurrencyText, LoadingSpinner } from '@components/common';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { useDashboardStats, useRevenue } from '@hooks/useAnalytics';

const AnalyticsScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const { data: stats, isLoading, refetch } = useDashboardStats();
  const { data: revenue, refetch: refetchRevenue } = useRevenue();
  const [refreshing, setRefreshing] = React.useState(false);

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([refetch(), refetchRevenue()]);
    setRefreshing(false);
  };

  if (isLoading) return <LoadingSpinner />;

  return (
    <ScrollView
      style={[styles.container, { paddingTop: insets.top }]}
      contentContainerStyle={styles.scrollContent}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    >
      <Text style={styles.pageTitle}>Analytics</Text>

      {/* KPI Cards */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.kpiRow}>
        <StatCard title="Total Revenue" value={`$${((stats?.total_revenue || 0) / 1000).toFixed(1)}K`}
          subtitle={`${stats?.revenue_growth || 0}% growth`}
          icon={<Icon name="trending-up" size={20} color={colors.success} />}
          accentColor={colors.success} />
        <StatCard title="MRR" value={`$${((stats?.monthly_recurring_revenue || 0) / 1000).toFixed(1)}K`}
          subtitle="monthly"
          icon={<Icon name="repeat" size={20} color={colors.primary[500]} />}
          accentColor={colors.primary[500]} />
        <StatCard title="Overdue" value={String(stats?.overdue_invoices || 0)}
          subtitle="invoices"
          icon={<Icon name="alert-circle" size={20} color={colors.danger} />}
          accentColor={colors.danger} />
      </ScrollView>

      {/* Revenue Summary */}
      <GlassCard preset="cardSolid" style={styles.card}>
        <View style={styles.cardContent}>
          <Text style={styles.sectionTitle}>Revenue Overview</Text>
          {revenue && revenue.length > 0 ? (
            <View style={styles.revenueList}>
              {(() => {
                const sliced = revenue.slice(0, 6);
                const maxRevenue = Math.max(...sliced.map(r => r.revenue), 1);
                return sliced.map((item, index) => (
                  <View key={index} style={styles.revenueRow}>
                    <Text style={styles.revenueDate}>{item.date}</Text>
                    <View style={styles.revenueBarContainer}>
                      <View style={[styles.revenueBar, {
                        width: `${Math.min((item.revenue / maxRevenue) * 100, 100)}%`
                      }]} />
                    </View>
                    <CurrencyText amount={item.revenue} size="sm" />
                  </View>
                ));
              })()}
            </View>
          ) : (
            <Text style={styles.noData}>No revenue data yet</Text>
          )}
        </View>
      </GlassCard>

      {/* Summary Stats */}
      <GlassCard preset="cardSolid" style={styles.card}>
        <View style={styles.cardContent}>
          <Text style={styles.sectionTitle}>Summary</Text>
          <View style={styles.summaryGrid}>
            {[
              { label: 'Active Clients', value: stats?.total_clients, icon: 'people', color: colors.primary[500] },
              { label: 'Active Contracts', value: stats?.active_contracts, icon: 'document-text', color: colors.accent[500] },
              { label: 'Pending Invoices', value: stats?.pending_invoices, icon: 'time', color: colors.warning },
              { label: 'Overdue Invoices', value: stats?.overdue_invoices, icon: 'alert-circle', color: colors.danger },
            ].map((item) => (
              <View key={item.label} style={styles.summaryItem}>
                <Icon name={item.icon} size={24} color={item.color} />
                <Text style={styles.summaryValue}>{item.value ?? 0}</Text>
                <Text style={styles.summaryLabel}>{item.label}</Text>
              </View>
            ))}
          </View>
        </View>
      </GlassCard>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background.primary },
  scrollContent: { paddingBottom: 100 },
  pageTitle: { fontFamily: fontFamily.bold, fontSize: fontSize['3xl'], color: colors.text.primary, paddingHorizontal: 20, paddingVertical: 16 },
  kpiRow: { paddingHorizontal: 20, marginBottom: 20 },
  card: { marginHorizontal: 20, marginBottom: 16 },
  cardContent: { padding: 20 },
  sectionTitle: { fontFamily: fontFamily.semiBold, fontSize: fontSize.xl, color: colors.text.primary, marginBottom: 16 },
  revenueList: { gap: 12 },
  revenueRow: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  revenueDate: { fontFamily: fontFamily.medium, fontSize: fontSize.sm, color: colors.text.secondary, width: 80 },
  revenueBarContainer: { flex: 1, height: 8, borderRadius: 4, backgroundColor: colors.figma.lighterElements },
  revenueBar: { height: 8, borderRadius: 4, backgroundColor: colors.primary[400] },
  noData: { fontFamily: fontFamily.regular, fontSize: fontSize.md, color: colors.text.muted, textAlign: 'center', padding: 24 },
  summaryGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 16 },
  summaryItem: { width: '45%', alignItems: 'center', padding: 16, backgroundColor: colors.background.primary, borderRadius: 12 },
  summaryValue: { fontFamily: fontFamily.bold, fontSize: fontSize['2xl'], color: colors.text.primary, marginTop: 8 },
  summaryLabel: { fontFamily: fontFamily.regular, fontSize: fontSize.sm, color: colors.text.secondary, marginTop: 2, textAlign: 'center' },
});

export default AnalyticsScreen;
