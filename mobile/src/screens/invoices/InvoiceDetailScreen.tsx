/**
 * InvoiceDetailScreen - Invoice detail with line items
 */

import React from 'react';
import { View, Text, StyleSheet, ScrollView } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { RouteProp } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';
import { GlassCard, GlassHeader, GlassButton } from '@components/glass';
import { Badge, CurrencyText, LoadingSpinner } from '@components/common';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { useInvoice, useSendInvoice, useMarkInvoicePaid } from '@hooks/useInvoices';
import type { InvoiceStackParamList } from '@types/navigation';

type Props = {
  navigation: NativeStackNavigationProp<InvoiceStackParamList, 'InvoiceDetail'>;
  route: RouteProp<InvoiceStackParamList, 'InvoiceDetail'>;
};

const InvoiceDetailScreen: React.FC<Props> = ({ navigation, route }) => {
  const { invoiceId } = route.params;
  const { data: invoice, isLoading } = useInvoice(invoiceId);
  const sendInvoice = useSendInvoice();
  const markPaid = useMarkInvoicePaid();

  if (isLoading || !invoice) return <LoadingSpinner />;

  const clientName = typeof invoice.client === 'object'
    ? (invoice.client.company_name || `${invoice.client.first_name} ${invoice.client.last_name}`)
    : 'Unknown';

  return (
    <View style={styles.container}>
      <GlassHeader title={invoice.invoice_number} onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Status Banner */}
        <GlassCard preset="cardSolid" style={styles.statusCard}>
          <View style={styles.statusContent}>
            <Badge label={invoice.status} variant={
              invoice.status === 'paid' ? 'success' : invoice.status === 'overdue' ? 'danger' : 'info'
            } size="md" />
            <CurrencyText amount={invoice.total} currency={invoice.currency} size="xl" />
            <Text style={styles.clientName}>{clientName}</Text>
          </View>
        </GlassCard>

        {/* Dates */}
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <View style={styles.dateRow}>
              <View style={styles.dateItem}>
                <Text style={styles.dateLabel}>Issued</Text>
                <Text style={styles.dateValue}>{new Date(invoice.issue_date).toLocaleDateString()}</Text>
              </View>
              <View style={styles.dateItem}>
                <Text style={styles.dateLabel}>Due</Text>
                <Text style={styles.dateValue}>{new Date(invoice.due_date).toLocaleDateString()}</Text>
              </View>
            </View>
          </View>
        </GlassCard>

        {/* Line Items */}
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <Text style={styles.sectionTitle}>Items</Text>
            {invoice.items.map((item, index) => (
              <View key={item.id || index} style={styles.lineItem}>
                <View style={styles.lineItemLeft}>
                  <Text style={styles.lineItemDesc}>{item.description}</Text>
                  <Text style={styles.lineItemQty}>
                    {item.quantity} x ${item.unit_price.toFixed(2)}
                  </Text>
                </View>
                <CurrencyText amount={item.total} size="sm" />
              </View>
            ))}

            <View style={styles.totals}>
              <View style={styles.totalRow}>
                <Text style={styles.totalLabel}>Subtotal</Text>
                <CurrencyText amount={invoice.subtotal} size="sm" />
              </View>
              {invoice.tax_amount > 0 && (
                <View style={styles.totalRow}>
                  <Text style={styles.totalLabel}>Tax ({invoice.tax_rate}%)</Text>
                  <CurrencyText amount={invoice.tax_amount} size="sm" />
                </View>
              )}
              {invoice.discount_amount > 0 && (
                <View style={styles.totalRow}>
                  <Text style={styles.totalLabel}>Discount</Text>
                  <Text style={[styles.totalLabel, { color: colors.success }]}>
                    -${invoice.discount_amount.toFixed(2)}
                  </Text>
                </View>
              )}
              <View style={[styles.totalRow, styles.grandTotal]}>
                <Text style={styles.grandTotalLabel}>Total</Text>
                <CurrencyText amount={invoice.total} size="lg" />
              </View>
            </View>
          </View>
        </GlassCard>

        {/* Actions */}
        <View style={styles.actions}>
          {invoice.status === 'draft' && (
            <GlassButton
              title="Send Invoice"
              onPress={() => sendInvoice.mutate(invoice.id)}
              variant="primary"
              loading={sendInvoice.isPending}
              fullWidth
              icon={<Icon name="send" size={18} color={colors.white} />}
            />
          )}
          {['sent', 'viewed', 'overdue'].includes(invoice.status) && (
            <GlassButton
              title="Mark as Paid"
              onPress={() => markPaid.mutate({
                id: invoice.id,
                data: { payment_amount: invoice.total, payment_method: 'card' },
              })}
              variant="primary"
              loading={markPaid.isPending}
              fullWidth
              icon={<Icon name="checkmark-circle" size={18} color={colors.white} />}
            />
          )}
        </View>
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background.primary },
  scrollContent: { padding: 20, paddingBottom: 100 },
  statusCard: { marginBottom: 16 },
  statusContent: { padding: 24, alignItems: 'center', gap: 8 },
  clientName: { fontFamily: fontFamily.medium, fontSize: fontSize.lg, color: colors.text.secondary },
  card: { marginBottom: 16 },
  cardContent: { padding: 20 },
  sectionTitle: { fontFamily: fontFamily.semiBold, fontSize: fontSize.xl, color: colors.text.primary, marginBottom: 16 },
  dateRow: { flexDirection: 'row', gap: 24 },
  dateItem: {},
  dateLabel: { fontFamily: fontFamily.medium, fontSize: fontSize.sm, color: colors.text.secondary, marginBottom: 4 },
  dateValue: { fontFamily: fontFamily.semiBold, fontSize: fontSize.lg, color: colors.text.primary },
  lineItem: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: colors.figma.lighterElements + '40' },
  lineItemLeft: { flex: 1 },
  lineItemDesc: { fontFamily: fontFamily.medium, fontSize: fontSize.md, color: colors.text.primary },
  lineItemQty: { fontFamily: fontFamily.regular, fontSize: fontSize.sm, color: colors.text.secondary, marginTop: 2 },
  totals: { marginTop: 16, gap: 8 },
  totalRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  totalLabel: { fontFamily: fontFamily.regular, fontSize: fontSize.md, color: colors.text.secondary },
  grandTotal: { marginTop: 8, paddingTop: 12, borderTopWidth: 2, borderTopColor: colors.figma.lighterElements },
  grandTotalLabel: { fontFamily: fontFamily.bold, fontSize: fontSize.xl, color: colors.text.primary },
  actions: { marginTop: 8, gap: 12 },
});

export default InvoiceDetailScreen;
