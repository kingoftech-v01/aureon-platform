/**
 * InvoiceListScreen - Invoice list with status badges and glassmorphism
 */

import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, RefreshControl, Pressable } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import Icon from 'react-native-vector-icons/Ionicons';
import { GlassCard } from '@components/glass';
import { Badge, ListItem, SearchBar, EmptyState, LoadingSpinner, CurrencyText } from '@components/common';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { useInvoices } from '@hooks/useInvoices';
import type { InvoiceStackParamList } from '@types/navigation';
import type { Invoice, InvoiceStatus } from '@/types';

type Props = {
  navigation: NativeStackNavigationProp<InvoiceStackParamList, 'InvoiceList'>;
};

const STATUS_MAP: Record<string, { label: string; variant: any }> = {
  draft: { label: 'Draft', variant: 'default' },
  sent: { label: 'Sent', variant: 'info' },
  viewed: { label: 'Viewed', variant: 'primary' },
  paid: { label: 'Paid', variant: 'success' },
  partially_paid: { label: 'Partial', variant: 'warning' },
  overdue: { label: 'Overdue', variant: 'danger' },
  cancelled: { label: 'Cancelled', variant: 'default' },
};

const InvoiceListScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const filters: Record<string, any> = {};
  if (search) filters.search = search;
  if (statusFilter) filters.status = statusFilter;

  const { data, isLoading, refetch } = useInvoices({ page: 1, page_size: 50 }, filters);

  const onRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  const renderInvoice = useCallback(({ item }: { item: Invoice }) => {
    const status = STATUS_MAP[item.status] || STATUS_MAP.draft;
    const clientName = typeof item.client === 'object'
      ? (item.client.company_name || `${item.client.first_name} ${item.client.last_name}`)
      : 'Unknown';

    return (
      <ListItem
        title={item.invoice_number}
        subtitle={`${clientName} · Due ${new Date(item.due_date).toLocaleDateString()}`}
        left={
          <View style={[styles.invoiceIcon, {
            backgroundColor: item.status === 'paid' ? colors.success + '20' :
              item.status === 'overdue' ? colors.danger + '20' : colors.primary[50]
          }]}>
            <Icon name="receipt-outline" size={20} color={
              item.status === 'paid' ? colors.success :
                item.status === 'overdue' ? colors.danger : colors.primary[500]
            } />
          </View>
        }
        badge={<Badge label={status.label} variant={status.variant} />}
        rightText={`$${item.total.toLocaleString()}`}
        onPress={() => navigation.navigate('InvoiceDetail', { invoiceId: item.id })}
      />
    );
  }, [navigation]);

  const statuses = ['all', 'draft', 'sent', 'paid', 'overdue'];

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Invoices</Text>
        <Pressable style={styles.addButton} onPress={() => navigation.navigate('InvoiceCreate')}>
          <Icon name="add" size={24} color={colors.white} />
        </Pressable>
      </View>

      <SearchBar value={search} onChangeText={setSearch} placeholder="Search invoices..." />

      <View style={styles.filterRow}>
        {statuses.map((status) => (
          <Pressable
            key={status}
            style={[styles.chip, (statusFilter === status || (!statusFilter && status === 'all')) && styles.chipActive]}
            onPress={() => setStatusFilter(status === 'all' ? null : status)}
          >
            <Text style={[styles.chipText, (statusFilter === status || (!statusFilter && status === 'all')) && styles.chipTextActive]}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </Text>
          </Pressable>
        ))}
      </View>

      {isLoading && !refreshing ? (
        <LoadingSpinner />
      ) : (
        <GlassCard preset="cardSolid" style={styles.listCard}>
          <FlatList
            data={data?.results || []}
            keyExtractor={(item) => item.id}
            renderItem={renderInvoice}
            ItemSeparatorComponent={() => <View style={styles.separator} />}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
            ListEmptyComponent={
              <EmptyState icon="receipt-outline" title="No invoices yet" description="Create your first invoice" />
            }
            contentContainerStyle={!data?.results?.length ? styles.emptyList : undefined}
          />
        </GlassCard>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background.primary },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, paddingVertical: 16 },
  headerTitle: { fontFamily: fontFamily.bold, fontSize: fontSize['3xl'], color: colors.text.primary },
  addButton: { width: 40, height: 40, borderRadius: 12, backgroundColor: colors.primary[500], alignItems: 'center', justifyContent: 'center' },
  filterRow: { flexDirection: 'row', paddingHorizontal: 16, marginBottom: 12, gap: 8 },
  chip: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: 20, backgroundColor: colors.white, borderWidth: 1, borderColor: colors.figma.borders },
  chipActive: { backgroundColor: colors.primary[500], borderColor: colors.primary[500] },
  chipText: { fontFamily: fontFamily.medium, fontSize: fontSize.sm, color: colors.text.secondary },
  chipTextActive: { color: colors.white },
  listCard: { flex: 1, marginHorizontal: 16, marginBottom: 100 },
  separator: { height: 1, backgroundColor: colors.figma.lighterElements + '40', marginHorizontal: 16 },
  emptyList: { flexGrow: 1 },
  invoiceIcon: { width: 40, height: 40, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
});

export default InvoiceListScreen;
