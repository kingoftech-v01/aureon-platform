/**
 * DashboardScreen - Main dashboard with KPI slider and activity list
 * Follows Figma horizontal slider + trending list pattern
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  FlatList,
  RefreshControl,
  Pressable,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';
import { GlassCard } from '@components/glass';
import { Avatar, StatCard, ListItem, CurrencyText, LoadingSpinner } from '@components/common';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { useAuthStore } from '@store/authStore';
import { useDashboardStats, useActivity } from '@hooks/useAnalytics';
import type { DashboardStats, ActivityItem } from '@/types';

const DashboardScreen: React.FC = () => {
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<any>();
  const { user } = useAuthStore();
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useDashboardStats();
  const { data: activity, isLoading: activityLoading, refetch: refetchActivity } = useActivity();
  const [refreshing, setRefreshing] = React.useState(false);

  const onRefresh = async () => {
    setRefreshing(true);
    await Promise.all([refetchStats(), refetchActivity()]);
    setRefreshing(false);
  };

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  const formatAmount = (amount?: number) => {
    if (!amount) return '$0';
    if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`;
    if (amount >= 1000) return `$${(amount / 1000).toFixed(1)}K`;
    return `$${amount.toFixed(0)}`;
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'payment': return 'card-outline';
      case 'invoice': return 'receipt-outline';
      case 'contract': return 'document-text-outline';
      case 'client': return 'person-add-outline';
      default: return 'notifications-outline';
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'payment': return colors.success;
      case 'invoice': return colors.warning;
      case 'contract': return colors.primary[500];
      case 'client': return colors.accent[500];
      default: return colors.info;
    }
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={{ paddingBottom: 100 }}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header */}
      <View style={[styles.header, { paddingTop: insets.top + 16 }]}>
        <View>
          <Text style={styles.greeting}>{getGreeting()},</Text>
          <Text style={styles.userName}>{user?.first_name || 'User'}</Text>
        </View>
        <Avatar name={user?.full_name} src={user?.avatar} size="md" />
      </View>

      {/* KPI Horizontal Slider (Figma card slider pattern) */}
      <View style={styles.section}>
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.sliderContent}
        >
          <StatCard
            title="Revenue"
            value={formatAmount(stats?.total_revenue)}
            subtitle={`${stats?.revenue_growth ?? 0}% growth`}
            icon={<Icon name="trending-up" size={20} color={colors.success} />}
            accentColor={colors.success}
          />
          <StatCard
            title="Clients"
            value={String(stats?.total_clients ?? 0)}
            subtitle={`${stats?.client_growth ?? 0}% growth`}
            icon={<Icon name="people" size={20} color={colors.primary[500]} />}
            accentColor={colors.primary[500]}
          />
          <StatCard
            title="Pending"
            value={String(stats?.pending_invoices ?? 0)}
            subtitle="invoices"
            icon={<Icon name="time" size={20} color={colors.warning} />}
            accentColor={colors.warning}
          />
          <StatCard
            title="Contracts"
            value={String(stats?.active_contracts ?? 0)}
            subtitle="active"
            icon={<Icon name="document-text" size={20} color={colors.accent[500]} />}
            accentColor={colors.accent[500]}
          />
        </ScrollView>
      </View>

      {/* Quick Actions */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Actions</Text>
        <View style={styles.quickActions}>
          {[
            { icon: 'person-add-outline', label: 'Client', color: colors.primary[500], onPress: () => navigation.navigate('ClientsTab', { screen: 'ClientCreate' }) },
            { icon: 'document-text-outline', label: 'Contract', color: colors.accent[500], onPress: () => navigation.navigate('InvoicesTab', { screen: 'ContractCreate' }) },
            { icon: 'receipt-outline', label: 'Invoice', color: colors.warning, onPress: () => navigation.navigate('InvoicesTab', { screen: 'InvoiceCreate' }) },
            { icon: 'bar-chart-outline', label: 'Reports', color: colors.info, onPress: () => navigation.navigate('AnalyticsTab') },
          ].map((action) => (
            <Pressable key={action.label} style={styles.quickAction} onPress={action.onPress}>
              <GlassCard preset="cardSmall" style={styles.actionCard}>
                <View style={styles.actionContent}>
                  <View style={[styles.actionIcon, { backgroundColor: action.color + '20' }]}>
                    <Icon name={action.icon} size={22} color={action.color} />
                  </View>
                  <Text style={styles.actionLabel}>{action.label}</Text>
                </View>
              </GlassCard>
            </Pressable>
          ))}
        </View>
      </View>

      {/* Recent Activity (Figma trending list pattern) */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Recent Activity</Text>
          <Pressable>
            <Icon name="ellipsis-horizontal" size={24} color={colors.text.muted} />
          </Pressable>
        </View>

        {activityLoading ? (
          <LoadingSpinner size="small" />
        ) : (
          <GlassCard preset="cardSolid">
            <View>
              {(activity || []).slice(0, 8).map((item: ActivityItem, index: number) => (
                <View key={item.id || index}>
                  <ListItem
                    title={item.description}
                    subtitle={new Date(item.created_at).toLocaleDateString()}
                    left={
                      <View
                        style={[
                          styles.activityIcon,
                          { backgroundColor: getActivityColor(item.type) + '20' },
                        ]}
                      >
                        <Icon
                          name={getActivityIcon(item.type)}
                          size={18}
                          color={getActivityColor(item.type)}
                        />
                      </View>
                    }
                    rightText={
                      item.amount
                        ? `${item.currency || '$'}${item.amount.toLocaleString()}`
                        : undefined
                    }
                  />
                  {index < (activity || []).slice(0, 8).length - 1 && (
                    <View style={styles.divider} />
                  )}
                </View>
              ))}
              {(!activity || activity.length === 0) && (
                <View style={styles.emptyActivity}>
                  <Text style={styles.emptyText}>No recent activity</Text>
                </View>
              )}
            </View>
          </GlassCard>
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background.primary,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingBottom: 16,
  },
  greeting: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    color: colors.text.secondary,
  },
  userName: {
    fontFamily: fontFamily.bold,
    fontSize: fontSize['3xl'],
    color: colors.text.primary,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  sectionTitle: {
    fontFamily: fontFamily.semiBold,
    fontSize: fontSize.xl,
    color: colors.text.primary,
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  sliderContent: {
    paddingHorizontal: 20,
  },
  quickActions: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    gap: 10,
  },
  quickAction: {
    flex: 1,
  },
  actionCard: {},
  actionContent: {
    alignItems: 'center',
    padding: 14,
  },
  actionIcon: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  actionLabel: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.sm,
    color: colors.text.primary,
  },
  activityIcon: {
    width: 40,
    height: 40,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  divider: {
    height: 1,
    backgroundColor: colors.figma.lighterElements + '40',
    marginHorizontal: 16,
  },
  emptyActivity: {
    padding: 32,
    alignItems: 'center',
  },
  emptyText: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    color: colors.text.muted,
  },
});

export default DashboardScreen;
