/**
 * Main App Component
 * Aureon by Rhematek Solutions
 *
 * Root application component with routing and providers
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, ProtectedRoute, PublicRoute } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ToastProvider } from '@/components/common/Toast';
import { ErrorBoundary, PageLoadingFallback, LoadingErrorFallback } from '@/components/common';
import { Layout } from '@/components/layout';

// Auth pages
import {
  Login,
  Register,
  ForgotPassword,
  ResetPassword,
  VerifyEmail,
} from '@/pages/auth';

// Dashboard pages (placeholders for now)
const Dashboard = React.lazy(() => import('@/pages/Dashboard'));
const Clients = React.lazy(() => import('@/pages/clients/ClientList'));
const Contracts = React.lazy(() => import('@/pages/contracts/ContractList'));
const Invoices = React.lazy(() => import('@/pages/invoices/InvoiceList'));
const Payments = React.lazy(() => import('@/pages/payments/PaymentList'));
const Analytics = React.lazy(() => import('@/pages/analytics/Analytics'));
const Documents = React.lazy(() => import('@/pages/documents/DocumentList'));
const Settings = React.lazy(() => import('@/pages/settings/Settings'));
const NotFound = React.lazy(() => import('@/pages/NotFound'));

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

/**
 * Main App Component
 */
const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <ThemeProvider defaultTheme="system">
            <ToastProvider>
              <AuthProvider>
                <React.Suspense fallback={<PageLoadingFallback />}>
                  <Routes>
                    {/* Public Routes (redirect to dashboard if authenticated) */}
                    <Route
                      path="/auth/login"
                      element={
                        <PublicRoute>
                          <Login />
                        </PublicRoute>
                      }
                    />
                    <Route
                      path="/auth/register"
                      element={
                        <PublicRoute>
                          <Register />
                        </PublicRoute>
                      }
                    />
                    <Route
                      path="/auth/forgot-password"
                      element={
                        <PublicRoute>
                          <ForgotPassword />
                        </PublicRoute>
                      }
                    />
                    <Route
                      path="/auth/reset-password"
                      element={
                        <PublicRoute>
                          <ResetPassword />
                        </PublicRoute>
                      }
                    />
                    <Route
                      path="/auth/verify-email"
                      element={
                        <PublicRoute>
                          <VerifyEmail />
                        </PublicRoute>
                      }
                    />

                    {/* Protected Routes (require authentication) */}
                    <Route
                      path="/dashboard"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <Dashboard />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />

                    <Route
                      path="/clients/*"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <Clients />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />

                    <Route
                      path="/contracts/*"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <Contracts />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />

                    <Route
                      path="/invoices/*"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <Invoices />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />

                    <Route
                      path="/payments/*"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <Payments />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />

                    <Route
                      path="/analytics"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <Analytics />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />

                    <Route
                      path="/documents/*"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <Documents />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />

                    <Route
                      path="/settings/*"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <Settings />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />

                    {/* Root redirect */}
                    <Route path="/" element={<Navigate to="/dashboard" replace />} />

                    {/* 404 Not Found */}
                    <Route path="*" element={<NotFound />} />
                  </Routes>
                </React.Suspense>
              </AuthProvider>
            </ToastProvider>
          </ThemeProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
