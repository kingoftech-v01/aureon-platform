/**
 * Main App Component
 * Aureon by Rhematek Solutions
 *
 * Root application component with routing and providers
 */

import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, ProtectedRoute, PublicRoute } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { ToastProvider } from '@/components/common/Toast';
import { ErrorBoundary, PageLoadingFallback } from '@/components/common';
import { ProtectedLayout } from '@/components/layout';

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
const Landing = lazy(() => import('@/pages/Landing'));

// Marketing pages
const About = lazy(() => import('@/pages/marketing/About'));
const Contact = lazy(() => import('@/pages/marketing/Contact'));
const Privacy = lazy(() => import('@/pages/marketing/Privacy'));
const Terms = lazy(() => import('@/pages/marketing/Terms'));
const MarketingFAQ = lazy(() => import('@/pages/marketing/FAQ'));

// Dashboard pages
const Dashboard = lazy(() => import('@/pages/Dashboard'));
const Clients = lazy(() => import('@/pages/clients/ClientList'));
const ClientCreate = lazy(() => import('@/pages/clients/ClientCreate'));
const ClientDetail = lazy(() => import('@/pages/clients/ClientDetail'));
const ClientEdit = lazy(() => import('@/pages/clients/ClientEdit'));
const Contracts = lazy(() => import('@/pages/contracts/ContractList'));
const ContractCreate = lazy(() => import('@/pages/contracts/ContractCreate'));
const ContractDetail = lazy(() => import('@/pages/contracts/ContractDetail'));
const ContractEdit = lazy(() => import('@/pages/contracts/ContractEdit'));
const Invoices = lazy(() => import('@/pages/invoices/InvoiceList'));
const InvoiceCreate = lazy(() => import('@/pages/invoices/InvoiceCreate'));
const InvoiceDetail = lazy(() => import('@/pages/invoices/InvoiceDetail'));
const InvoiceEdit = lazy(() => import('@/pages/invoices/InvoiceEdit'));
const Payments = lazy(() => import('@/pages/payments/PaymentList'));
const PaymentCreate = lazy(() => import('@/pages/payments/PaymentCreate'));
const PaymentDetail = lazy(() => import('@/pages/payments/PaymentDetail'));
const Analytics = lazy(() => import('@/pages/analytics/Analytics'));
const RevenueForecast = lazy(() => import('@/pages/analytics/RevenueForecast'));
const NotificationCenter = lazy(() => import('@/pages/notifications/NotificationCenter'));
const Settings = lazy(() => import('@/pages/settings/Settings'));
const TeamManagement = lazy(() => import('@/pages/settings/TeamManagement'));
const IntegrationsPage = lazy(() => import('@/pages/settings/IntegrationsPage'));
const WebhookManagement = lazy(() => import('@/pages/webhooks/WebhookManagement'));
const ActivityFeed = lazy(() => import('@/pages/activity/ActivityFeed'));
const RecurringInvoices = lazy(() => import('@/pages/invoices/RecurringInvoices'));
const GlobalSearch = lazy(() => import('@/pages/search/GlobalSearch'));

// New pages - Settings
const ProfilePage = lazy(() => import('@/pages/settings/ProfilePage'));
const BillingPage = lazy(() => import('@/pages/settings/BillingPage'));
const ApiKeysPage = lazy(() => import('@/pages/settings/ApiKeysPage'));

// New pages - Proposals & Templates
const ProposalList = lazy(() => import('@/pages/proposals/ProposalList'));
const ProposalCreate = lazy(() => import('@/pages/proposals/ProposalCreate'));
const TemplateManager = lazy(() => import('@/pages/templates/TemplateManager'));

// New pages - Documents & Calendar
const DocumentVault = lazy(() => import('@/pages/documents/DocumentVault'));
const CalendarView = lazy(() => import('@/pages/calendar/CalendarView'));

// New pages - Reports
const TaxReport = lazy(() => import('@/pages/reports/TaxReport'));
const DataImport = lazy(() => import('@/pages/reports/DataImport'));
const RevenueRecognition = lazy(() => import('@/pages/reports/RevenueRecognition'));

// New pages - Analytics
const FinancialHealth = lazy(() => import('@/pages/analytics/FinancialHealth'));
const ClientInsights = lazy(() => import('@/pages/analytics/ClientInsights'));
const CashFlowForecast = lazy(() => import('@/pages/analytics/CashFlowForecast'));
const ConversionFunnel = lazy(() => import('@/pages/analytics/ConversionFunnel'));

// New pages - Clients
const ClientTimeline = lazy(() => import('@/pages/clients/ClientTimeline'));
const ClientMap = lazy(() => import('@/pages/clients/ClientMap'));
const ClientSurvey = lazy(() => import('@/pages/clients/ClientSurvey'));

// New pages - Invoices & Payments
const InvoiceAging = lazy(() => import('@/pages/invoices/InvoiceAging'));
const InvoicePDFPreview = lazy(() => import('@/pages/invoices/InvoicePDFPreview'));
const PaymentReceipt = lazy(() => import('@/pages/payments/PaymentReceipt'));

// New pages - Other
const KanbanBoard = lazy(() => import('@/pages/kanban/KanbanBoard'));
const HelpCenter = lazy(() => import('@/pages/help/HelpCenter'));
const ContractVersions = lazy(() => import('@/pages/contracts/ContractVersions'));
const StripeConnect = lazy(() => import('@/pages/stripe/StripeConnect'));
const OnboardingWizard = lazy(() => import('@/pages/onboarding/OnboardingWizard'));

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
                <Suspense fallback={<PageLoadingFallback />}>
                  <Routes>
                    {/* ================================ */}
                    {/* Public Routes                    */}
                    {/* ================================ */}

                    {/* Landing Page */}
                    <Route
                      path="/"
                      element={
                        <PublicRoute>
                          <Landing />
                        </PublicRoute>
                      }
                    />

                    {/* Marketing Pages */}
                    <Route path="/about" element={<About />} />
                    <Route path="/contact" element={<Contact />} />
                    <Route path="/privacy" element={<Privacy />} />
                    <Route path="/terms" element={<Terms />} />
                    <Route path="/faq" element={<MarketingFAQ />} />

                    {/* Auth Routes (redirect to dashboard if authenticated) */}
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

                    {/* MFA Routes (no Layout wrapper) */}
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

                    {/* Onboarding (protected, but no Layout) */}
                    <Route
                      path="/onboarding"
                      element={
                        <ProtectedRoute>
                          <OnboardingWizard />
                        </ProtectedRoute>
                      }
                    />

                    {/* ================================ */}
                    {/* Protected Routes with Layout     */}
                    {/* ================================ */}
                    <Route element={<ProtectedLayout />}>
                      {/* Dashboard */}
                      <Route path="/dashboard" element={<Dashboard />} />

                      {/* Clients */}
                      <Route path="/clients" element={<Clients />} />
                      <Route path="/clients/create" element={<ClientCreate />} />
                      <Route path="/clients/map" element={<ClientMap />} />
                      <Route path="/clients/surveys" element={<ClientSurvey />} />
                      <Route path="/clients/:id" element={<ClientDetail />} />
                      <Route path="/clients/:id/edit" element={<ClientEdit />} />
                      <Route path="/clients/:id/timeline" element={<ClientTimeline />} />

                      {/* Contracts */}
                      <Route path="/contracts" element={<Contracts />} />
                      <Route path="/contracts/create" element={<ContractCreate />} />
                      <Route path="/contracts/:id" element={<ContractDetail />} />
                      <Route path="/contracts/:id/edit" element={<ContractEdit />} />
                      <Route path="/contracts/:id/versions" element={<ContractVersions />} />

                      {/* Proposals */}
                      <Route path="/proposals" element={<ProposalList />} />
                      <Route path="/proposals/create" element={<ProposalCreate />} />

                      {/* Search */}
                      <Route path="/search" element={<GlobalSearch />} />

                      {/* Invoices */}
                      <Route path="/invoices" element={<Invoices />} />
                      <Route path="/invoices/recurring" element={<RecurringInvoices />} />
                      <Route path="/invoices/create" element={<InvoiceCreate />} />
                      <Route path="/invoices/aging" element={<InvoiceAging />} />
                      <Route path="/invoices/:id" element={<InvoiceDetail />} />
                      <Route path="/invoices/:id/edit" element={<InvoiceEdit />} />
                      <Route path="/invoices/:id/preview" element={<InvoicePDFPreview />} />

                      {/* Payments */}
                      <Route path="/payments" element={<Payments />} />
                      <Route path="/payments/create" element={<PaymentCreate />} />
                      <Route path="/payments/:id" element={<PaymentDetail />} />
                      <Route path="/payments/:id/receipt" element={<PaymentReceipt />} />

                      {/* Analytics */}
                      <Route path="/analytics" element={<Analytics />} />
                      <Route path="/analytics/forecast" element={<RevenueForecast />} />
                      <Route path="/analytics/health" element={<FinancialHealth />} />
                      <Route path="/analytics/clients" element={<ClientInsights />} />
                      <Route path="/analytics/cash-flow" element={<CashFlowForecast />} />
                      <Route path="/analytics/funnel" element={<ConversionFunnel />} />

                      {/* Documents */}
                      <Route path="/documents" element={<DocumentVault />} />
                      <Route path="/documents/*" element={<DocumentVault />} />

                      {/* Notifications */}
                      <Route path="/notifications" element={<NotificationCenter />} />

                      {/* Webhooks */}
                      <Route path="/webhooks" element={<WebhookManagement />} />

                      {/* Activity Feed */}
                      <Route path="/activity" element={<ActivityFeed />} />

                      {/* Templates */}
                      <Route path="/templates" element={<TemplateManager />} />

                      {/* Calendar */}
                      <Route path="/calendar" element={<CalendarView />} />

                      {/* Kanban */}
                      <Route path="/kanban" element={<KanbanBoard />} />

                      {/* Reports */}
                      <Route path="/reports/tax" element={<TaxReport />} />
                      <Route path="/reports/import" element={<DataImport />} />
                      <Route path="/reports/revenue-recognition" element={<RevenueRecognition />} />

                      {/* Stripe Connect */}
                      <Route path="/stripe/connect" element={<StripeConnect />} />

                      {/* Help Center */}
                      <Route path="/help" element={<HelpCenter />} />

                      {/* Settings */}
                      <Route path="/settings" element={<Settings />} />
                      <Route path="/settings/profile" element={<ProfilePage />} />
                      <Route path="/settings/team" element={<TeamManagement />} />
                      <Route path="/settings/billing" element={<BillingPage />} />
                      <Route path="/settings/api-keys" element={<ApiKeysPage />} />
                      <Route path="/settings/integrations" element={<IntegrationsPage />} />
                      <Route path="/settings/webhooks" element={<WebhookManagement />} />
                      <Route path="/settings/*" element={<Settings />} />
                    </Route>

                    {/* 404 Not Found */}
                    <Route path="*" element={<Error404 />} />
                  </Routes>
                </Suspense>
              </AuthProvider>
            </ToastProvider>
          </ThemeProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
