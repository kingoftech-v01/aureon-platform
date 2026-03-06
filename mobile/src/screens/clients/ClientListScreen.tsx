/**
 * ClientListScreen - Searchable client list with glassmorphism
 * Follows Figma trending list pattern
 */

import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  Pressable,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import Icon from 'react-native-vector-icons/Ionicons';
import { GlassCard } from '@components/glass';
import {
  Avatar,
  Badge,
  ListItem,
  SearchBar,
  EmptyState,
  LoadingSpinner,
} from '@components/common';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { useClients } from '@hooks/useClients';
import type { ClientStackParamList } from '@types/navigation';
import type { Client, LifecycleStage } from '@/types';

type Props = {
  navigation: NativeStackNavigationProp<ClientStackParamList, 'ClientList'>;
};

const STAGE_BADGES: Record<string, { label: string; variant: any }> = {
  lead: { label: 'Lead', variant: 'info' },
  prospect: { label: 'Prospect', variant: 'warning' },
  active: { label: 'Active', variant: 'success' },
  churned: { label: 'Churned', variant: 'danger' },
  archived: { label: 'Archived', variant: 'default' },
};

const ClientListScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const [search, setSearch] = useState('');
  const [stageFilter, setStageFilter] = useState<string | null>(null);

  const filters: Record<string, any> = {};
  if (search) filters.search = search;
  if (stageFilter) filters.lifecycle_stage = stageFilter;

  const { data, isLoading, refetch } = useClients(
    { page: 1, page_size: 50 },
    filters,
  );

  const [refreshing, setRefreshing] = useState(false);
  const onRefresh = async () => {
    setRefreshing(true);
    await refetch();
    setRefreshing(false);
  };

  const getClientName = (client: Client) => {
    if (client.company_name) return client.company_name;
    return `${client.first_name || ''} ${client.last_name || ''}`.trim() || client.email;
  };

  const renderClient = useCallback(
    ({ item }: { item: Client }) => {
      const stage = STAGE_BADGES[item.lifecycle_stage] || STAGE_BADGES.lead;
      return (
        <ListItem
          title={getClientName(item)}
          subtitle={item.email}
          left={<Avatar name={getClientName(item)} size="md" />}
          badge={<Badge label={stage.label} variant={stage.variant} />}
          rightText={
            item.total_revenue
              ? `$${item.total_revenue.toLocaleString()}`
              : undefined
          }
          onPress={() =>
            navigation.navigate('ClientDetail', { clientId: item.id })
          }
        />
      );
    },
    [navigation],
  );

  const stages = ['all', 'lead', 'prospect', 'active', 'churned'];

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Clients</Text>
        <Pressable
          style={styles.addButton}
          onPress={() => navigation.navigate('ClientCreate')}
        >
          <Icon name="add" size={24} color={colors.white} />
        </Pressable>
      </View>

      <SearchBar value={search} onChangeText={setSearch} placeholder="Search clients..." />

      {/* Stage filter chips */}
      <View style={styles.filterRow}>
        {stages.map((stage) => (
          <Pressable
            key={stage}
            style={[
              styles.chip,
              (stageFilter === stage || (!stageFilter && stage === 'all')) &&
                styles.chipActive,
            ]}
            onPress={() => setStageFilter(stage === 'all' ? null : stage)}
          >
            <Text
              style={[
                styles.chipText,
                (stageFilter === stage || (!stageFilter && stage === 'all')) &&
                  styles.chipTextActive,
              ]}
            >
              {stage.charAt(0).toUpperCase() + stage.slice(1)}
            </Text>
          </Pressable>
        ))}
      </View>

      {/* Client List */}
      {isLoading && !refreshing ? (
        <LoadingSpinner />
      ) : (
        <GlassCard preset="cardSolid" style={styles.listCard}>
          <FlatList
            data={data?.results || []}
            keyExtractor={(item) => item.id}
            renderItem={renderClient}
            ItemSeparatorComponent={() => <View style={styles.separator} />}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
            }
            ListEmptyComponent={
              <EmptyState
                icon="people-outline"
                title="No clients yet"
                description="Add your first client to get started"
                actionLabel="Add Client"
                onAction={() => navigation.navigate('ClientCreate')}
              />
            }
            contentContainerStyle={
              !data?.results?.length ? styles.emptyList : undefined
            }
          />
        </GlassCard>
      )}
    </View>
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
    paddingVertical: 16,
  },
  headerTitle: {
    fontFamily: fontFamily.bold,
    fontSize: fontSize['3xl'],
    color: colors.text.primary,
  },
  addButton: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: colors.primary[500],
    alignItems: 'center',
    justifyContent: 'center',
  },
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 12,
    gap: 8,
  },
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
    backgroundColor: colors.white,
    borderWidth: 1,
    borderColor: colors.figma.borders,
  },
  chipActive: {
    backgroundColor: colors.primary[500],
    borderColor: colors.primary[500],
  },
  chipText: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.sm,
    color: colors.text.secondary,
  },
  chipTextActive: {
    color: colors.white,
  },
  listCard: {
    flex: 1,
    marginHorizontal: 16,
    marginBottom: 100,
  },
  separator: {
    height: 1,
    backgroundColor: colors.figma.lighterElements + '40',
    marginHorizontal: 16,
  },
  emptyList: {
    flexGrow: 1,
  },
});

export default ClientListScreen;
