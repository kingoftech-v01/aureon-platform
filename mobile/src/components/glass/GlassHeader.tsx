/**
 * GlassHeader - Glassmorphism navigation header
 * Matches Figma: back arrow left, title center, avatar/actions right
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  StatusBar,
  Platform,
} from 'react-native';
import { BlurView } from '@react-native-community/blur';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Ionicons';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { glassPresets } from '@theme/glassmorphism';

interface GlassHeaderProps {
  title?: string;
  onBack?: () => void;
  rightAction?: React.ReactNode;
  transparent?: boolean;
}

const GlassHeader: React.FC<GlassHeaderProps> = ({
  title,
  onBack,
  rightAction,
  transparent = false,
}) => {
  const insets = useSafeAreaInsets();
  const glass = glassPresets.header;
  const statusBarHeight = Platform.OS === 'ios' ? insets.top : StatusBar.currentHeight || 0;

  return (
    <View style={[styles.container, { paddingTop: statusBarHeight }]}>
      {!transparent && (
        <>
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
        </>
      )}

      <View style={styles.content}>
        <View style={styles.left}>
          {onBack && (
            <Pressable
              onPress={onBack}
              style={styles.iconButton}
              hitSlop={8}
            >
              <Icon
                name="arrow-back"
                size={24}
                color={colors.text.secondary}
              />
            </Pressable>
          )}
        </View>

        <View style={styles.center}>
          {title && (
            <Text style={styles.title} numberOfLines={1}>
              {title}
            </Text>
          )}
        </View>

        <View style={styles.right}>
          {rightAction || <View style={styles.placeholder} />}
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    zIndex: 100,
  },
  content: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: 56,
    paddingHorizontal: 16,
    zIndex: 1,
  },
  left: {
    width: 48,
    alignItems: 'flex-start',
  },
  center: {
    flex: 1,
    alignItems: 'center',
  },
  right: {
    width: 48,
    alignItems: 'flex-end',
  },
  title: {
    fontFamily: fontFamily.semiBold,
    fontSize: fontSize.xl,
    color: colors.text.primary,
  },
  iconButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholder: {
    width: 24,
  },
});

export default GlassHeader;
