/**
 * ClientPicker - Searchable client selector with modal list
 */

import React, { useState } from 'react';
import { View, Text, FlatList, Pressable, StyleSheet } from 'react-native';
import { GlassCard, GlassInput, GlassModal } from '@components/glass';
import { Avatar, Badge } from '@components/common';
import { useClients } from '@hooks/useClients';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import Ionicons from 'react-native-vector-icons/Ionicons';
import type { Client } from '@types/index';

interface ClientPickerProps {
  label?: string;
  selectedId?: string;
  onSelect: (client: Client) => void;
  error?: string;
}

const ClientPicker: React.FC<ClientPickerProps> = ({
  label = 'Client',
  selectedId,
  onSelect,
  error,
}) => {
  const [visible, setVisible] = useState(false);
  const [search, setSearch] = useState('');
  const { data, isLoading } = useClients(
    { page: 1, page_size: 50 },
    search ? { search } : undefined,
  );

  const clients = data?.results || [];
  const selectedClient = clients.find((c: Client) => c.id === selectedId);

  const getClientName = (client: Client) =>
    client.type === 'individual'
      ? `${client.first_name} ${client.last_name}`
      : client.company_name || '';

  return (
    <View>
      {label && <Text style={styles.label}>{label}</Text>}
      <Pressable onPress={() => setVisible(true)}>
        <GlassCard preset="input" style={styles.selector}>
          <View style={styles.selectorContent}>
            {selectedClient ? (
              <View style={styles.selectedRow}>
                <Avatar name={getClientName(selectedClient)} size="sm" />
                <View style={styles.selectedInfo}>
                  <Text style={styles.selectedName}>
                    {getClientName(selectedClient)}
                  </Text>
                  <Text style={styles.selectedEmail}>
                    {selectedClient.email}
                  </Text>
                </View>
              </View>
            ) : (
              <Text style={styles.placeholder}>Select a client...</Text>
            )}
          </View>
        </GlassCard>
      </Pressable>
      {error && <Text style={styles.error}>{error}</Text>}

      <GlassModal visible={visible} onClose={() => setVisible(false)}>
        <Text style={styles.modalTitle}>Select Client</Text>
        <GlassInput
          placeholder="Search clients..."
          value={search}
          onChangeText={setSearch}
          icon={
            <Ionicons
              name="search-outline"
              size={20}
              color={colors.text.muted}
            />
          }
        />
        <FlatList
          data={clients}
          keyExtractor={(item) => item.id}
          style={styles.list}
          renderItem={({ item }) => (
            <Pressable
              onPress={() => {
                onSelect(item);
                setVisible(false);
              }}
              style={({ pressed }) => [
                styles.clientItem,
                pressed && styles.pressed,
                item.id === selectedId && styles.selectedItem,
              ]}
            >
              <Avatar name={getClientName(item)} size="sm" />
              <View style={styles.clientInfo}>
                <Text style={styles.clientName}>{getClientName(item)}</Text>
                <Text style={styles.clientEmail}>{item.email}</Text>
              </View>
              <Badge
                variant={
                  item.lifecycle_stage === 'active' ? 'success' : 'default'
                }
                size="sm"
                label={item.lifecycle_stage}
              />
            </Pressable>
          )}
          ListEmptyComponent={
            <Text style={styles.empty}>
              {isLoading ? 'Loading...' : 'No clients found'}
            </Text>
          }
        />
      </GlassModal>
    </View>
  );
};

const styles = StyleSheet.create({
  label: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.sm,
    color: colors.text.secondary,
    marginBottom: 6,
  },
  selector: {
    marginBottom: 0,
  },
  selectorContent: {
    padding: 14,
  },
  selectedRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  selectedInfo: {
    flex: 1,
  },
  selectedName: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.md,
    color: colors.text.primary,
  },
  selectedEmail: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.sm,
    color: colors.text.secondary,
  },
  placeholder: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    color: colors.text.muted,
  },
  error: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.sm,
    color: colors.danger,
    marginTop: 4,
  },
  modalTitle: {
    fontFamily: fontFamily.semiBold,
    fontSize: fontSize['2xl'],
    color: colors.text.inverse,
    marginBottom: 16,
  },
  list: {
    maxHeight: 300,
    marginTop: 12,
  },
  clientItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    gap: 12,
    borderRadius: 10,
  },
  pressed: {
    opacity: 0.7,
  },
  selectedItem: {
    backgroundColor: 'rgba(0, 124, 255, 0.1)',
  },
  clientInfo: {
    flex: 1,
  },
  clientName: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.md,
    color: colors.text.primary,
  },
  clientEmail: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.sm,
    color: colors.text.secondary,
  },
  empty: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    color: colors.text.muted,
    textAlign: 'center',
    padding: 24,
  },
});

export default ClientPicker;
