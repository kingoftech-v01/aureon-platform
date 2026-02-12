/**
 * Aureon Frontend TypeScript Types
 * Rhematek Solutions
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
  company_name?: string;
}

// ============================================
// TENANT TYPES
// ============================================

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  plan: SubscriptionPlan;
  is_active: boolean;
  trial_ends_at?: string;
  subscription_ends_at?: string;
  max_users: number;
  max_clients: number;
  max_contracts_per_month: number;
  max_invoices_per_month: number;
  storage_limit_gb: number;
  custom_domain?: string;
  logo?: string;
  primary_color?: string;
  accent_color?: string;
  created_at: string;
  updated_at: string;
}

export enum SubscriptionPlan {
  FREE = 'free',
  STARTER = 'starter',
  PRO = 'pro',
  BUSINESS = 'business',
}

export interface Domain {
  id: string;
  domain: string;
  is_primary: boolean;
  is_verified: boolean;
  tenant: string;
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

export interface ClientNote {
  id: string;
  client: string;
  content: string;
  created_by: User;
  created_at: string;
  updated_at: string;
}

// ============================================
// CONTRACT TYPES
// ============================================

export interface Contract {
  id: string;
  contract_number: string;
  client: Client;
  template?: string;
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
  document_url?: string;
  version: number;
  parent_contract?: string;
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

export interface ContractTemplate {
  id: string;
  name: string;
  description: string;
  content: string;
  category: string;
  is_active: boolean;
  variables: Record<string, any>;
  created_at: string;
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
  document_url?: string;
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

export interface RecurringInvoice {
  id: string;
  client: Client;
  frequency: RecurrenceFrequency;
  start_date: string;
  end_date?: string;
  next_invoice_date: string;
  is_active: boolean;
  template_invoice: Invoice;
}

export enum RecurrenceFrequency {
  WEEKLY = 'weekly',
  BIWEEKLY = 'biweekly',
  MONTHLY = 'monthly',
  QUARTERLY = 'quarterly',
  ANNUALLY = 'annually',
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
  CANCELLED = 'cancelled',
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
  stripe_payment_method_id?: string;
}

export enum PaymentMethodType {
  CARD = 'card',
  BANK_ACCOUNT = 'bank_account',
  PAYPAL = 'paypal',
}

export interface Refund {
  id: string;
  payment: string;
  amount: number;
  reason?: string;
  status: RefundStatus;
  stripe_refund_id?: string;
  created_at: string;
}

export enum RefundStatus {
  PENDING = 'pending',
  SUCCEEDED = 'succeeded',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

// ============================================
// NOTIFICATION TYPES
// ============================================

export interface Notification {
  id: string;
  user: string;
  type: NotificationType;
  title: string;
  message: string;
  link?: string;
  is_read: boolean;
  read_at?: string;
  created_at: string;
}

export enum NotificationType {
  INFO = 'info',
  SUCCESS = 'success',
  WARNING = 'warning',
  ERROR = 'error',
  CONTRACT_SIGNED = 'contract_signed',
  INVOICE_PAID = 'invoice_paid',
  PAYMENT_RECEIVED = 'payment_received',
  PAYMENT_FAILED = 'payment_failed',
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

export interface AnalyticsSnapshot {
  id: string;
  tenant: string;
  date: string;
  total_revenue: number;
  mrr: number;
  arr: number;
  total_clients: number;
  active_clients: number;
  churned_clients: number;
  total_contracts: number;
  signed_contracts: number;
  total_invoices: number;
  paid_invoices: number;
  average_invoice_value: number;
  created_at: string;
}

// ============================================
// DOCUMENT TYPES
// ============================================

export interface Document {
  id: string;
  title: string;
  description?: string;
  file_url: string;
  file_type: string;
  file_size: number;
  category: DocumentCategory;
  related_client?: string;
  related_contract?: string;
  related_invoice?: string;
  version: number;
  is_current_version: boolean;
  uploaded_by: User;
  created_at: string;
  updated_at: string;
}

export enum DocumentCategory {
  CONTRACT = 'contract',
  INVOICE = 'invoice',
  RECEIPT = 'receipt',
  PROPOSAL = 'proposal',
  OTHER = 'other',
}

// ============================================
// WEBHOOK TYPES
// ============================================

export interface Webhook {
  id: string;
  name: string;
  url: string;
  events: WebhookEvent[];
  is_active: boolean;
  secret: string;
  created_at: string;
  updated_at: string;
}

export enum WebhookEvent {
  CONTRACT_SIGNED = 'contract.signed',
  INVOICE_CREATED = 'invoice.created',
  INVOICE_PAID = 'invoice.paid',
  PAYMENT_RECEIVED = 'payment.received',
  PAYMENT_FAILED = 'payment.failed',
  CLIENT_CREATED = 'client.created',
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
  template?: string;
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

export interface SortConfig {
  field: string;
  direction: SortDirection;
}

export interface FilterConfig {
  [key: string]: any;
}

export interface PaginationConfig {
  page: number;
  page_size: number;
  pageSize?: number; // alias
}
