/**
 * EmptyState - Empty list placeholder
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { GlassButton } from '@components/glass';

interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  icon = 'folder-open-outline',
  title,
  description,
  actionLabel,
  onAction,
}) => {
  return (
    <View style={styles.container}>
      <Icon name={icon} size={64} color={colors.figma.lighterElements} />
      <Text style={styles.title}>{title}</Text>
      {description && <Text style={styles.description}>{description}</Text>}
      {actionLabel && onAction && (
        <GlassButton
          title={actionLabel}
          onPress={onAction}
          variant="primary"
          size="sm"
          style={styles.button}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  title: {
    fontFamily: fontFamily.semiBold,
    fontSize: fontSize.xl,
    color: colors.text.primary,
    marginTop: 16,
    textAlign: 'center',
  },
  description: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.md,
    color: colors.text.secondary,
    marginTop: 8,
    textAlign: 'center',
  },
  button: {
    marginTop: 24,
  },
});

export default EmptyState;
