/**
 * ContractListScreen - Contract list with milestone progress
 */

import React, { useState, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, RefreshControl, Pressable } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Ionicons';
import { useQuery } from '@tanstack/react-query';
import { GlassCard } from '@components/glass';
import { Badge, ListItem, SearchBar, EmptyState, LoadingSpinner, CurrencyText } from '@components/common';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { contractService } from '@services/contractService';
import type { Contract } from '@/types';

interface Props {
  navigation: any;
}

const ContractListScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const [search, setSearch] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['contracts', search],
    queryFn: () => contractService.getContracts({ page: 1, page_size: 50 }, search ? { search } : undefined),
  });

  const onRefresh = async () => { setRefreshing(true); await refetch(); setRefreshing(false); };

  const getStatusVariant = (status: string) => {
    const map: Record<string, any> = {
      draft: 'default', sent: 'info', signed: 'primary', active: 'success', completed: 'success', terminated: 'danger',
    };
    return map[status] || 'default';
  };

  const renderContract = useCallback(({ item }: { item: Contract }) => {
    const clientName = typeof item.client === 'object'
      ? (item.client.company_name || `${item.client.first_name} ${item.client.last_name}`)
      : 'Unknown';
    return (
      <ListItem
        title={item.title}
        subtitle={`${clientName} · ${item.contract_number}`}
        left={
          <View style={[styles.contractIcon, { backgroundColor: colors.accent[50] }]}>
            <Icon name="document-text-outline" size={20} color={colors.accent[600]} />
          </View>
        }
        badge={<Badge label={item.status} variant={getStatusVariant(item.status)} />}
        rightText={`$${item.total_value.toLocaleString()}`}
        onPress={() => navigation.navigate('ContractDetail', { contractId: item.id })}
      />
    );
  }, [navigation]);

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Contracts</Text>
      </View>
      <SearchBar value={search} onChangeText={setSearch} placeholder="Search contracts..." />
      {isLoading && !refreshing ? <LoadingSpinner /> : (
        <GlassCard preset="cardSolid" style={styles.listCard}>
          <FlatList
            data={data?.results || []}
            keyExtractor={(item) => item.id}
            renderItem={renderContract}
            ItemSeparatorComponent={() => <View style={styles.separator} />}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
            ListEmptyComponent={<EmptyState icon="document-text-outline" title="No contracts" description="Create your first contract" />}
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
  listCard: { flex: 1, marginHorizontal: 16, marginBottom: 100 },
  separator: { height: 1, backgroundColor: colors.figma.lighterElements + '40', marginHorizontal: 16 },
  emptyList: { flexGrow: 1 },
  contractIcon: { width: 40, height: 40, borderRadius: 12, alignItems: 'center', justifyContent: 'center' },
});

export default ContractListScreen;
