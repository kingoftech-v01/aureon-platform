/**
 * ContractCreateScreen - Create new contract form
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
  Pressable,
  TextInput,
} from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { GlassCard, GlassHeader, GlassButton, GlassInput } from '@components/glass';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { contractService } from '@services/contractService';
import type { InvoiceStackParamList } from '@types/navigation';

type Props = {
  navigation: NativeStackNavigationProp<InvoiceStackParamList, 'ContractCreate'>;
};

const CONTRACT_TYPES = [
  { value: 'fixed_price', label: 'Fixed Price' },
  { value: 'hourly', label: 'Hourly' },
  { value: 'retainer', label: 'Retainer' },
  { value: 'milestone', label: 'Milestone' },
];

const ContractCreateScreen: React.FC<Props> = ({ navigation }) => {
  const queryClient = useQueryClient();

  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [clientId, setClientId] = useState('');
  const [contractType, setContractType] = useState('fixed_price');
  const [value, setValue] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [paymentTerms, setPaymentTerms] = useState('');
  const [notes, setNotes] = useState('');

  const createContract = useMutation({
    mutationFn: (data: any) => contractService.createContract(data),
    onSuccess: (contract) => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] });
      navigation.navigate('ContractDetail', { contractId: contract.id });
    },
    onError: () => {
      Alert.alert('Error', 'Failed to create contract');
    },
  });

  const handleSubmit = async () => {
    if (!title.trim()) {
      Alert.alert('Error', 'Contract title is required');
      return;
    }
    if (!clientId.trim()) {
      Alert.alert('Error', 'Client ID is required');
      return;
    }
    if (!value.trim()) {
      Alert.alert('Error', 'Contract value is required');
      return;
    }

    createContract.mutate({
      title: title.trim(),
      description: description.trim() || undefined,
      client: clientId.trim(),
      content: `Contract type: ${contractType}\n\n${description || ''}`,
      total_value: parseFloat(value) || 0,
      currency: currency || 'USD',
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    });
  };

  return (
    <View style={styles.container}>
      <GlassHeader title="New Contract" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        {/* Basic Info */}
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <Text style={styles.sectionTitle}>Contract Details</Text>

            <GlassInput
              label="Title *"
              value={title}
              onChangeText={setTitle}
              placeholder="e.g. Web Development Agreement"
              autoCapitalize="words"
            />

            <Text style={styles.inputLabel}>Description</Text>
            <View style={styles.textAreaContainer}>
              <TextInput
                style={styles.textArea}
                value={description}
                onChangeText={setDescription}
                placeholder="Describe the scope of work..."
                placeholderTextColor={colors.text.muted}
                multiline
                numberOfLines={4}
                textAlignVertical="top"
              />
            </View>

            <GlassInput
              label="Client ID *"
              value={clientId}
              onChangeText={setClientId}
              placeholder="Enter client ID"
              autoCapitalize="none"
            />
          </View>
        </GlassCard>

        {/* Contract Type */}
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <Text style={styles.sectionTitle}>Contract Type</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.chipsRow}
            >
              {CONTRACT_TYPES.map(type => {
                const isSelected = contractType === type.value;
                return (
                  <Pressable
                    key={type.value}
                    onPress={() => setContractType(type.value)}
                    style={[
                      styles.chip,
                      isSelected && styles.chipSelected,
                    ]}
                  >
                    <Text
                      style={[
                        styles.chipText,
                        isSelected && styles.chipTextSelected,
                      ]}
                    >
                      {type.label}
                    </Text>
                  </Pressable>
                );
              })}
            </ScrollView>
          </View>
        </GlassCard>

        {/* Financial */}
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <Text style={styles.sectionTitle}>Financial</Text>

            <View style={styles.row}>
              <View style={{ flex: 2 }}>
                <GlassInput
                  label="Value *"
                  value={value}
                  onChangeText={setValue}
                  placeholder="0.00"
                  keyboardType="numeric"
                />
              </View>
              <View style={{ flex: 1 }}>
                <GlassInput
                  label="Currency"
                  value={currency}
                  onChangeText={setCurrency}
                  placeholder="USD"
                  autoCapitalize="characters"
                />
              </View>
            </View>

            <GlassInput
              label="Payment Terms"
              value={paymentTerms}
              onChangeText={setPaymentTerms}
              placeholder="e.g. Net 30"
              autoCapitalize="words"
            />
          </View>
        </GlassCard>

        {/* Dates */}
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <Text style={styles.sectionTitle}>Timeline</Text>

            <View style={styles.row}>
              <View style={styles.half}>
                <GlassInput
                  label="Start Date"
                  value={startDate}
                  onChangeText={setStartDate}
                  placeholder="YYYY-MM-DD"
                />
              </View>
              <View style={styles.half}>
                <GlassInput
                  label="End Date"
                  value={endDate}
                  onChangeText={setEndDate}
                  placeholder="YYYY-MM-DD"
                />
              </View>
            </View>
          </View>
        </GlassCard>

        {/* Notes */}
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <Text style={styles.sectionTitle}>Notes</Text>
            <View style={styles.textAreaContainer}>
              <TextInput
                style={styles.textArea}
                value={notes}
                onChangeText={setNotes}
                placeholder="Additional notes..."
                placeholderTextColor={colors.text.muted}
                multiline
                numberOfLines={3}
                textAlignVertical="top"
              />
            </View>
          </View>
        </GlassCard>

        {/* Submit */}
        <View style={styles.actions}>
          <GlassButton
            title="Create Contract"
            onPress={handleSubmit}
            variant="primary"
            size="lg"
            loading={createContract.isPending}
            fullWidth
          />
        </View>
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
    padding: 20,
    paddingBottom: 100,
  },
  card: {
    marginBottom: 20,
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
  inputLabel: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.md,
    color: colors.text.primary,
    marginBottom: 8,
  },
  textAreaContainer: {
    borderWidth: 1,
    borderColor: colors.figma.borders,
    borderRadius: 12,
    backgroundColor: colors.background.secondary,
    padding: 12,
    minHeight: 100,
    marginBottom: 12,
  },
  textArea: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    color: colors.text.primary,
    minHeight: 80,
    lineHeight: 22,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  half: {
    flex: 1,
  },
  chipsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  chip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: colors.figma.lighterElements + '40',
    borderWidth: 1,
    borderColor: colors.figma.lighterElements,
  },
  chipSelected: {
    backgroundColor: colors.primary[500],
    borderColor: colors.primary[500],
  },
  chipText: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.sm,
    color: colors.text.secondary,
  },
  chipTextSelected: {
    color: colors.white,
  },
  actions: {
    paddingVertical: 8,
  },
});

export default ContractCreateScreen;
