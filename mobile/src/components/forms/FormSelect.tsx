import React, { useState } from 'react';
import { View, Text, TouchableOpacity, Modal, FlatList, StyleSheet } from 'react-native';
import { Controller, Control } from 'react-hook-form';
import { colors } from '@theme/colors';
import { spacing } from '@theme/spacing';
import { fontFamily, fontSize } from '@theme/typography';

interface Option {
  label: string;
  value: string;
}

interface FormSelectProps {
  name: string;
  control: Control<any>;
  label: string;
  options: Option[];
  error?: string;
  placeholder?: string;
}

export function FormSelect({ name, control, label, options, error, placeholder = 'Select...' }: FormSelectProps) {
  const [visible, setVisible] = useState(false);

  return (
    <View style={styles.container}>
      <Text style={styles.label}>{label}</Text>
      <Controller
        control={control}
        name={name}
        render={({ field: { onChange, value } }) => {
          const selectedOption = options.find((o) => o.value === value);
          return (
            <>
              <TouchableOpacity
                style={[styles.select, error && styles.selectError]}
                onPress={() => setVisible(true)}
              >
                <Text style={[styles.selectText, !selectedOption && styles.placeholder]}>
                  {selectedOption?.label || placeholder}
                </Text>
              </TouchableOpacity>
              <Modal visible={visible} transparent animationType="slide">
                <TouchableOpacity style={styles.overlay} onPress={() => setVisible(false)}>
                  <View style={styles.modal}>
                    <FlatList
                      data={options}
                      keyExtractor={(item) => item.value}
                      renderItem={({ item }) => (
                        <TouchableOpacity
                          style={[styles.option, item.value === value && styles.optionSelected]}
                          onPress={() => { onChange(item.value); setVisible(false); }}
                        >
                          <Text style={[styles.optionText, item.value === value && styles.optionTextSelected]}>
                            {item.label}
                          </Text>
                        </TouchableOpacity>
                      )}
                    />
                  </View>
                </TouchableOpacity>
              </Modal>
            </>
          );
        }}
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
  select: {
    borderWidth: 1,
    borderColor: colors.figma.borders,
    borderRadius: 12,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm + 2,
    backgroundColor: colors.background.primary,
  },
  selectError: { borderColor: colors.danger },
  selectText: { fontSize: fontSize.md, color: colors.text.primary },
  placeholder: { color: colors.text.muted },
  overlay: { flex: 1, justifyContent: 'flex-end', backgroundColor: 'rgba(0,0,0,0.5)' },
  modal: {
    backgroundColor: colors.background.primary,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '50%',
    paddingVertical: spacing.md,
  },
  option: { paddingHorizontal: spacing.lg, paddingVertical: spacing.md },
  optionSelected: { backgroundColor: colors.primary[50] },
  optionText: { fontSize: fontSize.md, color: colors.text.primary },
  optionTextSelected: { color: colors.primary[500], fontFamily: fontFamily.semiBold },
  error: { fontSize: fontSize.xs, color: colors.danger, marginTop: spacing.xs },
});
