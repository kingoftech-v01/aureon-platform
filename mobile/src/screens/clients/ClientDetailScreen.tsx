/**
 * ClientDetailScreen - Client profile with stats and actions
 */

import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';
import { GlassCard, GlassHeader } from '@components/glass';
import { Avatar, Badge, CurrencyText, LoadingSpinner } from '@components/common';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { useClient } from '@hooks/useClients';
import type { ClientStackParamList } from '@types/navigation';

type Props = {
  navigation: NativeStackNavigationProp<ClientStackParamList, 'ClientDetail'>;
  route: RouteProp<ClientStackParamList, 'ClientDetail'>;
};

const ClientDetailScreen: React.FC<Props> = ({ navigation, route }) => {
  const { clientId } = route.params;
  const { data: client, isLoading } = useClient(clientId);

  if (isLoading || !client) {
    return <LoadingSpinner />;
  }

  const name =
    client.company_name ||
    `${client.first_name || ''} ${client.last_name || ''}`.trim();

  return (
    <View style={styles.container}>
      <GlassHeader
        title="Client"
        onBack={() => navigation.goBack()}
        rightAction={
          <Icon name="create-outline" size={24} color={colors.text.secondary} />
        }
      />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Profile Section */}
        <View style={styles.profileSection}>
          <Avatar name={name} size="xl" />
          <Text style={styles.name}>{name}</Text>
          <Text style={styles.email}>{client.email}</Text>
          <Badge
            label={client.lifecycle_stage}
            variant={
              client.lifecycle_stage === 'active'
                ? 'success'
                : client.lifecycle_stage === 'lead'
                  ? 'info'
                  : 'default'
            }
            size="md"
          />
        </View>

        {/* Stats Cards */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.statsRow}
        >
          <GlassCard preset="cardSolid" style={styles.statCard}>
            <View style={styles.statContent}>
              <Text style={styles.statLabel}>Total Revenue</Text>
              <CurrencyText amount={client.total_revenue || 0} size="lg" />
            </View>
          </GlassCard>
          <GlassCard preset="cardSolid" style={styles.statCard}>
            <View style={styles.statContent}>
              <Text style={styles.statLabel}>ARR</Text>
              <CurrencyText
                amount={client.annual_recurring_revenue || 0}
                size="lg"
              />
            </View>
          </GlassCard>
          <GlassCard preset="cardSolid" style={styles.statCard}>
            <View style={styles.statContent}>
              <Text style={styles.statLabel}>Lifetime Value</Text>
              <CurrencyText amount={client.lifetime_value || 0} size="lg" />
            </View>
          </GlassCard>
        </ScrollView>

        {/* Details */}
        <GlassCard preset="cardSolid" style={styles.detailsCard}>
          <View style={styles.detailsContent}>
            <Text style={styles.detailsTitle}>Details</Text>

            {client.phone_number && (
              <View style={styles.detailRow}>
                <Icon name="call-outline" size={18} color={colors.text.muted} />
                <Text style={styles.detailText}>{client.phone_number}</Text>
              </View>
            )}
            {client.address && (
              <View style={styles.detailRow}>
                <Icon name="location-outline" size={18} color={colors.text.muted} />
                <Text style={styles.detailText}>
                  {[client.address, client.city, client.state, client.country]
                    .filter(Boolean)
                    .join(', ')}
                </Text>
              </View>
            )}
            {client.website && (
              <View style={styles.detailRow}>
                <Icon name="globe-outline" size={18} color={colors.text.muted} />
                <Text style={styles.detailText}>{client.website}</Text>
              </View>
            )}
            {client.tags?.length > 0 && (
              <View style={styles.tagsRow}>
                {client.tags.map((tag) => (
                  <Badge key={tag} label={tag} variant="primary" />
                ))}
              </View>
            )}
          </View>
        </GlassCard>

        {client.notes && (
          <GlassCard preset="cardSolid" style={styles.notesCard}>
            <View style={styles.detailsContent}>
              <Text style={styles.detailsTitle}>Notes</Text>
              <Text style={styles.notesText}>{client.notes}</Text>
            </View>
          </GlassCard>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background.primary,
  },
  scrollContent: {
    paddingBottom: 100,
  },
  profileSection: {
    alignItems: 'center',
    paddingVertical: 24,
    gap: 8,
  },
  name: {
    fontFamily: fontFamily.bold,
    fontSize: fontSize['3xl'],
    color: colors.text.primary,
  },
  email: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    color: colors.text.secondary,
  },
  statsRow: {
    paddingHorizontal: 20,
    gap: 12,
    marginBottom: 20,
  },
  statCard: {
    width: 140,
  },
  statContent: {
    padding: 16,
  },
  statLabel: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.sm,
    color: colors.text.secondary,
    marginBottom: 4,
  },
  detailsCard: {
    marginHorizontal: 20,
    marginBottom: 16,
  },
  detailsContent: {
    padding: 20,
  },
  detailsTitle: {
    fontFamily: fontFamily.semiBold,
    fontSize: fontSize.xl,
    color: colors.text.primary,
    marginBottom: 16,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  detailText: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    color: colors.text.primary,
    flex: 1,
  },
  tagsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 8,
  },
  notesCard: {
    marginHorizontal: 20,
    marginBottom: 16,
  },
  notesText: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    color: colors.text.primary,
    lineHeight: 22,
  },
});

export default ClientDetailScreen;
