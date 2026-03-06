/**
 * RegisterScreen - Account creation with glassmorphism
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  Alert,
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Ionicons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { GlassCard, GlassButton, GlassInput } from '@components/glass';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { useAuthStore } from '@store/authStore';
import type { AuthStackParamList } from '@types/navigation';

type Props = {
  navigation: NativeStackNavigationProp<AuthStackParamList, 'Register'>;
};

const RegisterScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { register, isLoading, error, clearError } = useAuthStore();

  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleRegister = async () => {
    if (!firstName || !lastName || !email || !password) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }
    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }

    try {
      await register({
        first_name: firstName,
        last_name: lastName,
        email: email.trim(),
        password,
        password_confirm: confirmPassword,
      });
    } catch {
      // Error handled by store
    }
  };

  return (
    <LinearGradient
      colors={[colors.primary[700], colors.primary[900]]}
      style={styles.gradient}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.flex}
      >
        <ScrollView
          contentContainerStyle={[
            styles.scrollContent,
            { paddingTop: insets.top + 20, paddingBottom: insets.bottom + 24 },
          ]}
          keyboardShouldPersistTaps="handled"
        >
          <GlassCard preset="card" style={styles.card}>
            <View style={styles.cardContent}>
              <Text style={styles.heading}>Create Account</Text>
              <Text style={styles.subheading}>
                Start managing your finances today
              </Text>

              {error && (
                <View style={styles.errorBanner}>
                  <Icon name="alert-circle" size={18} color={colors.danger} />
                  <Text style={styles.errorText}>{error}</Text>
                  <Pressable onPress={clearError}>
                    <Icon name="close" size={18} color={colors.danger} />
                  </Pressable>
                </View>
              )}

              <View style={styles.row}>
                <View style={styles.halfInput}>
                  <GlassInput
                    label="First Name"
                    value={firstName}
                    onChangeText={setFirstName}
                    placeholder="John"
                    autoCapitalize="words"
                  />
                </View>
                <View style={styles.halfInput}>
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
                label="Email"
                value={email}
                onChangeText={setEmail}
                placeholder="you@example.com"
                keyboardType="email-address"
                autoCapitalize="none"
                icon={
                  <Icon name="mail-outline" size={20} color={colors.text.muted} />
                }
              />

              <GlassInput
                label="Password"
                value={password}
                onChangeText={setPassword}
                placeholder="Min 8 characters"
                secureTextEntry
                icon={
                  <Icon name="lock-closed-outline" size={20} color={colors.text.muted} />
                }
              />

              <GlassInput
                label="Confirm Password"
                value={confirmPassword}
                onChangeText={setConfirmPassword}
                placeholder="Re-enter password"
                secureTextEntry
                icon={
                  <Icon name="lock-closed-outline" size={20} color={colors.text.muted} />
                }
              />

              <GlassButton
                title="Create Account"
                onPress={handleRegister}
                variant="primary"
                size="lg"
                loading={isLoading}
                fullWidth
              />

              <View style={styles.loginRow}>
                <Text style={styles.loginText}>Already have an account? </Text>
                <Pressable onPress={() => navigation.navigate('Login')}>
                  <Text style={styles.loginLink}>Sign In</Text>
                </Pressable>
              </View>
            </View>
          </GlassCard>
        </ScrollView>
      </KeyboardAvoidingView>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  flex: { flex: 1 },
  gradient: { flex: 1 },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 24,
    justifyContent: 'center',
  },
  card: { width: '100%' },
  cardContent: { padding: 24 },
  heading: {
    fontFamily: fontFamily.bold,
    fontSize: fontSize['3xl'],
    color: colors.white,
    marginBottom: 4,
  },
  subheading: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: 24,
  },
  errorBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.dangerLight,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 10,
    marginBottom: 16,
    gap: 8,
  },
  errorText: {
    flex: 1,
    fontFamily: fontFamily.regular,
    fontSize: fontSize.sm,
    color: colors.danger,
  },
  row: {
    flexDirection: 'row',
    gap: 12,
  },
  halfInput: { flex: 1 },
  loginRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 24,
  },
  loginText: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  loginLink: {
    fontFamily: fontFamily.semiBold,
    fontSize: fontSize.md,
    color: colors.accent[400],
  },
});

export default RegisterScreen;
