import React, { useEffect, useRef } from 'react';
import { View, Animated, StyleSheet, ViewStyle } from 'react-native';
import { colors } from '@theme/colors';

interface SkeletonProps {
  width?: number | string;
  height?: number;
  borderRadius?: number;
  style?: ViewStyle;
}

const SkeletonLoader: React.FC<SkeletonProps> = ({ width = '100%', height = 20, borderRadius = 8, style }) => {
  const opacity = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, { toValue: 0.7, duration: 800, useNativeDriver: true }),
        Animated.timing(opacity, { toValue: 0.3, duration: 800, useNativeDriver: true }),
      ])
    );
    animation.start();
    return () => animation.stop();
  }, []);

  return (
    <Animated.View
      style={[
        { width: width as any, height, borderRadius, backgroundColor: colors.figma.lighterElements, opacity },
        style,
      ]}
    />
  );
};

// Pre-built skeleton patterns
export const SkeletonCard: React.FC<{ style?: ViewStyle }> = ({ style }) => (
  <View style={[styles.card, style]}>
    <SkeletonLoader height={16} width="60%" />
    <SkeletonLoader height={12} width="40%" style={{ marginTop: 8 }} />
    <SkeletonLoader height={32} width="80%" style={{ marginTop: 16 }} />
  </View>
);

export const SkeletonListItem: React.FC = () => (
  <View style={styles.listItem}>
    <SkeletonLoader width={44} height={44} borderRadius={22} />
    <View style={styles.listItemContent}>
      <SkeletonLoader height={14} width="70%" />
      <SkeletonLoader height={12} width="50%" style={{ marginTop: 6 }} />
    </View>
    <SkeletonLoader height={14} width={60} />
  </View>
);

const styles = StyleSheet.create({
  card: { padding: 16, backgroundColor: 'rgba(255,255,255,0.6)', borderRadius: 16, marginBottom: 12 },
  listItem: { flexDirection: 'row', alignItems: 'center', padding: 14, gap: 12 },
  listItemContent: { flex: 1 },
});

export default SkeletonLoader;
