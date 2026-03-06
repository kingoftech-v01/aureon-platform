/**
 * PaymentDetailScreen - Payment detail view with glassmorphism
 */

import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { RouteProp } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';
import { useQuery } from '@tanstack/react-query';
import { GlassCard, GlassHeader } from '@components/glass';
import { Badge, CurrencyText, LoadingSpinner } from '@components/common';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { paymentService } from '@services/paymentService';
import type { MoreStackParamList } from '@types/navigation';

const PaymentDetailScreen: React.FC<{ navigation: any; route: any }> = ({ navigation, route }) => {
  const { paymentId } = route.params;

  const { data: payment, isLoading } = useQuery({
    queryKey: ['payment', paymentId],
    queryFn: () => paymentService.getPayment(paymentId),
  });

  if (isLoading || !payment) {
    return <LoadingSpinner />;
  }

  const getStatusVariant = (status: string) => {
    const map: Record<string, any> = {
      succeeded: 'success',
      pending: 'warning',
      processing: 'info',
      failed: 'danger',
      refunded: 'default',
      partially_refunded: 'warning',
    };
    return map[status] || 'default';
  };

  const getStatusIcon = (status: string) => {
    const map: Record<string, string> = {
      succeeded: 'checkmark-circle',
      pending: 'time',
      processing: 'sync',
      failed: 'close-circle',
      refunded: 'arrow-undo',
      partially_refunded: 'arrow-undo',
    };
    return map[status] || 'help-circle';
  };

  const statusColor = payment.status === 'succeeded'
    ? colors.success
    : payment.status === 'failed'
      ? colors.danger
      : payment.status === 'pending'
        ? colors.warning
        : colors.info;

  return (
    <View style={styles.container}>
      <GlassHeader title="Payment" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Amount & Status Header */}
        <View style={styles.headerSection}>
          <View style={[styles.statusIconCircle, { backgroundColor: statusColor + '20' }]}>
            <Icon
              name={getStatusIcon(payment.status)}
              size={36}
              color={statusColor}
            />
          </View>
          <CurrencyText
            amount={payment.amount}
            currency={payment.currency}
            size="xl"
          />
          <Badge
            label={payment.status}
            variant={getStatusVariant(payment.status)}
            size="md"
          />
          <Text style={styles.paymentNumber}>{payment.payment_number}</Text>
        </View>

        {/* Details Card */}
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <Text style={styles.sectionTitle}>Details</Text>

            <View style={styles.detailRow}>
              <View style={styles.detailIcon}>
                <Icon name="card-outline" size={18} color={colors.text.muted} />
              </View>
              <View style={styles.detailInfo}>
                <Text style={styles.detailLabel}>Payment Method</Text>
                <Text style={styles.detailValue}>
                  {payment.payment_method?.type
                    ? payment.payment_method.type.replace('_', ' ')
                    : 'N/A'}
                </Text>
              </View>
            </View>

            <View style={styles.detailRow}>
              <View style={styles.detailIcon}>
                <Icon name="finger-print-outline" size={18} color={colors.text.muted} />
              </View>
              <View style={styles.detailInfo}>
                <Text style={styles.detailLabel}>Transaction ID</Text>
                <Text style={styles.detailValue} numberOfLines={1}>
                  {payment.transaction_id || payment.stripe_payment_intent_id || 'N/A'}
                </Text>
              </View>
            </View>

            <View style={styles.detailRow}>
              <View style={styles.detailIcon}>
                <Icon name="calendar-outline" size={18} color={colors.text.muted} />
              </View>
              <View style={styles.detailInfo}>
                <Text style={styles.detailLabel}>Date</Text>
                <Text style={styles.detailValue}>
                  {payment.paid_at
                    ? new Date(payment.paid_at).toLocaleString()
                    : new Date(payment.created_at).toLocaleString()}
                </Text>
              </View>
            </View>

            <View style={styles.detailRow}>
              <View style={styles.detailIcon}>
                <Icon name="cash-outline" size={18} color={colors.text.muted} />
              </View>
              <View style={styles.detailInfo}>
                <Text style={styles.detailLabel}>Currency</Text>
                <Text style={styles.detailValue}>{payment.currency || 'USD'}</Text>
              </View>
            </View>
          </View>
        </GlassCard>

        {/* Invoice Card */}
        {payment.invoice && (
          <GlassCard preset="cardSolid" style={styles.card}>
            <View style={styles.cardContent}>
              <Text style={styles.sectionTitle}>Invoice</Text>

              <View style={styles.detailRow}>
                <View style={styles.detailIcon}>
                  <Icon name="document-text-outline" size={18} color={colors.text.muted} />
                </View>
                <View style={styles.detailInfo}>
                  <Text style={styles.detailLabel}>Invoice Number</Text>
                  <Text style={styles.detailValue}>
                    {payment.invoice.invoice_number || 'N/A'}
                  </Text>
                </View>
              </View>

              {payment.invoice.client && (
                <View style={styles.detailRow}>
                  <View style={styles.detailIcon}>
                    <Icon name="person-outline" size={18} color={colors.text.muted} />
                  </View>
                  <View style={styles.detailInfo}>
                    <Text style={styles.detailLabel}>Client</Text>
                    <Text style={styles.detailValue}>
                      {payment.invoice.client.company_name ||
                        `${payment.invoice.client.first_name || ''} ${payment.invoice.client.last_name || ''}`.trim() ||
                        'N/A'}
                    </Text>
                  </View>
                </View>
              )}

              <View style={styles.detailRow}>
                <View style={styles.detailIcon}>
                  <Icon name="pricetag-outline" size={18} color={colors.text.muted} />
                </View>
                <View style={styles.detailInfo}>
                  <Text style={styles.detailLabel}>Invoice Status</Text>
                  <Badge
                    label={payment.invoice.status}
                    variant={payment.invoice.status === 'paid' ? 'success' : 'info'}
                  />
                </View>
              </View>
            </View>
          </GlassCard>
        )}

        {/* Stripe / Card Info */}
        {payment.payment_method && (payment.payment_method.last4 || payment.payment_method.brand) && (
          <GlassCard preset="cardSolid" style={styles.card}>
            <View style={styles.cardContent}>
              <Text style={styles.sectionTitle}>Card Info</Text>

              {payment.payment_method.brand && (
                <View style={styles.detailRow}>
                  <View style={styles.detailIcon}>
                    <Icon name="card-outline" size={18} color={colors.text.muted} />
                  </View>
                  <View style={styles.detailInfo}>
                    <Text style={styles.detailLabel}>Card Brand</Text>
                    <Text style={[styles.detailValue, styles.capitalizedText]}>
                      {payment.payment_method.brand}
                    </Text>
                  </View>
                </View>
              )}

              {payment.payment_method.last4 && (
                <View style={styles.detailRow}>
                  <View style={styles.detailIcon}>
                    <Icon name="ellipsis-horizontal" size={18} color={colors.text.muted} />
                  </View>
                  <View style={styles.detailInfo}>
                    <Text style={styles.detailLabel}>Card Number</Text>
                    <Text style={styles.detailValue}>
                      **** **** **** {payment.payment_method.last4}
                    </Text>
                  </View>
                </View>
              )}

              {payment.payment_method.exp_month && payment.payment_method.exp_year && (
                <View style={styles.detailRow}>
                  <View style={styles.detailIcon}>
                    <Icon name="calendar-outline" size={18} color={colors.text.muted} />
                  </View>
                  <View style={styles.detailInfo}>
                    <Text style={styles.detailLabel}>Expiry</Text>
                    <Text style={styles.detailValue}>
                      {String(payment.payment_method.exp_month).padStart(2, '0')}/{payment.payment_method.exp_year}
                    </Text>
                  </View>
                </View>
              )}
            </View>
          </GlassCard>
        )}

        {/* Notes */}
        {payment.notes && (
          <GlassCard preset="cardSolid" style={styles.card}>
            <View style={styles.cardContent}>
              <Text style={styles.sectionTitle}>Notes</Text>
              <Text style={styles.notesText}>{payment.notes}</Text>
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
  headerSection: {
    alignItems: 'center',
    paddingVertical: 28,
    gap: 8,
  },
  statusIconCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  paymentNumber: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.sm,
    color: colors.text.secondary,
    marginTop: 4,
  },
  card: {
    marginHorizontal: 20,
    marginBottom: 16,
  },
  cardContent: {
    padding: 20,
  },
  sectionTitle: {
    fontFamily: fontFamily.semiBold,
    fontSize: fontSize.xl,
    color: colors.text.primary,
    marginBottom: 16,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: colors.figma.lighterElements + '30',
  },
  detailIcon: {
    width: 36,
    height: 36,
    borderRadius: 10,
    backgroundColor: colors.figma.lighterElements + '30',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  detailInfo: {
    flex: 1,
  },
  detailLabel: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.sm,
    color: colors.text.secondary,
    marginBottom: 2,
  },
  detailValue: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.md,
    color: colors.text.primary,
  },
  capitalizedText: {
    textTransform: 'capitalize',
  },
  notesText: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    color: colors.text.primary,
    lineHeight: 22,
  },
});

export default PaymentDetailScreen;
