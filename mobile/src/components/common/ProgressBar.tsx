import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';

interface ProgressBarProps {
  progress: number; // 0-100
  label?: string;
  showPercentage?: boolean;
  color?: string;
  height?: number;
}

const ProgressBar: React.FC<ProgressBarProps> = ({ progress, label, showPercentage = true, color, height = 8 }) => {
  const clampedProgress = Math.min(100, Math.max(0, progress));

  return (
    <View>
      {(label || showPercentage) && (
        <View style={styles.header}>
          {label && <Text style={styles.label}>{label}</Text>}
          {showPercentage && <Text style={styles.percentage}>{Math.round(clampedProgress)}%</Text>}
        </View>
      )}
      <View style={[styles.track, { height }]}>
        <LinearGradient
          colors={color ? [color, color] : [colors.primary[400], colors.primary[600]]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={[styles.fill, { width: `${clampedProgress}%`, height }]}
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 },
  label: { fontFamily: fontFamily.medium, fontSize: fontSize.sm, color: colors.text.secondary },
  percentage: { fontFamily: fontFamily.semiBold, fontSize: fontSize.sm, color: colors.text.primary },
  track: { backgroundColor: colors.figma.lighterElements, borderRadius: 99, overflow: 'hidden' },
  fill: { borderRadius: 99 },
});

export default ProgressBar;
