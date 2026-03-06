/**
 * ForgotPasswordScreen - Password reset request with glassmorphism
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
} from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Ionicons';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { GlassCard, GlassButton, GlassInput, GlassHeader } from '@components/glass';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { authService } from '@services/authService';
import type { AuthStackParamList } from '@types/navigation';

type Props = {
  navigation: NativeStackNavigationProp<AuthStackParamList, 'ForgotPassword'>;
};

const ForgotPasswordScreen: React.FC<Props> = ({ navigation }) => {
  const insets = useSafeAreaInsets();

  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async () => {
    if (!email.trim()) {
      setError('Please enter your email address');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await authService.requestPasswordReset(email.trim());
      setSuccess(true);
    } catch (err: any) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.message ||
        'Failed to send reset link. Please try again.';
      setError(message);
    } finally {
      setLoading(false);
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
          {/* Header */}
          <Pressable style={styles.backButton} onPress={() => navigation.goBack()}>
            <Icon name="arrow-back" size={24} color={colors.white} />
          </Pressable>

          <GlassCard preset="card" style={styles.card}>
            <View style={styles.cardContent}>
              {success ? (
                /* Success State */
                <View style={styles.successContainer}>
                  <View style={styles.successIconCircle}>
                    <Icon name="mail-open-outline" size={48} color={colors.accent[400]} />
                  </View>
                  <Text style={styles.heading}>Check your email</Text>
                  <Text style={styles.subheading}>
                    We've sent a password reset link to{'\n'}
                    <Text style={styles.emailHighlight}>{email}</Text>
                  </Text>
                  <Text style={styles.instructionText}>
                    If you don't see the email, check your spam folder or try again.
                  </Text>

                  <GlassButton
                    title="Back to Sign In"
                    onPress={() => navigation.navigate('Login')}
                    variant="primary"
                    size="lg"
                    fullWidth
                  />
                </View>
              ) : (
                /* Form State */
                <>
                  <Text style={styles.heading}>Reset Password</Text>
                  <Text style={styles.subheading}>
                    Enter your email address and we'll send you a link to reset your password.
                  </Text>

                  {error && (
                    <View style={styles.errorBanner}>
                      <Icon name="alert-circle" size={18} color={colors.danger} />
                      <Text style={styles.errorText}>{error}</Text>
                      <Pressable onPress={() => setError(null)}>
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

                  <GlassButton
                    title="Send Reset Link"
                    onPress={handleSubmit}
                    variant="primary"
                    size="lg"
                    loading={loading}
                    fullWidth
                  />

                  <View style={styles.backRow}>
                    <Pressable onPress={() => navigation.navigate('Login')}>
                      <Text style={styles.backLink}>Back to Sign In</Text>
                    </Pressable>
                  </View>
                </>
              )}
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
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
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
    lineHeight: 22,
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
  backRow: {
    alignItems: 'center',
    marginTop: 24,
  },
  backLink: {
    fontFamily: fontFamily.semiBold,
    fontSize: fontSize.md,
    color: colors.accent[400],
  },
  successContainer: {
    alignItems: 'center',
  },
  successIconCircle: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  emailHighlight: {
    fontFamily: fontFamily.semiBold,
    color: colors.accent[400],
  },
  instructionText: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.sm,
    color: 'rgba(255, 255, 255, 0.5)',
    textAlign: 'center',
    marginBottom: 32,
    lineHeight: 20,
  },
});

export default ForgotPasswordScreen;
