/**
 * PaymentListScreen - Payment history with glassmorphism
 */

import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, RefreshControl } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Ionicons';
import { useQuery } from '@tanstack/react-query';
import { GlassCard } from '@components/glass';
import { Badge, ListItem, EmptyState, LoadingSpinner } from '@components/common';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { paymentService } from '@services/paymentService';
import type { Payment } from '@/types';

const PaymentListScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const [refreshing, setRefreshing] = useState(false);
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['payments'],
    queryFn: () => paymentService.getPayments({ page: 1, page_size: 50 }),
  });

  const onRefresh = async () => { setRefreshing(true); await refetch(); setRefreshing(false); };

  const getStatusVariant = (status: string) => {
    const map: Record<string, any> = { succeeded: 'success', pending: 'warning', processing: 'info', failed: 'danger', refunded: 'default' };
    return map[status] || 'default';
  };

  const renderPayment = useCallback(({ item }: { item: Payment }) => (
    <ListItem
      title={`$${item.amount.toLocaleString()}`}
      subtitle={`${item.payment_number} · ${new Date(item.created_at).toLocaleDateString()}`}
      left={
        <View style={[styles.paymentIcon, { backgroundColor: item.status === 'succeeded' ? colors.success + '20' : colors.warning + '20' }]}>
          <Icon name={item.status === 'succeeded' ? 'checkmark-circle' : 'time'} size={20}
            color={item.status === 'succeeded' ? colors.success : colors.warning} />
        </View>
      }
      badge={<Badge label={item.status} variant={getStatusVariant(item.status)} />}
      onPress={() => navigation.navigate('PaymentDetail', { paymentId: item.id })}
    />
  ), [navigation]);

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Payments</Text>
      </View>
      {isLoading && !refreshing ? <LoadingSpinner /> : (
        <GlassCard preset="cardSolid" style={styles.listCard}>
          <FlatList
            data={data?.results || []}
            keyExtractor={(item) => item.id}
            renderItem={renderPayment}
            ItemSeparatorComponent={() => <View style={styles.separator} />}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
            ListEmptyComponent={<EmptyState icon="card-outline" title="No payments" description="Payments will appear here" />}
          />
        </GlassCard>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background.primary },
  header: { paddingHorizontal: 20, paddingVertical: 16 },
  headerTitle: { fontFamily: fontFamily.bold, fontSize: fontSize['3xl'], color: colors.text.primary },
  listCard: { flex: 1, marginHorizontal: 16, marginBottom: 100 },
  separator: { height: 1, backgroundColor: colors.figma.lighterElements + '40', marginHorizontal: 16 },
  paymentIcon: { width: 40, height: 40, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
});

export default PaymentListScreen;
