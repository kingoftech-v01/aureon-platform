/**
 * Aureon Mobile API Client
 * Axios-based with JWT authentication via Keychain
 * Adapted from frontend/src/services/api.ts
 */

import axios, {
  AxiosInstance,
  AxiosError,
  InternalAxiosRequestConfig,
} from 'axios';
import { tokenService } from './tokenService';
import { API_CONFIG } from '@config/api';
import type { ApiError } from '@/types';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_CONFIG.baseURL,
  timeout: API_CONFIG.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Store logout callback (set by auth store)
let onAuthFailure: (() => void) | null = null;

export const setAuthFailureCallback = (callback: () => void) => {
  onAuthFailure = callback;
};

// ============================================
// REQUEST INTERCEPTOR
// ============================================

apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = tokenService.getAccessToken();

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  },
);

// ============================================
// RESPONSE INTERCEPTOR (Token Refresh)
// ============================================

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: any) => void;
}> = [];

const processQueue = (error: any = null, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return apiClient(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = tokenService.getRefreshToken();

      if (!refreshToken) {
        await tokenService.clearTokens();
        onAuthFailure?.();
        return Promise.reject(error);
      }

      try {
        const response = await axios.post(
          `${API_CONFIG.baseURL}/auth/token/refresh/`,
          { refresh: refreshToken },
        );

        const { access } = response.data;
        await tokenService.setTokens(access, refreshToken);

        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${access}`;
        }

        processQueue(null, access);
        isRefreshing = false;

        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;
        await tokenService.clearTokens();
        onAuthFailure?.();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);

// ============================================
// ERROR HANDLER
// ============================================

export const handleApiError = (error: unknown): ApiError => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<ApiError>;

    if (axiosError.response?.data) {
      return axiosError.response.data;
    }

    if (axiosError.request) {
      return {
        message: 'No response from server. Please check your connection.',
      };
    }
  }

  return {
    message: 'An unexpected error occurred. Please try again.',
  };
};

// ============================================
// QUERY PARAMS BUILDER
// ============================================

export const buildQueryParams = (params: Record<string, any>): string => {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') {
      if (Array.isArray(value)) {
        value.forEach((v) => searchParams.append(key, String(v)));
      } else {
        searchParams.append(key, String(value));
      }
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : '';
};

export { tokenService };
export default apiClient;
