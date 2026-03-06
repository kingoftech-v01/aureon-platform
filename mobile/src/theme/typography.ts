/**
 * Aureon Mobile Typography
 */

import { TextStyle } from 'react-native';

export const fontFamily = {
  regular: 'Inter-Regular',
  medium: 'Inter-Medium',
  semiBold: 'Inter-SemiBold',
  bold: 'Inter-Bold',
} as const;

export const fontSize = {
  xs: 10,
  sm: 12,
  md: 14,
  lg: 16,
  xl: 18,
  '2xl': 20,
  '3xl': 24,
  '4xl': 30,
  '5xl': 36,
} as const;

export const textStyles: Record<string, TextStyle> = {
  h1: {
    fontFamily: fontFamily.bold,
    fontSize: fontSize['4xl'],
    lineHeight: 36,
  },
  h2: {
    fontFamily: fontFamily.bold,
    fontSize: fontSize['3xl'],
    lineHeight: 30,
  },
  h3: {
    fontFamily: fontFamily.semiBold,
    fontSize: fontSize['2xl'],
    lineHeight: 26,
  },
  h4: {
    fontFamily: fontFamily.semiBold,
    fontSize: fontSize.xl,
    lineHeight: 24,
  },
  body: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.lg,
    lineHeight: 22,
  },
  bodySmall: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    lineHeight: 20,
  },
  caption: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.sm,
    lineHeight: 16,
  },
  label: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.md,
    lineHeight: 18,
  },
  button: {
    fontFamily: fontFamily.semiBold,
    fontSize: fontSize.lg,
    lineHeight: 20,
  },
};
