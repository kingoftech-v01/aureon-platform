import React from 'react';
import { View, Text, TextInput, StyleSheet, TextInputProps } from 'react-native';
import { Controller, Control } from 'react-hook-form';
import { colors } from '@theme/colors';
import { spacing } from '@theme/spacing';
import { fontFamily, fontSize } from '@theme/typography';

interface FormInputProps extends Omit<TextInputProps, 'value' | 'onChangeText'> {
  name: string;
  control: Control<any>;
  label: string;
  error?: string;
}

export function FormInput({ name, control, label, error, ...props }: FormInputProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <Controller
        control={control}
        name={name}
        render={({ field: { onChange, onBlur, value } }) => (
          <TextInput
            style={[styles.input, error && styles.inputError]}
            onBlur={onBlur}
            onChangeText={onChange}
            value={value}
            placeholderTextColor={colors.text.muted}
            {...props}
          />
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
    paddingVertical: spacing.sm,
    fontSize: fontSize.md,
    fontFamily: fontFamily.regular,
    color: colors.text.primary,
    backgroundColor: colors.background.primary,
  },
  inputError: { borderColor: colors.danger },
  error: {
    fontSize: fontSize.xs,
    color: colors.danger,
    marginTop: spacing.xs,
  },
});
