/**
 * SettingsScreen - Profile and app settings with glassmorphism
 */

import React from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable, Alert } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Ionicons';
import { GlassCard, GlassButton } from '@components/glass';
import { Avatar } from '@components/common';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { useAuthStore } from '@store/authStore';

const SettingsScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    Alert.alert('Logout', 'Are you sure you want to sign out?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Sign Out', style: 'destructive', onPress: () => logout() },
    ]);
  };

  const settingsGroups = [
    {
      title: 'Account',
      items: [
        { icon: 'person-outline', label: 'Profile', onPress: () => navigation.navigate('Profile') },
        { icon: 'shield-outline', label: 'Security', onPress: () => {} },
        { icon: 'notifications-outline', label: 'Notifications', onPress: () => {} },
      ],
    },
    {
      title: 'Finance',
      items: [
        { icon: 'card-outline', label: 'Payments', onPress: () => navigation.navigate('PaymentList') },
        { icon: 'document-text-outline', label: 'All Contracts', onPress: () => navigation.navigate('ContractListAll') },
      ],
    },
    {
      title: 'About',
      items: [
        { icon: 'help-circle-outline', label: 'Help & Support', onPress: () => {} },
        { icon: 'information-circle-outline', label: 'About Aureon', onPress: () => {} },
      ],
    },
  ];

  return (
    <ScrollView style={[styles.container, { paddingTop: insets.top }]} contentContainerStyle={styles.scrollContent}>
      <Text style={styles.pageTitle}>Settings</Text>

      {/* Profile Card */}
      <GlassCard preset="cardSolid" style={styles.profileCard} onPress={() => navigation.navigate('Profile')}>
        <View style={styles.profileContent}>
          <Avatar name={user?.full_name} src={user?.avatar} size="lg" />
          <View style={styles.profileInfo}>
            <Text style={styles.profileName}>{user?.full_name || 'User'}</Text>
            <Text style={styles.profileEmail}>{user?.email}</Text>
            <Text style={styles.profileRole}>{user?.role}</Text>
          </View>
          <Icon name="chevron-forward" size={20} color={colors.text.muted} />
        </View>
      </GlassCard>

      {/* Settings Groups */}
      {settingsGroups.map((group) => (
        <View key={group.title}>
          <Text style={styles.groupTitle}>{group.title}</Text>
          <GlassCard preset="cardSolid" style={styles.groupCard}>
            <View>
              {group.items.map((item, index) => (
                <Pressable key={item.label} onPress={item.onPress} style={({ pressed }) => [styles.settingItem, { opacity: pressed ? 0.7 : 1 }]}>
                  <Icon name={item.icon} size={22} color={colors.text.secondary} />
                  <Text style={styles.settingLabel}>{item.label}</Text>
                  <Icon name="chevron-forward" size={18} color={colors.text.muted} />
                </Pressable>
              ))}
            </View>
          </GlassCard>
        </View>
      ))}

      {/* Logout */}
      <View style={styles.logoutSection}>
        <GlassButton title="Sign Out" onPress={handleLogout} variant="danger" fullWidth icon={<Icon name="log-out-outline" size={20} color={colors.danger} />} />
      </View>

      <Text style={styles.version}>Aureon Mobile v1.0.0</Text>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background.primary },
  scrollContent: { paddingBottom: 100 },
  pageTitle: { fontFamily: fontFamily.bold, fontSize: fontSize['3xl'], color: colors.text.primary, paddingHorizontal: 20, paddingVertical: 16 },
  profileCard: { marginHorizontal: 20, marginBottom: 24 },
  profileContent: { flexDirection: 'row', alignItems: 'center', padding: 16 },
  profileInfo: { flex: 1, marginLeft: 16 },
  profileName: { fontFamily: fontFamily.semiBold, fontSize: fontSize.xl, color: colors.text.primary },
  profileEmail: { fontFamily: fontFamily.regular, fontSize: fontSize.sm, color: colors.text.secondary, marginTop: 2 },
  profileRole: { fontFamily: fontFamily.medium, fontSize: fontSize.sm, color: colors.primary[500], marginTop: 2, textTransform: 'capitalize' },
  groupTitle: { fontFamily: fontFamily.semiBold, fontSize: fontSize.md, color: colors.text.secondary, paddingHorizontal: 20, marginBottom: 8 },
  groupCard: { marginHorizontal: 20, marginBottom: 20 },
  settingItem: { flexDirection: 'row', alignItems: 'center', paddingVertical: 14, paddingHorizontal: 16, gap: 14 },
  settingLabel: { flex: 1, fontFamily: fontFamily.medium, fontSize: fontSize.lg, color: colors.text.primary },
  logoutSection: { paddingHorizontal: 20, marginTop: 8 },
  version: { fontFamily: fontFamily.regular, fontSize: fontSize.sm, color: colors.text.muted, textAlign: 'center', marginTop: 24, marginBottom: 16 },
});

export default SettingsScreen;
