/**
 * ListItem - Standard list item (Figma trending list pattern)
 * Thumbnail on left, title/subtitle/metadata on right
 */

import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';

interface ListItemProps {
  title: string;
  subtitle?: string;
  rightText?: string;
  rightSubtext?: string;
  left?: React.ReactNode;
  right?: React.ReactNode;
  badge?: React.ReactNode;
  onPress?: () => void;
}

const ListItem: React.FC<ListItemProps> = ({
  title,
  subtitle,
  rightText,
  rightSubtext,
  left,
  right,
  badge,
  onPress,
}) => {
  const content = (
    <View style={styles.container}>
      {left && <View style={styles.left}>{left}</View>}

      <View style={styles.center}>
        <View style={styles.titleRow}>
          <Text style={styles.title} numberOfLines={1}>
            {title}
          </Text>
          {badge}
        </View>
        {subtitle && (
          <Text style={styles.subtitle} numberOfLines={1}>
            {subtitle}
          </Text>
        )}
      </View>

      {(rightText || right) && (
        <View style={styles.right}>
          {rightText && (
            <Text style={styles.rightText}>{rightText}</Text>
          )}
          {rightSubtext && (
            <Text style={styles.rightSubtext}>{rightSubtext}</Text>
          )}
          {right}
        </View>
      )}
    </View>
  );

  if (onPress) {
    return (
      <Pressable
        onPress={onPress}
        style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}
      >
        {content}
      </Pressable>
    );
  }

  return content;
};

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  left: {
    marginRight: 12,
  },
  center: {
    flex: 1,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.lg,
    color: colors.text.primary,
    flexShrink: 1,
  },
  subtitle: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.sm,
    color: colors.text.secondary,
    marginTop: 2,
  },
  right: {
    alignItems: 'flex-end',
    marginLeft: 12,
  },
  rightText: {
    fontFamily: fontFamily.semiBold,
    fontSize: fontSize.lg,
    color: colors.text.primary,
  },
  rightSubtext: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.sm,
    color: colors.text.secondary,
    marginTop: 2,
  },
});

export default ListItem;
