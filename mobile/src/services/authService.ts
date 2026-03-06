/**
 * Authentication API Service
 */

import apiClient from './api';
import { tokenService } from './tokenService';
import type { User, AuthTokens, LoginCredentials, RegisterData } from '@/types';

export const authService = {
  login: async (credentials: LoginCredentials): Promise<{ user: User; tokens: AuthTokens }> => {
    const response = await apiClient.post('/auth/login/', credentials);
    const { user, access, refresh } = response.data;
    await tokenService.setTokens(access, refresh);
    return { user, tokens: { access, refresh } };
  },

  register: async (data: RegisterData): Promise<{ user: User; tokens: AuthTokens }> => {
    const response = await apiClient.post('/auth/register/', data);
    const { user, access, refresh } = response.data;
    await tokenService.setTokens(access, refresh);
    return { user, tokens: { access, refresh } };
  },

  logout: async (): Promise<void> => {
    const refreshToken = tokenService.getRefreshToken();
    if (refreshToken) {
      try {
        await apiClient.post('/auth/logout/', { refresh: refreshToken });
      } catch {
        // Ignore logout API errors
      }
    }
    await tokenService.clearTokens();
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get('/auth/me/');
    return response.data;
  },

  updateProfile: async (userId: string, data: Partial<User>): Promise<User> => {
    const response = await apiClient.patch(`/users/${userId}/`, data);
    return response.data;
  },

  changePassword: async (userId: string, oldPassword: string, newPassword: string): Promise<void> => {
    await apiClient.post(`/users/${userId}/change_password/`, {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },

  requestPasswordReset: async (email: string): Promise<void> => {
    await apiClient.post('/auth/password-reset/', { email });
  },
};
