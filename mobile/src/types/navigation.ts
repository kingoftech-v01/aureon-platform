/**
 * Navigation type definitions
 */

import { NavigatorScreenParams } from '@react-navigation/native';

// Auth Stack
export type AuthStackParamList = {
  Login: undefined;
  Register: undefined;
  ForgotPassword: undefined;
};

// Dashboard Stack
export type DashboardStackParamList = {
  Dashboard: undefined;
};

// Client Stack
export type ClientStackParamList = {
  ClientList: undefined;
  ClientDetail: { clientId: string };
  ClientCreate: undefined;
  ClientEdit: { clientId: string };
};

// Invoice Stack
export type InvoiceStackParamList = {
  InvoiceList: undefined;
  InvoiceDetail: { invoiceId: string };
  InvoiceCreate: undefined;
  ContractList: undefined;
  ContractDetail: { contractId: string };
  ContractCreate: undefined;
};

// Analytics Stack
export type AnalyticsStackParamList = {
  Analytics: undefined;
};

// More Stack
export type MoreStackParamList = {
  Settings: undefined;
  Profile: undefined;
  PaymentList: undefined;
  PaymentDetail: { paymentId: string };
  ContractListAll: undefined;
  ContractDetailAll: { contractId: string };
};

// Main Tab Navigator
export type MainTabParamList = {
  DashboardTab: NavigatorScreenParams<DashboardStackParamList>;
  ClientsTab: NavigatorScreenParams<ClientStackParamList>;
  InvoicesTab: NavigatorScreenParams<InvoiceStackParamList>;
  AnalyticsTab: NavigatorScreenParams<AnalyticsStackParamList>;
  MoreTab: NavigatorScreenParams<MoreStackParamList>;
};

// Root Navigator
export type RootStackParamList = {
  Splash: undefined;
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<MainTabParamList>;
};
