/**
 * ClientEditScreen - Edit existing client form
 */

import React, { useState, useEffect } from 'react';
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
import { RouteProp } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Ionicons';
import { GlassCard, GlassHeader, GlassButton, GlassInput } from '@components/glass';
import { Badge, LoadingSpinner } from '@components/common';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { useClient, useUpdateClient } from '@hooks/useClients';
import { ClientType, LifecycleStage } from '@/types';
import type { ClientStackParamList } from '@types/navigation';

type Props = {
  navigation: NativeStackNavigationProp<ClientStackParamList, 'ClientEdit'>;
  route: RouteProp<ClientStackParamList, 'ClientEdit'>;
};

const LIFECYCLE_STAGES: { value: LifecycleStage; label: string }[] = [
  { value: LifecycleStage.LEAD, label: 'Lead' },
  { value: LifecycleStage.PROSPECT, label: 'Prospect' },
  { value: LifecycleStage.ACTIVE, label: 'Active' },
  { value: LifecycleStage.CHURNED, label: 'Churned' },
  { value: LifecycleStage.ARCHIVED, label: 'Archived' },
];

const ClientEditScreen: React.FC<Props> = ({ navigation, route }) => {
  const { clientId } = route.params;
  const { data: client, isLoading } = useClient(clientId);
  const updateClient = useUpdateClient();

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [website, setWebsite] = useState('');
  const [address, setAddress] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [postalCode, setPostalCode] = useState('');
  const [country, setCountry] = useState('');
  const [lifecycleStage, setLifecycleStage] = useState<LifecycleStage>(LifecycleStage.LEAD);
  const [notes, setNotes] = useState('');
  const [tagsInput, setTagsInput] = useState('');

  // Pre-populate form fields when client data loads
  useEffect(() => {
    if (client) {
      setFirstName(client.first_name || '');
      setLastName(client.last_name || '');
      setEmail(client.email || '');
      setPhone(client.phone_number || '');
      setCompanyName(client.company_name || '');
      setWebsite(client.website || '');
      setAddress(client.address || '');
      setCity(client.city || '');
      setState(client.state || '');
      setPostalCode(client.postal_code || '');
      setCountry(client.country || '');
      setLifecycleStage(client.lifecycle_stage || LifecycleStage.LEAD);
      setNotes(client.notes || '');
      setTagsInput(client.tags?.join(', ') || '');
    }
  }, [client]);

  const handleSubmit = async () => {
    if (!email.trim()) {
      Alert.alert('Error', 'Email is required');
      return;
    }

    const tags = tagsInput
      .split(',')
      .map(t => t.trim())
      .filter(Boolean);

    try {
      await updateClient.mutateAsync({
        id: clientId,
        data: {
          type: companyName ? ClientType.COMPANY : ClientType.INDIVIDUAL,
          first_name: firstName,
          last_name: lastName,
          email: email.trim(),
          phone_number: phone || undefined,
          company_name: companyName || undefined,
          website: website || undefined,
          address: address || undefined,
          city: city || undefined,
          state: state || undefined,
          postal_code: postalCode || undefined,
          country: country || undefined,
          lifecycle_stage: lifecycleStage,
          notes: notes || undefined,
          tags: tags.length > 0 ? tags : undefined,
        },
      });
      navigation.goBack();
    } catch {
      Alert.alert('Error', 'Failed to update client');
    }
  };

  if (isLoading || !client) {
    return <LoadingSpinner />;
  }

  return (
    <View style={styles.container}>
      <GlassHeader
        title="Edit Client"
        onBack={() => navigation.goBack()}
      />

      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        {/* Contact Info */}
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
              label="Company"
              value={companyName}
              onChangeText={setCompanyName}
              placeholder="Acme Corp"
              autoCapitalize="words"
            />

            <GlassInput
              label="Website"
              value={website}
              onChangeText={setWebsite}
              placeholder="https://example.com"
              keyboardType="url"
              autoCapitalize="none"
            />
          </View>
        </GlassCard>

        {/* Address */}
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <Text style={styles.sectionTitle}>Address</Text>

            <GlassInput
              label="Street Address"
              value={address}
              onChangeText={setAddress}
              placeholder="123 Main St"
            />

            <View style={styles.row}>
              <View style={styles.half}>
                <GlassInput
                  label="City"
                  value={city}
                  onChangeText={setCity}
                  placeholder="New York"
                  autoCapitalize="words"
                />
              </View>
              <View style={styles.half}>
                <GlassInput
                  label="State"
                  value={state}
                  onChangeText={setState}
                  placeholder="NY"
                  autoCapitalize="characters"
                />
              </View>
            </View>

            <View style={styles.row}>
              <View style={styles.half}>
                <GlassInput
                  label="Postal Code"
                  value={postalCode}
                  onChangeText={setPostalCode}
                  placeholder="10001"
                  keyboardType="number-pad"
                />
              </View>
              <View style={styles.half}>
                <GlassInput
                  label="Country"
                  value={country}
                  onChangeText={setCountry}
                  placeholder="US"
                  autoCapitalize="characters"
                />
              </View>
            </View>
          </View>
        </GlassCard>

        {/* Lifecycle Stage */}
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <Text style={styles.sectionTitle}>Lifecycle Stage</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.chipsRow}
            >
              {LIFECYCLE_STAGES.map(stage => {
                const isSelected = lifecycleStage === stage.value;
                return (
                  <Pressable
                    key={stage.value}
                    onPress={() => setLifecycleStage(stage.value)}
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
                      {stage.label}
                    </Text>
                  </Pressable>
                );
              })}
            </ScrollView>
          </View>
        </GlassCard>

        {/* Tags & Notes */}
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <Text style={styles.sectionTitle}>Additional Info</Text>

            <GlassInput
              label="Tags (comma separated)"
              value={tagsInput}
              onChangeText={setTagsInput}
              placeholder="vip, enterprise, referral"
              autoCapitalize="none"
            />

            <Text style={styles.inputLabel}>Notes</Text>
            <View style={styles.textAreaContainer}>
              <TextInput
                style={styles.textArea}
                value={notes}
                onChangeText={setNotes}
                placeholder="Add notes about this client..."
                placeholderTextColor={colors.text.muted}
                multiline
                numberOfLines={4}
                textAlignVertical="top"
              />
            </View>
          </View>
        </GlassCard>

        {/* Submit */}
        <View style={styles.actions}>
          <GlassButton
            title="Save Changes"
            onPress={handleSubmit}
            variant="primary"
            size="lg"
            loading={updateClient.isPending}
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
    textTransform: 'capitalize',
  },
  chipTextSelected: {
    color: colors.white,
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
  },
  textArea: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    color: colors.text.primary,
    minHeight: 80,
    lineHeight: 22,
  },
  actions: {
    paddingVertical: 8,
  },
});

export default ClientEditScreen;
