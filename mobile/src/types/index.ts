/**
 * Aureon Mobile TypeScript Types
 * Adapted from frontend/src/types/index.ts
 */

// ============================================
// USER & AUTHENTICATION TYPES
// ============================================

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: UserRole;
  avatar?: string;
  phone_number?: string;
  is_active: boolean;
  is_email_verified: boolean;
  two_factor_enabled: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
}

export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  CONTRIBUTOR = 'contributor',
  CLIENT = 'client',
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  password_confirm: string;
  first_name: string;
  last_name: string;
  organization_name?: string;
}

// ============================================
// CLIENT TYPES
// ============================================

export interface Client {
  id: string;
  type: ClientType;
  company_name?: string;
  first_name?: string;
  last_name?: string;
  email: string;
  phone_number?: string;
  address?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  website?: string;
  lifecycle_stage: LifecycleStage;
  tags: string[];
  total_revenue: number;
  annual_recurring_revenue: number;
  lifetime_value: number;
  portal_access_enabled: boolean;
  portal_last_login?: string;
  notes: string;
  created_at: string;
  updated_at: string;
  created_by: string;
}

export enum ClientType {
  INDIVIDUAL = 'individual',
  COMPANY = 'company',
}

export enum LifecycleStage {
  LEAD = 'lead',
  PROSPECT = 'prospect',
  ACTIVE = 'active',
  CHURNED = 'churned',
  ARCHIVED = 'archived',
}

// ============================================
// CONTRACT TYPES
// ============================================

export interface Contract {
  id: string;
  contract_number: string;
  client: Client;
  title: string;
  description: string;
  content: string;
  status: ContractStatus;
  start_date?: string;
  end_date?: string;
  total_value: number;
  currency: string;
  signed_at?: string;
  signed_by_client?: string;
  signed_by_provider?: string;
  version: number;
  milestones: ContractMilestone[];
  created_at: string;
  updated_at: string;
  created_by: User;
}

export enum ContractStatus {
  DRAFT = 'draft',
  SENT = 'sent',
  VIEWED = 'viewed',
  SIGNED = 'signed',
  ACTIVE = 'active',
  COMPLETED = 'completed',
  TERMINATED = 'terminated',
  EXPIRED = 'expired',
}

export interface ContractMilestone {
  id: string;
  contract: string;
  title: string;
  description: string;
  amount: number;
  due_date?: string;
  is_completed: boolean;
  completed_at?: string;
  order: number;
}

// ============================================
// INVOICE TYPES
// ============================================

export interface Invoice {
  id: string;
  invoice_number: string;
  client: Client;
  contract?: string;
  status: InvoiceStatus;
  issue_date: string;
  due_date: string;
  paid_date?: string;
  subtotal: number;
  tax_rate: number;
  tax_amount: number;
  discount_amount: number;
  total: number;
  currency: string;
  notes?: string;
  payment_terms?: string;
  items: InvoiceItem[];
  is_recurring: boolean;
  created_at: string;
  updated_at: string;
}

export enum InvoiceStatus {
  DRAFT = 'draft',
  SENT = 'sent',
  VIEWED = 'viewed',
  PAID = 'paid',
  PARTIALLY_PAID = 'partially_paid',
  OVERDUE = 'overdue',
  CANCELLED = 'cancelled',
}

export interface InvoiceItem {
  id: string;
  invoice: string;
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
  total: number;
}

// ============================================
// PAYMENT TYPES
// ============================================

export interface Payment {
  id: string;
  payment_number: string;
  invoice: Invoice;
  amount: number;
  currency: string;
  status: PaymentStatus;
  payment_method: PaymentMethod;
  stripe_payment_intent_id?: string;
  transaction_id?: string;
  paid_at?: string;
  notes?: string;
  receipt_url?: string;
  created_at: string;
  updated_at: string;
}

export enum PaymentStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  SUCCEEDED = 'succeeded',
  FAILED = 'failed',
  REFUNDED = 'refunded',
  PARTIALLY_REFUNDED = 'partially_refunded',
}

export interface PaymentMethod {
  id: string;
  type: PaymentMethodType;
  last4?: string;
  brand?: string;
  exp_month?: number;
  exp_year?: number;
  is_default: boolean;
}

export enum PaymentMethodType {
  CARD = 'card',
  BANK_ACCOUNT = 'bank_account',
  PAYPAL = 'paypal',
}

// ============================================
// ANALYTICS TYPES
// ============================================

export interface DashboardStats {
  total_revenue: number;
  monthly_recurring_revenue: number;
  total_clients: number;
  active_contracts: number;
  pending_invoices: number;
  overdue_invoices: number;
  revenue_growth: number;
  client_growth: number;
}

export interface RevenueMetric {
  date: string;
  revenue: number;
  invoices_count: number;
  payments_count: number;
}

export interface ActivityItem {
  id: string;
  type: string;
  description: string;
  amount?: number;
  currency?: string;
  created_at: string;
}

// ============================================
// API RESPONSE TYPES
// ============================================

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  detail?: string;
  message?: string;
  errors?: Record<string, string[]>;
}

// ============================================
// FORM TYPES
// ============================================

export interface ClientFormData {
  type: ClientType;
  company_name?: string;
  first_name?: string;
  last_name?: string;
  email: string;
  phone_number?: string;
  address?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  website?: string;
  lifecycle_stage: LifecycleStage;
  tags?: string[];
  notes?: string;
}

export interface ContractFormData {
  client: string;
  title: string;
  description?: string;
  content: string;
  start_date?: string;
  end_date?: string;
  total_value: number;
  currency: string;
}

export interface InvoiceFormData {
  client: string;
  contract?: string;
  issue_date: string;
  due_date: string;
  tax_rate: number;
  discount_amount?: number;
  notes?: string;
  payment_terms?: string;
  items: InvoiceItemFormData[];
}

export interface InvoiceItemFormData {
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
}

// ============================================
// UTILITY TYPES
// ============================================

export type SortDirection = 'asc' | 'desc';

export interface FilterConfig {
  [key: string]: any;
}

export interface PaginationConfig {
  page: number;
  page_size: number;
}
