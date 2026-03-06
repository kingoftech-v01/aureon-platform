/**
 * GlassModal - Glassmorphism modal overlay
 */

import React, { ReactNode } from 'react';
import {
  View,
  Modal,
  StyleSheet,
  Pressable,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { BlurView } from '@react-native-community/blur';
import { glassPresets } from '@theme/glassmorphism';
import { colors } from '@theme/colors';

interface GlassModalProps {
  visible: boolean;
  onClose: () => void;
  children: ReactNode;
}

const GlassModal: React.FC<GlassModalProps> = ({
  visible,
  onClose,
  children,
}) => {
  const glass = glassPresets.modal;

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.overlay}
      >
        <Pressable style={styles.backdrop} onPress={onClose}>
          <BlurView
            blurType="dark"
            blurAmount={10}
            style={StyleSheet.absoluteFill}
            reducedTransparencyFallbackColor="black"
          />
          <View
            style={[
              StyleSheet.absoluteFill,
              { backgroundColor: colors.overlay },
            ]}
          />
        </Pressable>

        <View
          style={[
            styles.content,
            {
              borderRadius: glass.borderRadius,
              borderWidth: glass.borderWidth,
              borderColor: glass.borderColor,
              overflow: 'hidden',
            },
            glass.shadow,
          ]}
        >
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
          <View style={styles.inner}>{children}</View>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  backdrop: {
    ...StyleSheet.absoluteFillObject,
  },
  content: {
    width: '100%',
    maxHeight: '80%',
  },
  inner: {
    zIndex: 1,
    padding: 24,
  },
});

export default GlassModal;
