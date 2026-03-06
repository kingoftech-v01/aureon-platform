import React, { useEffect, useRef } from 'react';
import { Animated, ViewStyle } from 'react-native';
import { GlassCard } from '@components/glass';

interface AnimatedCardProps {
  children: React.ReactNode;
  delay?: number;
  style?: ViewStyle;
  preset?: 'card' | 'cardSmall' | 'cardSolid';
  onPress?: () => void;
}

const AnimatedCard: React.FC<AnimatedCardProps> = ({ children, delay = 0, style, preset = 'cardSolid', onPress }) => {
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 400,
        delay,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 400,
        delay,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  return (
    <Animated.View style={[{ opacity: fadeAnim, transform: [{ translateY: slideAnim }] }, style]}>
      <GlassCard preset={preset} onPress={onPress}>
        {children}
      </GlassCard>
    </Animated.View>
  );
};

export default AnimatedCard;
