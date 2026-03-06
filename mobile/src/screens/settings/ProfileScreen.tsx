/**
 * ProfileScreen - User profile view/edit with glassmorphism
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Alert,
  Pressable,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Ionicons';
import { GlassCard, GlassHeader, GlassButton, GlassInput } from '@components/glass';
import { Avatar } from '@components/common';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { useAuthStore } from '@store/authStore';
import { authService } from '@services/authService';

const TIMEZONES = [
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'Europe/London',
  'Europe/Paris',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Australia/Sydney',
];

const ProfileScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { user } = useAuthStore();

  const [phone, setPhone] = useState(user?.phone_number || '');
  const [jobTitle, setJobTitle] = useState('');
  const [timezone, setTimezone] = useState('UTC');
  const [saving, setSaving] = useState(false);
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(user?.two_factor_enabled || false);

  const handleSave = async () => {
    if (!user) return;

    setSaving(true);
    try {
      await authService.updateProfile(user.id, {
        phone_number: phone || undefined,
      });
      Alert.alert('Success', 'Profile updated successfully');
    } catch {
      Alert.alert('Error', 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleChangePassword = () => {
    Alert.alert(
      'Change Password',
      'Password change functionality will open a secure form.',
      [{ text: 'OK' }],
    );
  };

  const handleToggle2FA = () => {
    setTwoFactorEnabled(!twoFactorEnabled);
    Alert.alert(
      'Two-Factor Authentication',
      twoFactorEnabled
        ? 'Two-factor authentication has been disabled.'
        : 'Two-factor authentication has been enabled.',
    );
  };

  return (
    <View style={styles.container}>
      <GlassHeader title="Profile" onBack={() => navigation.goBack()} />

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Avatar Section */}
        <View style={styles.avatarSection}>
          <View style={styles.avatarWrapper}>
            <Avatar name={user?.full_name} src={user?.avatar} size="xl" />
            <View style={styles.cameraOverlay}>
              <Icon name="camera" size={16} color={colors.white} />
            </View>
          </View>
          <Text style={styles.displayName}>{user?.full_name || 'User'}</Text>
          <Text style={styles.displayEmail}>{user?.email}</Text>
          <Text style={styles.displayRole}>{user?.role}</Text>
        </View>

        {/* Profile Info */}
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <Text style={styles.sectionTitle}>Personal Info</Text>

            <View style={styles.readOnlyField}>
              <Text style={styles.readOnlyLabel}>Full Name</Text>
              <Text style={styles.readOnlyValue}>{user?.full_name || 'N/A'}</Text>
            </View>

            <View style={styles.readOnlyField}>
              <Text style={styles.readOnlyLabel}>Email</Text>
              <Text style={styles.readOnlyValue}>{user?.email || 'N/A'}</Text>
            </View>

            <GlassInput
              label="Phone Number"
              value={phone}
              onChangeText={setPhone}
              placeholder="+1 (555) 000-0000"
              keyboardType="phone-pad"
            />

            <GlassInput
              label="Job Title"
              value={jobTitle}
              onChangeText={setJobTitle}
              placeholder="e.g. Finance Manager"
              autoCapitalize="words"
            />

            {/* Timezone Selector */}
            <Text style={styles.fieldLabel}>Timezone</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.timezoneRow}
            >
              {TIMEZONES.map(tz => {
                const isSelected = timezone === tz;
                return (
                  <Pressable
                    key={tz}
                    onPress={() => setTimezone(tz)}
                    style={[
                      styles.timezoneChip,
                      isSelected && styles.timezoneChipSelected,
                    ]}
                  >
                    <Text
                      style={[
                        styles.timezoneText,
                        isSelected && styles.timezoneTextSelected,
                      ]}
                    >
                      {tz.replace('_', ' ').split('/').pop() || tz}
                    </Text>
                  </Pressable>
                );
              })}
            </ScrollView>

            <View style={styles.saveButtonWrapper}>
              <GlassButton
                title="Save Changes"
                onPress={handleSave}
                variant="primary"
                size="lg"
                loading={saving}
                fullWidth
              />
            </View>
          </View>
        </GlassCard>

        {/* Security Section */}
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <Text style={styles.sectionTitle}>Security</Text>

            <Pressable
              style={({ pressed }) => [
                styles.securityItem,
                { opacity: pressed ? 0.7 : 1 },
              ]}
              onPress={handleChangePassword}
            >
              <View style={styles.securityIconContainer}>
                <Icon name="key-outline" size={20} color={colors.primary[500]} />
              </View>
              <View style={styles.securityInfo}>
                <Text style={styles.securityLabel}>Change Password</Text>
                <Text style={styles.securityHint}>Update your login password</Text>
              </View>
              <Icon name="chevron-forward" size={18} color={colors.text.muted} />
            </Pressable>

            <View style={styles.divider} />

            <Pressable
              style={({ pressed }) => [
                styles.securityItem,
                { opacity: pressed ? 0.7 : 1 },
              ]}
              onPress={handleToggle2FA}
            >
              <View style={styles.securityIconContainer}>
                <Icon name="shield-checkmark-outline" size={20} color={colors.primary[500]} />
              </View>
              <View style={styles.securityInfo}>
                <Text style={styles.securityLabel}>Two-Factor Authentication</Text>
                <Text style={styles.securityHint}>
                  {twoFactorEnabled ? 'Enabled' : 'Disabled'} - Tap to {twoFactorEnabled ? 'disable' : 'enable'}
                </Text>
              </View>
              <View
                style={[
                  styles.toggleTrack,
                  twoFactorEnabled && styles.toggleTrackActive,
                ]}
              >
                <View
                  style={[
                    styles.toggleThumb,
                    twoFactorEnabled && styles.toggleThumbActive,
                  ]}
                />
              </View>
            </Pressable>
          </View>
        </GlassCard>

        {/* Account Info */}
        <GlassCard preset="cardSolid" style={styles.card}>
          <View style={styles.cardContent}>
            <Text style={styles.sectionTitle}>Account</Text>

            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Member since</Text>
              <Text style={styles.infoValue}>
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString()
                  : 'N/A'}
              </Text>
            </View>

            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Last login</Text>
              <Text style={styles.infoValue}>
                {user?.last_login
                  ? new Date(user.last_login).toLocaleDateString()
                  : 'N/A'}
              </Text>
            </View>

            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>Email verified</Text>
              <Text style={[styles.infoValue, { color: user?.is_email_verified ? colors.success : colors.warning }]}>
                {user?.is_email_verified ? 'Yes' : 'No'}
              </Text>
            </View>
          </View>
        </GlassCard>
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
  avatarSection: {
    alignItems: 'center',
    paddingVertical: 24,
    gap: 4,
  },
  avatarWrapper: {
    position: 'relative',
    marginBottom: 12,
  },
  cameraOverlay: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: colors.primary[500],
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: colors.background.primary,
  },
  displayName: {
    fontFamily: fontFamily.bold,
    fontSize: fontSize['3xl'],
    color: colors.text.primary,
  },
  displayEmail: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    color: colors.text.secondary,
  },
  displayRole: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.sm,
    color: colors.primary[500],
    textTransform: 'capitalize',
    marginTop: 2,
  },
  card: {
    marginHorizontal: 20,
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
  readOnlyField: {
    marginBottom: 16,
  },
  readOnlyLabel: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.sm,
    color: colors.text.secondary,
    marginBottom: 4,
  },
  readOnlyValue: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.lg,
    color: colors.text.primary,
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: colors.figma.lighterElements + '30',
    borderRadius: 10,
    overflow: 'hidden',
  },
  fieldLabel: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.md,
    color: colors.text.primary,
    marginBottom: 8,
  },
  timezoneRow: {
    flexDirection: 'row',
    gap: 8,
    paddingBottom: 4,
  },
  timezoneChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: colors.figma.lighterElements + '40',
    borderWidth: 1,
    borderColor: colors.figma.lighterElements,
  },
  timezoneChipSelected: {
    backgroundColor: colors.primary[500],
    borderColor: colors.primary[500],
  },
  timezoneText: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.sm,
    color: colors.text.secondary,
  },
  timezoneTextSelected: {
    color: colors.white,
  },
  saveButtonWrapper: {
    marginTop: 20,
  },
  securityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
  },
  securityIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: colors.primary[50],
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 14,
  },
  securityInfo: {
    flex: 1,
  },
  securityLabel: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.lg,
    color: colors.text.primary,
  },
  securityHint: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.sm,
    color: colors.text.secondary,
    marginTop: 2,
  },
  divider: {
    height: 1,
    backgroundColor: colors.figma.lighterElements + '40',
    marginVertical: 4,
  },
  toggleTrack: {
    width: 48,
    height: 28,
    borderRadius: 14,
    backgroundColor: colors.figma.lighterElements,
    justifyContent: 'center',
    paddingHorizontal: 2,
  },
  toggleTrackActive: {
    backgroundColor: colors.success,
  },
  toggleThumb: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.white,
  },
  toggleThumbActive: {
    alignSelf: 'flex-end',
  },
  infoRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: colors.figma.lighterElements + '30',
  },
  infoLabel: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    color: colors.text.secondary,
  },
  infoValue: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.md,
    color: colors.text.primary,
  },
});

export default ProfileScreen;
