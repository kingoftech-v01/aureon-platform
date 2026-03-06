/**
 * ClientCreateScreen - Create new client form
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, Alert } from 'react-native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { GlassCard, GlassHeader, GlassButton, GlassInput } from '@components/glass';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { useCreateClient } from '@hooks/useClients';
import { ClientType, LifecycleStage } from '@/types';
import type { ClientStackParamList } from '@types/navigation';

type Props = {
  navigation: NativeStackNavigationProp<ClientStackParamList, 'ClientCreate'>;
};

const ClientCreateScreen: React.FC<Props> = ({ navigation }) => {
  const createClient = useCreateClient();

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [companyName, setCompanyName] = useState('');

  const handleSubmit = async () => {
    if (!email.trim()) {
      Alert.alert('Error', 'Email is required');
      return;
    }

    try {
      await createClient.mutateAsync({
        type: companyName ? ClientType.COMPANY : ClientType.INDIVIDUAL,
        first_name: firstName,
        last_name: lastName,
        email: email.trim(),
        phone_number: phone,
        company_name: companyName || undefined,
        lifecycle_stage: LifecycleStage.LEAD,
      });
      navigation.goBack();
    } catch {
      Alert.alert('Error', 'Failed to create client');
    }
  };

  return (
    <View style={styles.container}>
      <GlassHeader
        title="New Client"
        onBack={() => navigation.goBack()}
      />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <Text style={styles.sectionTitle}>Contact Info</Text>

            <View style={styles.row}>
              <View style={styles.half}>
                <GlassInput
                  label="First Name"
                  value={firstName}
                  onChangeText={setFirstName}
                  placeholder="John"
                  autoCapitalize="words"
                />
              </View>
              <View style={styles.half}>
                <GlassInput
                  label="Last Name"
                  value={lastName}
                  onChangeText={setLastName}
                  placeholder="Doe"
                  autoCapitalize="words"
                />
              </View>
            </View>

            <GlassInput
              label="Email *"
              value={email}
              onChangeText={setEmail}
              placeholder="john@example.com"
              keyboardType="email-address"
              autoCapitalize="none"
            />

            <GlassInput
              label="Phone"
              value={phone}
              onChangeText={setPhone}
              placeholder="+1 (555) 000-0000"
              keyboardType="phone-pad"
            />

            <GlassInput
              label="Company (optional)"
              value={companyName}
              onChangeText={setCompanyName}
              placeholder="Acme Corp"
              autoCapitalize="words"
            />
          </View>
        </GlassCard>

        <View style={styles.actions}>
          <GlassButton
            title="Create Client"
            onPress={handleSubmit}
            variant="primary"
            size="lg"
            loading={createClient.isPending}
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
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  half: {
    flex: 1,
  },
  actions: {
    paddingVertical: 8,
  },
});

export default ClientCreateScreen;
