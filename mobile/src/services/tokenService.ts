/**
 * Secure Token Storage using react-native-keychain
 * Replaces localStorage from web frontend
 */

import * as Keychain from 'react-native-keychain';

const ACCESS_SERVICE = 'aureon_access_token';
const REFRESH_SERVICE = 'aureon_refresh_token';

// In-memory cache for synchronous access in interceptors
let cachedAccessToken: string | null = null;
let cachedRefreshToken: string | null = null;

export const tokenService = {
  /**
   * Get access token (sync from cache)
   */
  getAccessToken: (): string | null => {
    return cachedAccessToken;
  },

  /**
   * Get refresh token (sync from cache)
   */
  getRefreshToken: (): string | null => {
    return cachedRefreshToken;
  },

  /**
   * Store tokens in both Keychain and cache
   */
  setTokens: async (accessToken: string, refreshToken: string): Promise<void> => {
    cachedAccessToken = accessToken;
    cachedRefreshToken = refreshToken;

    await Promise.all([
      Keychain.setGenericPassword('token', accessToken, {
        service: ACCESS_SERVICE,
      }),
      Keychain.setGenericPassword('token', refreshToken, {
        service: REFRESH_SERVICE,
      }),
    ]);
  },

  /**
   * Clear all tokens
   */
  clearTokens: async (): Promise<void> => {
    cachedAccessToken = null;
    cachedRefreshToken = null;

    await Promise.all([
      Keychain.resetGenericPassword({ service: ACCESS_SERVICE }),
      Keychain.resetGenericPassword({ service: REFRESH_SERVICE }),
    ]);
  },

  /**
   * Hydrate cache from Keychain on app start
   */
  hydrate: async (): Promise<{ access: string | null; refresh: string | null }> => {
    try {
      const [accessResult, refreshResult] = await Promise.all([
        Keychain.getGenericPassword({ service: ACCESS_SERVICE }),
        Keychain.getGenericPassword({ service: REFRESH_SERVICE }),
      ]);

      const access = accessResult ? accessResult.password : null;
      const refresh = refreshResult ? refreshResult.password : null;

      cachedAccessToken = access;
      cachedRefreshToken = refresh;

      return { access, refresh };
    } catch {
      return { access: null, refresh: null };
    }
  },
};
