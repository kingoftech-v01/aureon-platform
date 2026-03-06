import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Controller, Control } from 'react-hook-form';
import { format } from 'date-fns';
import { colors } from '@theme/colors';
import { spacing } from '@theme/spacing';
import { fontFamily, fontSize } from '@theme/typography';

interface FormDatePickerProps {
  name: string;
  control: Control<any>;
  label: string;
  error?: string;
  placeholder?: string;
}

export function FormDatePicker({ name, control, label, error, placeholder = 'Select date...' }: FormDatePickerProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <Controller
        control={control}
        name={name}
        render={({ field: { onChange, value } }) => (
          <TouchableOpacity
            style={[styles.input, error && styles.inputError]}
            onPress={() => {
              // For now, show a simple date string
              // In production, integrate with @react-native-community/datetimepicker
              const today = new Date();
              onChange(today.toISOString().split('T')[0]);
            }}
          >
            <Text style={[styles.text, !value && styles.placeholder]}>
              {value ? format(new Date(value), 'MMM dd, yyyy') : placeholder}
            </Text>
          </TouchableOpacity>
        )}
      />
      {error && <Text style={styles.error}>{error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { marginBottom: spacing.md },
  label: {
    fontSize: fontSize.sm,
    fontFamily: fontFamily.medium,
    color: colors.text.primary,
    marginBottom: spacing.xs,
  },
  input: {
    borderWidth: 1,
    borderColor: colors.figma.borders,
    borderRadius: 12,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 2,
    backgroundColor: colors.background.primary,
  },
  inputError: { borderColor: colors.danger },
  text: { fontSize: fontSize.md, color: colors.text.primary },
  placeholder: { color: colors.text.muted },
  error: { fontSize: fontSize.xs, color: colors.danger, marginTop: spacing.xs },
});
