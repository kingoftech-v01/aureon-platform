/**
 * AuthContext Tests
 * Aureon by Rhematek Solutions
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../AuthContext';
import * as authService from '@/services/authService';
import { mockUser } from '@/tests/mocks/data';

// Mock authService
vi.mock('@/services/authService', () => ({
  authService: {
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
    getCurrentUser: vi.fn(),
    refreshToken: vi.fn(),
  },
}));

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorageMock.clear();
  });

  it('provides authentication context', () => {
    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    expect(result.current).toBeDefined();
    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(result.current.isLoading).toBe(true); // Initially loading
  });

  it('logs in user successfully', async () => {
    const mockLoginResponse = {
      access: 'mock-access-token',
      refresh: 'mock-refresh-token',
      user: mockUser,
    };

    vi.mocked(authService.authService.login).mockResolvedValue(mockLoginResponse);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await act(async () => {
      await result.current.login({ email: 'test@example.com', password: 'password123' });
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
    expect(localStorage.getItem('accessToken')).toBe('mock-access-token');
    expect(localStorage.getItem('refreshToken')).toBe('mock-refresh-token');
  });

  it('registers user successfully', async () => {
    const mockRegisterResponse = {
      access: 'mock-access-token',
      refresh: 'mock-refresh-token',
      user: mockUser,
    };

    vi.mocked(authService.authService.register).mockResolvedValue(mockRegisterResponse);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await act(async () => {
      await result.current.register({
        first_name: 'John',
        last_name: 'Doe',
        email: 'test@example.com',
        password: 'password123',
        confirm_password: 'password123',
      });
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('logs out user successfully', async () => {
    const mockLoginResponse = {
      access: 'mock-access-token',
      refresh: 'mock-refresh-token',
      user: mockUser,
    };

    vi.mocked(authService.authService.login).mockResolvedValue(mockLoginResponse);
    vi.mocked(authService.authService.logout).mockResolvedValue(undefined);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    // Login first
    await act(async () => {
      await result.current.login({ email: 'test@example.com', password: 'password123' });
    });

    expect(result.current.isAuthenticated).toBe(true);

    // Then logout
    await act(async () => {
      await result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(localStorage.getItem('accessToken')).toBeNull();
    expect(localStorage.getItem('refreshToken')).toBeNull();
  });

  it('loads user from token on mount', async () => {
    localStorage.setItem('accessToken', 'existing-token');
    vi.mocked(authService.authService.getCurrentUser).mockResolvedValue(mockUser);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('handles login failure', async () => {
    vi.mocked(authService.authService.login).mockRejectedValue(
      new Error('Invalid credentials')
    );

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await expect(
      act(async () => {
        await result.current.login({ email: 'test@example.com', password: 'wrong' });
      })
    ).rejects.toThrow('Invalid credentials');

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('handles failed user fetch on mount', async () => {
    localStorage.setItem('accessToken', 'invalid-token');
    vi.mocked(authService.authService.getCurrentUser).mockRejectedValue(
      new Error('Token expired')
    );

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
    expect(localStorage.getItem('accessToken')).toBeNull();
  });

  it('updates user profile', async () => {
    const mockLoginResponse = {
      access: 'mock-access-token',
      refresh: 'mock-refresh-token',
      user: mockUser,
    };

    const updatedUser = { ...mockUser, first_name: 'Jane' };

    vi.mocked(authService.authService.login).mockResolvedValue(mockLoginResponse);

    const { result } = renderHook(() => useAuth(), {
      wrapper: AuthProvider,
    });

    // Login first
    await act(async () => {
      await result.current.login({ email: 'test@example.com', password: 'password123' });
    });

    // Update user
    act(() => {
      result.current.setUser(updatedUser);
    });

    expect(result.current.user?.first_name).toBe('Jane');
  });
});
