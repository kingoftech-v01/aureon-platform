/**
 * SearchBar - Glass-styled search input
 */

import React from 'react';
import { View, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { GlassInput } from '@components/glass';
import { colors } from '@theme/colors';

interface SearchBarProps {
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
}

const SearchBar: React.FC<SearchBarProps> = ({
  value,
  onChangeText,
  placeholder = 'Search...',
}) => {
  return (
    <View style={styles.container}>
      <GlassInput
        value={value}
        onChangeText={onChangeText}
        placeholder={placeholder}
        icon={<Icon name="search" size={20} color={colors.text.muted} />}
        iconRight={
          value ? (
            <Icon
              name="close-circle"
              size={20}
              color={colors.text.muted}
              onPress={() => onChangeText('')}
            />
          ) : undefined
        }
        returnKeyType="search"
        autoCapitalize="none"
        autoCorrect={false}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    marginBottom: 8,
  },
});

export default SearchBar;
