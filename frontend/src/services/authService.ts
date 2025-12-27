/**
 * Authentication API Service
 * Aureon by Rhematek Solutions
 */

import apiClient, { tokenService } from './api';
import type {
  User,
  AuthTokens,
  LoginCredentials,
  RegisterData,
} from '@/types';

export const authService = {
  /**
   * Login user
   */
  login: async (credentials: LoginCredentials): Promise<{ user: User; tokens: AuthTokens }> => {
    const response = await apiClient.post('/auth/login/', credentials);
    const { user, access, refresh } = response.data;

    // Store tokens
    tokenService.setTokens(access, refresh);

    return { user, tokens: { access, refresh } };
  },

  /**
   * Register new user
   */
  register: async (data: RegisterData): Promise<{ user: User; tokens: AuthTokens }> => {
    const response = await apiClient.post('/auth/register/', data);
    const { user, access, refresh } = response.data;

    // Store tokens
    tokenService.setTokens(access, refresh);

    return { user, tokens: { access, refresh } };
  },

  /**
   * Logout user
   */
  logout: async (): Promise<void> => {
    const refreshToken = tokenService.getRefreshToken();

    if (refreshToken) {
      await apiClient.post('/auth/logout/', { refresh: refreshToken });
    }

    tokenService.clearTokens();
  },

  /**
   * Get current user
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get('/auth/me/');
    return response.data;
  },

  /**
   * Update user profile
   */
  updateProfile: async (userId: string, data: Partial<User>): Promise<User> => {
    const response = await apiClient.patch(`/users/${userId}/`, data);
    return response.data;
  },

  /**
   * Change password
   */
  changePassword: async (
    userId: string,
    oldPassword: string,
    newPassword: string
  ): Promise<void> => {
    await apiClient.post(`/users/${userId}/change_password/`, {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  /**
   * Request password reset
   */
  requestPasswordReset: async (email: string): Promise<void> => {
    await apiClient.post('/auth/password-reset/', { email });
  },

  /**
   * Confirm password reset
   */
  confirmPasswordReset: async (
    token: string,
    password: string
  ): Promise<void> => {
    await apiClient.post('/auth/password-reset/confirm/', {
      token,
      password,
    });
  },

  /**
   * Verify email
   */
  verifyEmail: async (token: string): Promise<void> => {
    await apiClient.post('/auth/verify-email/', { token });
  },

  /**
   * Resend verification email
   */
  resendVerificationEmail: async (email: string): Promise<void> => {
    await apiClient.post('/auth/resend-verification/', { email });
  },

  /**
   * Enable 2FA
   */
  enable2FA: async (userId: string): Promise<{ qr_code: string; secret: string }> => {
    const response = await apiClient.post(`/users/${userId}/enable-2fa/`);
    return response.data;
  },

  /**
   * Verify 2FA code
   */
  verify2FA: async (userId: string, code: string): Promise<void> => {
    await apiClient.post(`/users/${userId}/verify-2fa/`, { code });
  },

  /**
   * Disable 2FA
   */
  disable2FA: async (userId: string): Promise<void> => {
    await apiClient.post(`/users/${userId}/disable-2fa/`);
  },
};

export default authService;
