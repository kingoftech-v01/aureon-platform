/**
 * CurrencyText - Formatted currency display
 */

import React from 'react';
import { Text, TextStyle, StyleProp } from 'react-native';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';

interface CurrencyTextProps {
  amount: number;
  currency?: string;
  style?: StyleProp<TextStyle>;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const CurrencyText: React.FC<CurrencyTextProps> = ({
  amount,
  currency = 'USD',
  style,
  size = 'md',
}) => {
  const formatted = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);

  const sizeStyles: Record<string, TextStyle> = {
    sm: { fontSize: fontSize.sm, fontFamily: fontFamily.medium },
    md: { fontSize: fontSize.lg, fontFamily: fontFamily.semiBold },
    lg: { fontSize: fontSize['2xl'], fontFamily: fontFamily.bold },
    xl: { fontSize: fontSize['4xl'], fontFamily: fontFamily.bold },
  };

  return (
    <Text style={[{ color: colors.text.primary }, sizeStyles[size], style]}>
      {formatted}
    </Text>
  );
};

export default CurrencyText;
