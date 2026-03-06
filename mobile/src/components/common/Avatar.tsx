/**
 * Avatar - User avatar with initials fallback
 */

import React from 'react';
import { View, Text, Image, StyleSheet } from 'react-native';
import { colors } from '@theme/colors';
import { fontFamily } from '@theme/typography';

type AvatarSize = 'sm' | 'md' | 'lg' | 'xl';

interface AvatarProps {
  src?: string;
  name?: string;
  size?: AvatarSize;
}

const sizeMap: Record<AvatarSize, { container: number; text: number }> = {
  sm: { container: 32, text: 12 },
  md: { container: 40, text: 14 },
  lg: { container: 56, text: 20 },
  xl: { container: 72, text: 26 },
};

const Avatar: React.FC<AvatarProps> = ({ src, name, size = 'md' }) => {
  const dim = sizeMap[size];

  const getInitials = (n?: string) => {
    if (!n) return '?';
    const parts = n.trim().split(' ');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return n[0].toUpperCase();
  };

  if (src) {
    return (
      <Image
        source={{ uri: src }}
        style={[
          styles.image,
          {
            width: dim.container,
            height: dim.container,
            borderRadius: dim.container / 2,
          },
        ]}
      />
    );
  }

  return (
    <View
      style={[
        styles.fallback,
        {
          width: dim.container,
          height: dim.container,
          borderRadius: dim.container / 2,
        },
      ]}
    >
      <Text style={[styles.initials, { fontSize: dim.text }]}>
        {getInitials(name)}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  image: {
    backgroundColor: colors.figma.lighterElements,
  },
  fallback: {
    backgroundColor: colors.primary[100],
    alignItems: 'center',
    justifyContent: 'center',
  },
  initials: {
    fontFamily: fontFamily.semiBold,
    color: colors.primary[700],
  },
});

export default Avatar;
