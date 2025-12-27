/**
 * Authentication Context
 * Aureon by Rhematek Solutions
 *
 * Provides global authentication state management with:
 * - User state management
 * - Login/logout handlers
 * - Automatic token refresh
 * - Protected route wrapper
 */

import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { authService } from '@/services';
import { tokenService } from '@/services/api';
import type { User, LoginCredentials, RegisterData } from '@/types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (data: Partial<User>) => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const location = useLocation();

  /**
   * Load user from token on mount
   */
  const loadUser = useCallback(async () => {
    const accessToken = tokenService.getAccessToken();

    if (!accessToken) {
      setIsLoading(false);
      return;
    }

    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
      setError(null);
    } catch (err: any) {
      console.error('Failed to load user:', err);
      // Token might be invalid, clear it
      tokenService.clearTokens();
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadUser();
  }, [loadUser]);

  /**
   * Login handler
   */
  const login = useCallback(async (credentials: LoginCredentials) => {
    setIsLoading(true);
    setError(null);

    try {
      const { user: loggedInUser } = await authService.login(credentials);
      setUser(loggedInUser);

      // Redirect to intended page or dashboard
      const from = (location.state as any)?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'Login failed. Please check your credentials.';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [navigate, location]);

  /**
   * Register handler
   */
  const register = useCallback(async (data: RegisterData) => {
    setIsLoading(true);
    setError(null);

    try {
      const { user: registeredUser } = await authService.register(data);
      setUser(registeredUser);

      // Redirect to dashboard after registration
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'Registration failed. Please try again.';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [navigate]);

  /**
   * Logout handler
   */
  const logout = useCallback(async () => {
    setIsLoading(true);

    try {
      await authService.logout();
    } catch (err) {
      console.error('Logout error:', err);
      // Continue with local logout even if API call fails
    } finally {
      setUser(null);
      setError(null);
      navigate('/login', { replace: true });
      setIsLoading(false);
    }
  }, [navigate]);

  /**
   * Update user profile
   */
  const updateUser = useCallback(async (data: Partial<User>) => {
    if (!user) {
      throw new Error('No user logged in');
    }

    setIsLoading(true);
    setError(null);

    try {
      const updatedUser = await authService.updateProfile(user.id, data);
      setUser(updatedUser);
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'Failed to update profile.';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    error,
    login,
    register,
    logout,
    updateUser,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * Hook to use auth context
 */
export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
};

/**
 * Protected Route Component
 * Redirects to login if user is not authenticated
 */
interface ProtectedRouteProps {
  children: ReactNode;
  requiredRoles?: string[];
  redirectTo?: string;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles = [],
  redirectTo = '/login',
}) => {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      // Redirect to login, saving the intended destination
      navigate(redirectTo, {
        replace: true,
        state: { from: location },
      });
    }
  }, [isAuthenticated, isLoading, navigate, redirectTo, location]);

  useEffect(() => {
    // Check role permissions if required
    if (!isLoading && isAuthenticated && requiredRoles.length > 0 && user) {
      const hasRequiredRole = requiredRoles.includes(user.role);

      if (!hasRequiredRole) {
        // Redirect to unauthorized page
        navigate('/unauthorized', { replace: true });
      }
    }
  }, [isAuthenticated, isLoading, user, requiredRoles, navigate]);

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  // Only render children if authenticated (and authorized if roles are required)
  if (!isAuthenticated) {
    return null;
  }

  if (requiredRoles.length > 0 && user && !requiredRoles.includes(user.role)) {
    return null;
  }

  return <>{children}</>;
};

/**
 * Public Route Component (inverse of ProtectedRoute)
 * Redirects to dashboard if user is already authenticated
 * Useful for login/register pages
 */
interface PublicRouteProps {
  children: ReactNode;
  redirectTo?: string;
}

export const PublicRoute: React.FC<PublicRouteProps> = ({
  children,
  redirectTo = '/dashboard',
}) => {
  const { isAuthenticated, isLoading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      navigate(redirectTo, { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate, redirectTo]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (isAuthenticated) {
    return null;
  }

  return <>{children}</>;
};

export default AuthContext;
