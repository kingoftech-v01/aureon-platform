/**
 * StatCard - KPI stat display with glassmorphism
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { GlassCard } from '@components/glass';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';

interface StatCardProps {
  title: string;
  value: string;
  subtitle?: string;
  icon?: React.ReactNode;
  accentColor?: string;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  icon,
  accentColor = colors.primary[500],
}) => {
  return (
    <GlassCard preset="cardSolid" style={styles.card}>
      <View style={styles.content}>
        <View style={styles.header}>
          {icon && (
            <View
              style={[styles.iconWrapper, { backgroundColor: accentColor + '20' }]}
            >
              {icon}
            </View>
          )}
          <Text style={styles.title}>{title}</Text>
        </View>
        <Text style={styles.value}>{value}</Text>
        {subtitle && <Text style={styles.subtitle}>{subtitle}</Text>}
      </View>
    </GlassCard>
  );
};

const styles = StyleSheet.create({
  card: {
    width: 160,
    marginRight: 12,
  },
  content: {
    padding: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  iconWrapper: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 8,
  },
  title: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.sm,
    color: colors.text.secondary,
    flex: 1,
  },
  value: {
    fontFamily: fontFamily.bold,
    fontSize: fontSize['3xl'],
    color: colors.text.primary,
    marginBottom: 2,
  },
  subtitle: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.sm,
    color: colors.text.muted,
  },
});

export default StatCard;
