/**
 * LoginScreen - Email/password login with glassmorphism
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
  navigation: NativeStackNavigationProp<AuthStackParamList, 'Login'>;
};

const LoginScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();
  const { login, isLoading, error, clearError } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !password.trim()) {
      Alert.alert('Error', 'Please enter email and password');
      return;
    }

    try {
      await login({ email: email.trim(), password });
    } catch {
      // Error is handled by the store
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
            { paddingTop: insets.top + 40, paddingBottom: insets.bottom + 24 },
          ]}
          keyboardShouldPersistTaps="handled"
        >
          {/* Logo */}
          <View style={styles.logoSection}>
            <View style={styles.glassCircle}>
              <Text style={styles.logoText}>A</Text>
            </View>
            <Text style={styles.appName}>Aureon</Text>
          </View>

          {/* Login Card */}
          <GlassCard preset="card" style={styles.card}>
            <View style={styles.cardContent}>
              <Text style={styles.heading}>Welcome back</Text>
              <Text style={styles.subheading}>
                Sign in to manage your finances
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

              <GlassInput
                label="Email"
                value={email}
                onChangeText={setEmail}
                placeholder="you@example.com"
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
                icon={
                  <Icon name="mail-outline" size={20} color={colors.text.muted} />
                }
              />

              <GlassInput
                label="Password"
                value={password}
                onChangeText={setPassword}
                placeholder="Enter your password"
                secureTextEntry={!showPassword}
                icon={
                  <Icon
                    name="lock-closed-outline"
                    size={20}
                    color={colors.text.muted}
                  />
                }
                iconRight={
                  <Pressable onPress={() => setShowPassword(!showPassword)}>
                    <Icon
                      name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                      size={20}
                      color={colors.text.muted}
                    />
                  </Pressable>
                }
              />

              <Pressable style={styles.forgotLink}>
                <Text style={styles.linkText}>Forgot password?</Text>
              </Pressable>

              <GlassButton
                title="Sign In"
                onPress={handleLogin}
                variant="primary"
                size="lg"
                loading={isLoading}
                fullWidth
              />

              <View style={styles.registerRow}>
                <Text style={styles.registerText}>
                  Don't have an account?{' '}
                </Text>
                <Pressable onPress={() => navigation.navigate('Register')}>
                  <Text style={styles.registerLink}>Sign Up</Text>
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
  logoSection: {
    alignItems: 'center',
    marginBottom: 32,
  },
  glassCircle: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.25)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
  },
  logoText: {
    fontFamily: fontFamily.bold,
    fontSize: 32,
    color: colors.white,
  },
  appName: {
    fontFamily: fontFamily.bold,
    fontSize: fontSize['3xl'],
    color: colors.white,
  },
  card: {
    width: '100%',
  },
  cardContent: {
    padding: 24,
  },
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
  forgotLink: {
    alignSelf: 'flex-end',
    marginBottom: 24,
    marginTop: -8,
  },
  linkText: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.sm,
    color: colors.accent[400],
  },
  registerRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 24,
  },
  registerText: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  registerLink: {
    fontFamily: fontFamily.semiBold,
    fontSize: fontSize.md,
    color: colors.accent[400],
  },
});

export default LoginScreen;
