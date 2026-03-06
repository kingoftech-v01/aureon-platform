/**
 * InvoiceCreateScreen - Create new invoice form
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { GlassCard, GlassHeader, GlassButton, GlassInput } from '@components/glass';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { useCreateInvoice } from '@hooks/useInvoices';
import type { InvoiceStackParamList } from '@types/navigation';

type Props = {
  navigation: NativeStackNavigationProp<InvoiceStackParamList, 'InvoiceCreate'>;
};

const InvoiceCreateScreen: React.FC<Props> = ({ navigation }) => {
  const createInvoice = useCreateInvoice();
  const [clientId, setClientId] = useState('');
  const [dueDate, setDueDate] = useState('');
  const [description, setDescription] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [unitPrice, setUnitPrice] = useState('');
  const [taxRate, setTaxRate] = useState('0');

  const handleSubmit = async () => {
    if (!clientId || !unitPrice) {
      Alert.alert('Error', 'Please fill in required fields');
      return;
    }

    const today = new Date().toISOString().split('T')[0];
    try {
      await createInvoice.mutateAsync({
        client: clientId,
        issue_date: today,
        due_date: dueDate || today,
        tax_rate: parseFloat(taxRate) || 0,
        items: [{
          description: description || 'Service',
          quantity: parseFloat(quantity) || 1,
          unit_price: parseFloat(unitPrice) || 0,
          tax_rate: parseFloat(taxRate) || 0,
        }],
      });
      navigation.goBack();
    } catch {
      Alert.alert('Error', 'Failed to create invoice');
    }
  };

  return (
    <View style={styles.container}>
      <GlassHeader title="New Invoice" onBack={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <Text style={styles.sectionTitle}>Invoice Details</Text>

            <GlassInput label="Client ID *" value={clientId} onChangeText={setClientId} placeholder="Enter client ID" />
            <GlassInput label="Due Date" value={dueDate} onChangeText={setDueDate} placeholder="YYYY-MM-DD" />

            <Text style={[styles.sectionTitle, { marginTop: 16 }]}>Line Item</Text>
            <GlassInput label="Description" value={description} onChangeText={setDescription} placeholder="Service description" />

            <View style={styles.row}>
              <View style={styles.half}>
                <GlassInput label="Quantity" value={quantity} onChangeText={setQuantity} keyboardType="numeric" />
              </View>
              <View style={styles.half}>
                <GlassInput label="Unit Price *" value={unitPrice} onChangeText={setUnitPrice} placeholder="0.00" keyboardType="numeric" />
              </View>
            </View>

            <GlassInput label="Tax Rate (%)" value={taxRate} onChangeText={setTaxRate} keyboardType="numeric" />
          </View>
        </GlassCard>

        <GlassButton title="Create Invoice" onPress={handleSubmit} variant="primary" size="lg" loading={createInvoice.isPending} fullWidth />
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background.primary },
  scrollContent: { padding: 20, paddingBottom: 100 },
  card: { marginBottom: 20 },
  cardContent: { padding: 20 },
  sectionTitle: { fontFamily: fontFamily.semiBold, fontSize: fontSize.xl, color: colors.text.primary, marginBottom: 16 },
  row: { flexDirection: 'row', gap: 12 },
  half: { flex: 1 },
});

export default InvoiceCreateScreen;
