/**
 * GlassButton - Glassmorphism styled button
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  ActivityIndicator,
  ViewStyle,
  StyleProp,
} from 'react-native';
import { BlurView } from '@react-native-community/blur';
import LinearGradient from 'react-native-linear-gradient';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { glassPresets } from '@theme/glassmorphism';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface GlassButtonProps {
  title: string;
  onPress: () => void;
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  disabled?: boolean;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
  fullWidth?: boolean;
  style?: StyleProp<ViewStyle>;
}

const GlassButton: React.FC<GlassButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  icon,
  iconRight,
  fullWidth = false,
  style,
}) => {
  const glass = glassPresets.button;
  const sizeStyles = sizes[size];
  const isDisabled = disabled || loading;

  if (variant === 'primary') {
    return (
      <Pressable
        onPress={onPress}
        disabled={isDisabled}
        style={({ pressed }) => [
          { opacity: pressed ? 0.85 : isDisabled ? 0.5 : 1 },
          fullWidth && styles.fullWidth,
          style,
        ]}
      >
        <LinearGradient
          colors={[colors.primary[500], colors.primary[600]]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={[
            styles.container,
            sizeStyles.container,
            { borderRadius: glass.borderRadius },
            glass.shadow,
          ]}
        >
          {loading ? (
            <ActivityIndicator color={colors.white} size="small" />
          ) : (
            <View style={styles.row}>
              {icon && <View style={styles.iconLeft}>{icon}</View>}
              <Text style={[styles.text, sizeStyles.text, styles.textInverse]}>
                {title}
              </Text>
              {iconRight && <View style={styles.iconRight}>{iconRight}</View>}
            </View>
          )}
        </LinearGradient>
      </Pressable>
    );
  }

  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      style={({ pressed }) => [
        { opacity: pressed ? 0.85 : isDisabled ? 0.5 : 1 },
        fullWidth && styles.fullWidth,
        style,
      ]}
    >
      <View
        style={[
          styles.container,
          sizeStyles.container,
          {
            borderRadius: glass.borderRadius,
            borderWidth: glass.borderWidth,
            borderColor:
              variant === 'danger'
                ? colors.danger
                : variant === 'ghost'
                  ? colors.transparent
                  : glass.borderColor,
            overflow: 'hidden',
          },
          glass.shadow,
        ]}
      >
        <BlurView
          blurType={glass.blurType}
          blurAmount={glass.blurAmount}
          style={StyleSheet.absoluteFill}
          reducedTransparencyFallbackColor="white"
        />
        <View
          style={[
            StyleSheet.absoluteFill,
            { backgroundColor: glass.backgroundColor },
          ]}
        />
        {loading ? (
          <ActivityIndicator
            color={variant === 'danger' ? colors.danger : colors.primary[500]}
            size="small"
          />
        ) : (
          <View style={[styles.row, { zIndex: 1 }]}>
            {icon && <View style={styles.iconLeft}>{icon}</View>}
            <Text
              style={[
                styles.text,
                sizeStyles.text,
                {
                  color:
                    variant === 'danger'
                      ? colors.danger
                      : colors.text.primary,
                },
              ]}
            >
              {title}
            </Text>
            {iconRight && <View style={styles.iconRight}>{iconRight}</View>}
          </View>
        )}
      </View>
    </Pressable>
  );
};

const sizes: Record<ButtonSize, { container: ViewStyle; text: any }> = {
  sm: {
    container: { paddingVertical: 8, paddingHorizontal: 16 },
    text: { fontSize: fontSize.sm },
  },
  md: {
    container: { paddingVertical: 14, paddingHorizontal: 24 },
    text: { fontSize: fontSize.lg },
  },
  lg: {
    container: { paddingVertical: 18, paddingHorizontal: 32 },
    text: { fontSize: fontSize.xl },
  },
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  fullWidth: {
    width: '100%',
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  text: {
    fontFamily: fontFamily.semiBold,
    color: colors.text.primary,
  },
  textInverse: {
    color: colors.white,
  },
  iconLeft: {
    marginRight: 8,
  },
  iconRight: {
    marginLeft: 8,
  },
});

export default GlassButton;
