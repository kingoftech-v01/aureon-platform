/**
 * GlassInput - Glassmorphism styled text input
 */

import React, { useState } from 'react';
import {
  View,
  TextInput,
  Text,
  StyleSheet,
  ViewStyle,
  StyleProp,
  TextInputProps,
} from 'react-native';
import { BlurView } from '@react-native-community/blur';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { glassPresets } from '@theme/glassmorphism';

interface GlassInputProps extends Omit<TextInputProps, 'style'> {
  label?: string;
  error?: string;
  hint?: string;
  icon?: React.ReactNode;
  iconRight?: React.ReactNode;
  containerStyle?: StyleProp<ViewStyle>;
}

const GlassInput: React.FC<GlassInputProps> = ({
  label,
  error,
  hint,
  icon,
  iconRight,
  containerStyle,
  ...inputProps
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const glass = glassPresets.input;

  return (
    <View style={[styles.wrapper, containerStyle]}>
      {label && <Text style={styles.label}>{label}</Text>}

      <View
        style={[
          styles.container,
          {
            borderRadius: glass.borderRadius,
            borderWidth: isFocused ? 1.5 : glass.borderWidth,
            borderColor: error
              ? colors.danger
              : isFocused
                ? colors.primary[400]
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

        <View style={styles.inputRow}>
          {icon && <View style={styles.iconLeft}>{icon}</View>}
          <TextInput
            {...inputProps}
            style={[
              styles.input,
              icon ? { paddingLeft: 0 } : null,
              iconRight ? { paddingRight: 0 } : null,
            ]}
            placeholderTextColor={colors.text.muted}
            onFocus={(e) => {
              setIsFocused(true);
              inputProps.onFocus?.(e);
            }}
            onBlur={(e) => {
              setIsFocused(false);
              inputProps.onBlur?.(e);
            }}
          />
          {iconRight && <View style={styles.iconRight}>{iconRight}</View>}
        </View>
      </View>

      {error && <Text style={styles.error}>{error}</Text>}
      {hint && !error && <Text style={styles.hint}>{hint}</Text>}
    </View>
  );
};

const styles = StyleSheet.create({
  wrapper: {
    marginBottom: 16,
  },
  label: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.md,
    color: colors.text.primary,
    marginBottom: 8,
  },
  container: {
    minHeight: 52,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    zIndex: 1,
  },
  input: {
    flex: 1,
    fontFamily: fontFamily.regular,
    fontSize: fontSize.lg,
    color: colors.text.primary,
    paddingVertical: 14,
  },
  iconLeft: {
    marginRight: 12,
  },
  iconRight: {
    marginLeft: 12,
  },
  error: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.sm,
    color: colors.danger,
    marginTop: 4,
  },
  hint: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.sm,
    color: colors.text.muted,
    marginTop: 4,
  },
});

export default GlassInput;
