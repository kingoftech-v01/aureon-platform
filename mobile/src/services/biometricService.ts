import * as Keychain from 'react-native-keychain';
import { Platform } from 'react-native';

const BIOMETRIC_KEY = 'aureon_biometric_enabled';

export const biometricService = {
  /**
   * Check if biometric authentication is available on this device
   */
  isAvailable: async (): Promise<{ available: boolean; biometryType: string | null }> => {
    try {
      const type = await Keychain.getSupportedBiometryType();
      return { available: !!type, biometryType: type };
    } catch {
      return { available: false, biometryType: null };
    }
  },

  /**
   * Enable biometric auth by storing credentials with biometric protection
   */
  enable: async (accessToken: string, refreshToken: string): Promise<boolean> => {
    try {
      await Keychain.setGenericPassword('biometric_tokens', JSON.stringify({ accessToken, refreshToken }), {
        service: BIOMETRIC_KEY,
        accessControl: Keychain.ACCESS_CONTROL.BIOMETRY_CURRENT_SET,
        accessible: Keychain.ACCESSIBLE.WHEN_PASSCODE_SET_THIS_DEVICE_ONLY,
        authenticationType: Keychain.AUTHENTICATION_TYPE.BIOMETRICS,
      });
      return true;
    } catch {
      return false;
    }
  },

  /**
   * Authenticate with biometrics and retrieve stored tokens
   */
  authenticate: async (): Promise<{ accessToken: string; refreshToken: string } | null> => {
    try {
      const credentials = await Keychain.getGenericPassword({
        service: BIOMETRIC_KEY,
        authenticationPrompt: {
          title: 'Authenticate',
          subtitle: 'Use biometrics to sign in to Aureon',
          cancel: 'Cancel',
        },
      });
      if (credentials) {
        return JSON.parse(credentials.password);
      }
      return null;
    } catch {
      return null;
    }
  },

  /**
   * Disable biometric authentication
   */
  disable: async (): Promise<void> => {
    try {
      await Keychain.resetGenericPassword({ service: BIOMETRIC_KEY });
    } catch {}
  },

  /**
   * Check if biometric auth is enabled (has stored credentials)
   */
  isEnabled: async (): Promise<boolean> => {
    try {
      const credentials = await Keychain.getGenericPassword({ service: BIOMETRIC_KEY });
      return !!credentials;
    } catch {
      return false;
    }
  },
};
