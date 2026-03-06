/**
 * GlassCard - Primary glassmorphism container component
 * Uses @react-native-community/blur for real frosted glass effect
 */

import React, { ReactNode } from 'react';
import {
  View,
  StyleSheet,
  ViewStyle,
  Pressable,
  StyleProp,
} from 'react-native';
import { BlurView } from '@react-native-community/blur';
import { glassPresets, GlassPreset } from '@theme/glassmorphism';

interface GlassCardProps {
  children: ReactNode;
  preset?: keyof typeof glassPresets;
  style?: StyleProp<ViewStyle>;
  onPress?: () => void;
  disabled?: boolean;
}

const GlassCard: React.FC<GlassCardProps> = ({
  children,
  preset = 'card',
  style,
  onPress,
  disabled = false,
}) => {
  const glass: GlassPreset = glassPresets[preset];

  const containerStyle: ViewStyle = {
    borderRadius: glass.borderRadius,
    overflow: 'hidden',
    borderWidth: glass.borderWidth,
    borderColor: glass.borderColor,
    ...glass.shadow,
  };

  const content = (
    <View style={[containerStyle, style]}>
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
      <View style={styles.content}>{children}</View>
    </View>
  );

  if (onPress) {
    return (
      <Pressable
        onPress={onPress}
        disabled={disabled}
        style={({ pressed }) => [{ opacity: pressed ? 0.85 : 1 }]}
      >
        {content}
      </Pressable>
    );
  }

  return content;
};

const styles = StyleSheet.create({
  content: {
    zIndex: 1,
  },
});

export default GlassCard;
