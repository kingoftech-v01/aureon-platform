/**
 * Auth Store - Zustand
 * Manages authentication state for the mobile app
 */

import { create } from 'zustand';
import { authService } from '@services/authService';
import { tokenService } from '@services/tokenService';
import { setAuthFailureCallback } from '@services/api';
import type { User, LoginCredentials, RegisterData } from '@/types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isHydrated: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  hydrate: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>((set, get) => {
  // Register auth failure callback
  setAuthFailureCallback(() => {
    set({ user: null, isAuthenticated: false });
  });

  return {
    user: null,
    isAuthenticated: false,
    isLoading: false,
    isHydrated: false,
    error: null,

    login: async (credentials: LoginCredentials) => {
      set({ isLoading: true, error: null });
      try {
        const { user } = await authService.login(credentials);
        set({ user, isAuthenticated: true, isLoading: false });
      } catch (err: any) {
        const message =
          err.response?.data?.detail ||
          err.response?.data?.message ||
          'Login failed. Please check your credentials.';
        set({ isLoading: false, error: message });
        throw err;
      }
    },

    register: async (data: RegisterData) => {
      set({ isLoading: true, error: null });
      try {
        const { user } = await authService.register(data);
        set({ user, isAuthenticated: true, isLoading: false });
      } catch (err: any) {
        const message =
          err.response?.data?.detail ||
          err.response?.data?.message ||
          'Registration failed. Please try again.';
        set({ isLoading: false, error: message });
        throw err;
      }
    },

    logout: async () => {
      set({ isLoading: true });
      try {
        await authService.logout();
      } finally {
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      }
    },

    hydrate: async () => {
      try {
        const { access } = await tokenService.hydrate();

        if (access) {
          const user = await authService.getCurrentUser();
          set({ user, isAuthenticated: true, isHydrated: true });
        } else {
          set({ isHydrated: true });
        }
      } catch {
        await tokenService.clearTokens();
        set({ isHydrated: true });
      }
    },

    clearError: () => set({ error: null }),
  };
});
