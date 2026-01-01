/**
 * Main App Component
 * Aureon by Rhematek Solutions
 *
 * Root application component with routing and providers
 */

import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, ProtectedRoute, PublicRoute } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ToastProvider } from '@/components/common/Toast';
import { ErrorBoundary, PageLoadingFallback } from '@/components/common';
import { Layout } from '@/components/layout';

// Auth pages
import {
  Login,
  Register,
  ForgotPassword,
  ResetPassword,
  VerifyEmail,
} from '@/pages/auth';

// MFA pages
import {
  MFASetup,
  MFAAuthenticate,
  MFARecoveryCodes,
  MFADisable,
} from '@/pages/mfa';

// Error pages
import {
  Error403,
  Error404,
  Error429,
  Error500,
} from '@/pages/errors';

// Tenant pages
import {
  TenantWelcome,
  TenantInactive,
  TenantNotFound,
} from '@/pages/tenant';

// Public pages
const Landing = React.lazy(() => import('@/pages/Landing'));

// Dashboard pages
const Dashboard = React.lazy(() => import('@/pages/Dashboard'));
const Clients = React.lazy(() => import('@/pages/clients/ClientList'));
const ClientCreate = React.lazy(() => import('@/pages/clients/ClientCreate'));
const ClientDetail = React.lazy(() => import('@/pages/clients/ClientDetail'));
const ClientEdit = React.lazy(() => import('@/pages/clients/ClientEdit'));
const Contracts = React.lazy(() => import('@/pages/contracts/ContractList'));
const ContractCreate = React.lazy(() => import('@/pages/contracts/ContractCreate'));
const ContractDetail = React.lazy(() => import('@/pages/contracts/ContractDetail'));
const ContractEdit = React.lazy(() => import('@/pages/contracts/ContractEdit'));
const Invoices = React.lazy(() => import('@/pages/invoices/InvoiceList'));
const InvoiceCreate = React.lazy(() => import('@/pages/invoices/InvoiceCreate'));
const InvoiceDetail = React.lazy(() => import('@/pages/invoices/InvoiceDetail'));
const InvoiceEdit = React.lazy(() => import('@/pages/invoices/InvoiceEdit'));
const Payments = React.lazy(() => import('@/pages/payments/PaymentList'));
const Analytics = React.lazy(() => import('@/pages/analytics/Analytics'));
const Documents = React.lazy(() => import('@/pages/documents/DocumentList'));
const Settings = React.lazy(() => import('@/pages/settings/Settings'));

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

                    {/* MFA Routes */}
                    <Route path="/auth/mfa/authenticate" element={<MFAAuthenticate />} />
                    <Route
                      path="/auth/mfa/setup"
                      element={
                        <ProtectedRoute>
                          <MFASetup />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/auth/mfa/recovery-codes"
                      element={
                        <ProtectedRoute>
                          <MFARecoveryCodes />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/auth/mfa/disable"
                      element={
                        <ProtectedRoute>
                          <MFADisable />
                        </ProtectedRoute>
                      }
                    />

                    {/* Tenant Routes */}
                    <Route path="/tenant/welcome" element={<TenantWelcome />} />
                    <Route path="/tenant/inactive" element={<TenantInactive />} />
                    <Route path="/tenant/not-found" element={<TenantNotFound />} />

                    {/* Error Pages */}
                    <Route path="/error/403" element={<Error403 />} />
                    <Route path="/error/404" element={<Error404 />} />
                    <Route path="/error/429" element={<Error429 />} />
                    <Route path="/error/500" element={<Error500 />} />

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

                    {/* Clients Routes */}
                    <Route
                      path="/clients"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <Clients />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/clients/create"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <ClientCreate />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/clients/:id"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <ClientDetail />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/clients/:id/edit"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <ClientEdit />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />

                    {/* Contracts Routes */}
                    <Route
                      path="/contracts"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <Contracts />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/contracts/create"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <ContractCreate />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/contracts/:id"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <ContractDetail />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/contracts/:id/edit"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <ContractEdit />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />

                    {/* Invoices Routes */}
                    <Route
                      path="/invoices"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <Invoices />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/invoices/create"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <InvoiceCreate />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/invoices/:id"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <InvoiceDetail />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/invoices/:id/edit"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <InvoiceEdit />
                          </Layout>
                        </ProtectedRoute>
                      }
                    />

                    {/* Payments Routes */}
                    <Route
                      path="/payments"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <Payments />
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

                    {/* Analytics Route */}
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

                    {/* Documents Routes */}
                    <Route
                      path="/documents"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <Documents />
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

                    {/* Settings Routes */}
                    <Route
                      path="/settings"
                      element={
                        <ProtectedRoute>
                          <Layout>
                            <Settings />
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

                    {/* Public Landing Page */}
                    <Route
                      path="/"
                      element={
                        <PublicRoute>
                          <Landing />
                        </PublicRoute>
                      }
                    />

                    {/* 404 Not Found */}
                    <Route path="*" element={<Error404 />} />
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
