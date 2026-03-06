/**
 * Badge - Status indicator component
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';

type BadgeVariant = 'default' | 'primary' | 'success' | 'warning' | 'danger' | 'info';

interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
  size?: 'sm' | 'md';
}

const variantColors: Record<BadgeVariant, { bg: string; text: string }> = {
  default: { bg: '#f1f5f9', text: colors.text.muted },
  primary: { bg: colors.primary[50], text: colors.primary[700] },
  success: { bg: colors.successLight, text: '#065f46' },
  warning: { bg: colors.warningLight, text: '#92400e' },
  danger: { bg: colors.dangerLight, text: '#991b1b' },
  info: { bg: colors.infoLight, text: '#1e40af' },
};

const Badge: React.FC<BadgeProps> = ({ label, variant = 'default', size = 'sm' }) => {
  const scheme = variantColors[variant];

  return (
    <View
      style={[
        styles.container,
        { backgroundColor: scheme.bg },
        size === 'md' && styles.md,
      ]}
    >
      <Text
        style={[
          styles.text,
          { color: scheme.text },
          size === 'md' && styles.textMd,
        ]}
      >
        {label}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  md: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
  },
  text: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.xs,
    textTransform: 'capitalize',
  },
  textMd: {
    fontSize: fontSize.sm,
  },
});

export default Badge;
