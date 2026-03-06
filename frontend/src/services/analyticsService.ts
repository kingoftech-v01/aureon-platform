/**
 * Analytics and Dashboard API Service
 * Aureon by Rhematek Solutions
 */

import apiClient from './api';
import type {
  DashboardStats,
  RevenueMetric,
  AnalyticsSnapshot,
} from '@/types';

export const analyticsService = {
  /**
   * Get dashboard overview statistics
   */
  getDashboardStats: async (): Promise<DashboardStats> => {
    const response = await apiClient.get('/analytics/dashboard/');
    return response.data;
  },

  /**
   * Get revenue metrics
   */
  getRevenueMetrics: async (params?: {
    period?: 'day' | 'week' | 'month' | 'quarter' | 'year';
    start_date?: string;
    end_date?: string;
    group_by?: 'day' | 'week' | 'month';
  }): Promise<RevenueMetric[]> => {
    const queryParams = new URLSearchParams();
    if (params?.period) queryParams.set('period', params.period);
    if (params?.start_date) queryParams.set('start_date', params.start_date);
    if (params?.end_date) queryParams.set('end_date', params.end_date);
    if (params?.group_by) queryParams.set('group_by', params.group_by);

    const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const response = await apiClient.get(`/analytics/revenue/${queryString}`);
    return response.data;
  },

  /**
   * Get revenue by client
   */
  getRevenueByClient: async (params?: {
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<
    Array<{
      client_id: string;
      client_name: string;
      total_revenue: number;
      invoice_count: number;
      payment_count: number;
    }>
  > => {
    const queryParams = new URLSearchParams();
    if (params?.start_date) queryParams.set('start_date', params.start_date);
    if (params?.end_date) queryParams.set('end_date', params.end_date);
    if (params?.limit) queryParams.set('limit', params.limit.toString());

    const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const response = await apiClient.get(`/analytics/revenue/by-client/${queryString}`);
    return response.data;
  },

  /**
   * Get client lifecycle metrics
   */
  getClientMetrics: async (): Promise<{
    total_clients: number;
    active_clients: number;
    new_clients_this_month: number;
    churned_clients: number;
    by_lifecycle_stage: Record<string, number>;
    average_client_value: number;
    client_retention_rate: number;
  }> => {
    const response = await apiClient.get('/analytics/clients/');
    return response.data;
  },

  /**
   * Get client growth over time
   */
  getClientGrowth: async (params?: {
    period?: 'month' | 'quarter' | 'year';
    start_date?: string;
    end_date?: string;
  }): Promise<
    Array<{
      period: string;
      new_clients: number;
      churned_clients: number;
      net_growth: number;
      total_clients: number;
    }>
  > => {
    const queryParams = new URLSearchParams();
    if (params?.period) queryParams.set('period', params.period);
    if (params?.start_date) queryParams.set('start_date', params.start_date);
    if (params?.end_date) queryParams.set('end_date', params.end_date);

    const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const response = await apiClient.get(`/analytics/clients/growth/${queryString}`);
    return response.data;
  },

  /**
   * Get contract metrics
   */
  getContractMetrics: async (): Promise<{
    total_contracts: number;
    active_contracts: number;
    pending_signature: number;
    completed_contracts: number;
    total_contract_value: number;
    average_contract_value: number;
    contract_win_rate: number;
  }> => {
    const response = await apiClient.get('/analytics/contracts/');
    return response.data;
  },

  /**
   * Get contract conversion funnel
   */
  getContractFunnel: async (params?: {
    start_date?: string;
    end_date?: string;
  }): Promise<{
    leads: number;
    proposals_sent: number;
    contracts_signed: number;
    contracts_completed: number;
    conversion_rate: number;
  }> => {
    const queryParams = new URLSearchParams();
    if (params?.start_date) queryParams.set('start_date', params.start_date);
    if (params?.end_date) queryParams.set('end_date', params.end_date);

    const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const response = await apiClient.get(`/analytics/contracts/funnel/${queryString}`);
    return response.data;
  },

  /**
   * Get invoice metrics
   */
  getInvoiceMetrics: async (): Promise<{
    total_invoices: number;
    paid_invoices: number;
    unpaid_invoices: number;
    overdue_invoices: number;
    total_invoiced: number;
    total_paid: number;
    total_outstanding: number;
    average_days_to_payment: number;
  }> => {
    const response = await apiClient.get('/analytics/invoices/');
    return response.data;
  },

  /**
   * Get invoice aging report
   */
  getInvoiceAging: async (): Promise<{
    current: { count: number; amount: number };
    days_1_30: { count: number; amount: number };
    days_31_60: { count: number; amount: number };
    days_61_90: { count: number; amount: number };
    days_over_90: { count: number; amount: number };
  }> => {
    const response = await apiClient.get('/analytics/invoices/aging/');
    return response.data;
  },

  /**
   * Get payment metrics
   */
  getPaymentMetrics: async (): Promise<{
    total_payments: number;
    successful_payments: number;
    failed_payments: number;
    total_amount: number;
    average_payment_amount: number;
    payment_success_rate: number;
    total_refunded: number;
  }> => {
    const response = await apiClient.get('/analytics/payments/');
    return response.data;
  },

  /**
   * Get payment methods breakdown
   */
  getPaymentMethodBreakdown: async (): Promise<
    Array<{
      method: string;
      count: number;
      total_amount: number;
      percentage: number;
    }>
  > => {
    const response = await apiClient.get('/analytics/payments/methods/');
    return response.data;
  },

  /**
   * Get cash flow projection
   */
  getCashFlowProjection: async (params?: {
    months?: number;
    include_recurring?: boolean;
  }): Promise<
    Array<{
      month: string;
      expected_revenue: number;
      expected_payments: number;
      recurring_revenue: number;
      one_time_revenue: number;
    }>
  > => {
    const queryParams = new URLSearchParams();
    if (params?.months) queryParams.set('months', params.months.toString());
    if (params?.include_recurring !== undefined) {
      queryParams.set('include_recurring', params.include_recurring.toString());
    }

    const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const response = await apiClient.get(`/analytics/cash-flow/${queryString}`);
    return response.data;
  },

  /**
   * Get MRR (Monthly Recurring Revenue) metrics
   */
  getMRRMetrics: async (): Promise<{
    current_mrr: number;
    new_mrr: number;
    expansion_mrr: number;
    churned_mrr: number;
    net_mrr_growth: number;
    mrr_growth_rate: number;
  }> => {
    const response = await apiClient.get('/analytics/mrr/');
    return response.data;
  },

  /**
   * Get MRR trend over time
   */
  getMRRTrend: async (params?: {
    months?: number;
    start_date?: string;
    end_date?: string;
  }): Promise<
    Array<{
      month: string;
      mrr: number;
      new_mrr: number;
      churned_mrr: number;
      net_growth: number;
    }>
  > => {
    const queryParams = new URLSearchParams();
    if (params?.months) queryParams.set('months', params.months.toString());
    if (params?.start_date) queryParams.set('start_date', params.start_date);
    if (params?.end_date) queryParams.set('end_date', params.end_date);

    const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const response = await apiClient.get(`/analytics/mrr/trend/${queryString}`);
    return response.data;
  },

  /**
   * Get top performing services/products
   */
  getTopServices: async (params?: {
    limit?: number;
    period?: 'month' | 'quarter' | 'year';
  }): Promise<
    Array<{
      service_name: string;
      revenue: number;
      invoice_count: number;
      client_count: number;
    }>
  > => {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.period) queryParams.set('period', params.period);

    const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const response = await apiClient.get(`/analytics/services/top/${queryString}`);
    return response.data;
  },

  /**
   * Get analytics snapshot (for caching/offline)
   */
  getSnapshot: async (): Promise<AnalyticsSnapshot> => {
    const response = await apiClient.get('/analytics/snapshot/');
    return response.data;
  },

  /**
   * Export analytics report
   */
  exportReport: async (params: {
    report_type: 'revenue' | 'clients' | 'invoices' | 'payments' | 'comprehensive';
    format: 'pdf' | 'csv' | 'xlsx';
    start_date?: string;
    end_date?: string;
  }): Promise<Blob> => {
    const queryParams = new URLSearchParams();
    queryParams.set('report_type', params.report_type);
    queryParams.set('format', params.format);
    if (params.start_date) queryParams.set('start_date', params.start_date);
    if (params.end_date) queryParams.set('end_date', params.end_date);

    const response = await apiClient.get(`/analytics/export/?${queryParams.toString()}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Get real-time activity feed
   */
  getActivityFeed: async (params?: {
    limit?: number;
    offset?: number;
    event_types?: string[];
  }): Promise<
    Array<{
      id: string;
      timestamp: string;
      event_type: string;
      description: string;
      user?: { id: string; name: string };
      metadata?: Record<string, any>;
    }>
  > => {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.set('limit', params.limit.toString());
    if (params?.offset) queryParams.set('offset', params.offset.toString());
    if (params?.event_types) {
      params.event_types.forEach((type) => queryParams.append('event_types', type));
    }

    const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const response = await apiClient.get(`/analytics/activity/${queryString}`);
    return response.data;
  },

  /**
   * Get geographic revenue distribution
   */
  getRevenueByRegion: async (): Promise<
    Array<{
      country: string;
      country_code: string;
      revenue: number;
      client_count: number;
      invoice_count: number;
    }>
  > => {
    const response = await apiClient.get('/analytics/revenue/by-region/');
    return response.data;
  },

  /**
   * Get revenue forecast with AI-powered projections
   */
  getRevenueForecast: async (params?: {
    months?: number;
  }): Promise<{
    history: Array<{ month: string; revenue: number; confidence?: number }>;
    forecast: Array<{ month: string; revenue: number; confidence?: number }>;
    recurring_monthly_revenue: number;
    pending_receivables: number;
    trend: 'up' | 'down' | 'stable';
    average_monthly_revenue: number;
  }> => {
    const queryParams = new URLSearchParams();
    if (params?.months) queryParams.set('months', params.months.toString());

    const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const response = await apiClient.get(`/analytics/forecast/${queryString}`);
    return response.data;
  },

  /**
   * Get custom analytics query
   */
  customQuery: async (query: {
    metrics: string[];
    dimensions?: string[];
    filters?: Record<string, any>;
    start_date?: string;
    end_date?: string;
  }): Promise<any> => {
    const response = await apiClient.post('/analytics/custom/', query);
    return response.data;
  },
};

export default analyticsService;
