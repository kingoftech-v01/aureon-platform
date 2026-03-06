/**
 * DatePicker - Simple date picker wrapping GlassInput with auto-formatting
 */

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { GlassInput } from '@components/glass';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import Ionicons from 'react-native-vector-icons/Ionicons';

interface DatePickerProps {
  label?: string;
  value: string; // YYYY-MM-DD
  onChange: (date: string) => void;
  placeholder?: string;
  error?: string;
  minDate?: string;
  maxDate?: string;
}

const DatePicker: React.FC<DatePickerProps> = ({
  label,
  value,
  onChange,
  placeholder = 'YYYY-MM-DD',
  error,
}) => {
  const formatDisplayDate = (dateStr: string) => {
    if (!dateStr) return '';
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <View>
      <GlassInput
        label={label}
        value={value}
        onChangeText={(text: string) => {
          // Auto-format: add dashes as user types
          const cleaned = text.replace(/[^0-9]/g, '');
          let formatted = cleaned;
          if (cleaned.length > 4) {
            formatted = cleaned.slice(0, 4) + '-' + cleaned.slice(4);
          }
          if (cleaned.length > 6) {
            formatted =
              formatted.slice(0, 7) + '-' + cleaned.slice(6, 8);
          }
          onChange(formatted);
        }}
        placeholder={placeholder}
        error={error}
        icon={
          <Ionicons
            name="calendar-outline"
            size={20}
            color={colors.text.muted}
          />
        }
        keyboardType="numeric"
        maxLength={10}
      />
      {value && value.length === 10 && (
        <Text style={styles.displayDate}>{formatDisplayDate(value)}</Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  displayDate: {
    fontFamily: fontFamily.regular,
    fontSize: fontSize.sm,
    color: colors.text.secondary,
    marginTop: 4,
    marginLeft: 4,
  },
});

export default DatePicker;
