/**
 * SplashScreen - Branded splash with glassmorphism animation
 */

import React, { useEffect } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import LinearGradient from 'react-native-linear-gradient';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { LoadingSpinner } from '@components/common';

const SplashScreen: React.FC = () => {
  const opacity = new Animated.Value(0);
  const scale = new Animated.Value(0.8);

  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, {
        toValue: 1,
        duration: 800,
        useNativeDriver: true,
      }),
      Animated.spring(scale, {
        toValue: 1,
        friction: 6,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  return (
    <LinearGradient
      colors={[colors.primary[700], colors.primary[900]]}
      style={styles.container}
    >
      <Animated.View
        style={[styles.logoContainer, { opacity, transform: [{ scale }] }]}
      >
        <View style={styles.glassCircle}>
          <Text style={styles.logoText}>A</Text>
        </View>
        <Text style={styles.appName}>Aureon</Text>
        <Text style={styles.tagline}>Finance Management</Text>
      </Animated.View>

      <View style={styles.loading}>
        <LoadingSpinner size="small" color={colors.white} />
      </View>
    </LinearGradient>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  logoContainer: {
    alignItems: 'center',
  },
  glassCircle: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.25)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  logoText: {
    fontFamily: fontFamily.bold,
    fontSize: 42,
    color: colors.white,
  },
  appName: {
    fontFamily: fontFamily.bold,
    fontSize: fontSize['4xl'],
    color: colors.white,
    marginBottom: 4,
  },
  tagline: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.lg,
    color: 'rgba(255, 255, 255, 0.7)',
  },
  loading: {
    position: 'absolute',
    bottom: 80,
  },
});

export default SplashScreen;
