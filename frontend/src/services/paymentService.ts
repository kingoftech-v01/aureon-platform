/**
 * Payment Processing API Service
 * Aureon by Rhematek Solutions
 * Stripe Integration
 */

import apiClient from './api';
import type {
  Payment,
  PaymentMethod,
  PaymentStatus,
  Refund,
  PaginatedResponse,
  PaginationConfig,
  FilterConfig,
  SortConfig,
} from '@/types';

/**
 * Build query string from params
 */
const buildQueryParams = (params: Record<string, any>): string => {
  const filteredParams = Object.entries(params)
    .filter(([_, value]) => value !== undefined && value !== null && value !== '')
    .reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {});

  const queryString = new URLSearchParams(filteredParams).toString();
  return queryString ? `?${queryString}` : '';
};

export const paymentService = {
  /**
   * Get payments with pagination, filtering, and sorting
   */
  getPayments: async (
    pagination?: PaginationConfig,
    filters?: FilterConfig,
    sort?: SortConfig
  ): Promise<PaginatedResponse<Payment>> => {
    const params = {
      page: pagination?.page,
      page_size: pagination?.pageSize,
      ordering: sort ? `${sort.direction === 'desc' ? '-' : ''}${sort.field}` : undefined,
      status: filters?.status,
      client: filters?.client,
      date_from: filters?.date_from,
      date_to: filters?.date_to,
      ...filters,
    };

    const queryString = buildQueryParams(params);
    const response = await apiClient.get(`/payments/${queryString}`);
    return response.data;
  },

  /**
   * Get single payment by ID
   */
  getPayment: async (id: string): Promise<Payment> => {
    const response = await apiClient.get(`/payments/${id}/`);
    return response.data;
  },

  /**
   * Create payment intent (Stripe)
   */
  createPaymentIntent: async (data: {
    amount: number;
    currency: string;
    invoice_id?: string;
    client_id?: string;
    payment_method_id?: string;
    description?: string;
    metadata?: Record<string, any>;
  }): Promise<{
    client_secret: string;
    payment_intent_id: string;
  }> => {
    const response = await apiClient.post('/payments/create-intent/', data);
    return response.data;
  },

  /**
   * Confirm payment
   */
  confirmPayment: async (
    paymentIntentId: string,
    paymentMethodId?: string
  ): Promise<Payment> => {
    const response = await apiClient.post('/payments/confirm/', {
      payment_intent_id: paymentIntentId,
      payment_method_id: paymentMethodId,
    });
    return response.data;
  },

  /**
   * Process payment with saved payment method
   */
  processPayment: async (data: {
    amount: number;
    currency: string;
    payment_method_id: string;
    invoice_id?: string;
    client_id?: string;
    description?: string;
  }): Promise<Payment> => {
    const response = await apiClient.post('/payments/process/', data);
    return response.data;
  },

  /**
   * Get payment methods for client
   */
  getPaymentMethods: async (clientId?: string): Promise<PaymentMethod[]> => {
    const url = clientId ? `/payments/methods/?client=${clientId}` : '/payments/methods/';
    const response = await apiClient.get(url);
    return response.data;
  },

  /**
   * Add payment method
   */
  addPaymentMethod: async (data: {
    payment_method_id: string;
    client_id?: string;
    set_as_default?: boolean;
  }): Promise<PaymentMethod> => {
    const response = await apiClient.post('/payments/methods/', data);
    return response.data;
  },

  /**
   * Update payment method
   */
  updatePaymentMethod: async (
    id: string,
    data: {
      billing_details?: {
        name?: string;
        email?: string;
        phone?: string;
        address?: Record<string, any>;
      };
      set_as_default?: boolean;
    }
  ): Promise<PaymentMethod> => {
    const response = await apiClient.patch(`/payments/methods/${id}/`, data);
    return response.data;
  },

  /**
   * Delete payment method
   */
  deletePaymentMethod: async (id: string): Promise<void> => {
    await apiClient.delete(`/payments/methods/${id}/`);
  },

  /**
   * Set default payment method
   */
  setDefaultPaymentMethod: async (id: string): Promise<PaymentMethod> => {
    const response = await apiClient.post(`/payments/methods/${id}/set_default/`);
    return response.data;
  },

  /**
   * Create refund
   */
  createRefund: async (data: {
    payment_id: string;
    amount?: number;
    reason?: 'duplicate' | 'fraudulent' | 'requested_by_customer';
    notes?: string;
  }): Promise<Refund> => {
    const response = await apiClient.post('/payments/refunds/', data);
    return response.data;
  },

  /**
   * Get refunds for payment
   */
  getRefunds: async (paymentId: string): Promise<Refund[]> => {
    const response = await apiClient.get(`/payments/${paymentId}/refunds/`);
    return response.data;
  },

  /**
   * Get refund by ID
   */
  getRefund: async (id: string): Promise<Refund> => {
    const response = await apiClient.get(`/payments/refunds/${id}/`);
    return response.data;
  },

  /**
   * Cancel refund (if pending)
   */
  cancelRefund: async (id: string): Promise<Refund> => {
    const response = await apiClient.post(`/payments/refunds/${id}/cancel/`);
    return response.data;
  },

  /**
   * Get payment statistics
   */
  getStats: async (): Promise<{
    total_payments: number;
    successful_payments: number;
    failed_payments: number;
    pending_payments: number;
    total_amount: number;
    total_refunded: number;
    average_transaction: number;
  }> => {
    const response = await apiClient.get('/payments/stats/');
    return response.data;
  },

  /**
   * Get payment receipt
   */
  getReceipt: async (id: string): Promise<Blob> => {
    const response = await apiClient.get(`/payments/${id}/receipt/`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Send receipt via email
   */
  sendReceipt: async (id: string, email?: string): Promise<void> => {
    await apiClient.post(`/payments/${id}/send_receipt/`, { email });
  },

  /**
   * Setup Stripe customer
   */
  setupStripeCustomer: async (clientId: string): Promise<{
    customer_id: string;
    setup_intent_client_secret: string;
  }> => {
    const response = await apiClient.post('/payments/setup-customer/', {
      client_id: clientId,
    });
    return response.data;
  },

  /**
   * Create subscription
   */
  createSubscription: async (data: {
    client_id: string;
    price_id: string;
    payment_method_id?: string;
    trial_days?: number;
    metadata?: Record<string, any>;
  }): Promise<{
    subscription_id: string;
    status: string;
    current_period_end: string;
    latest_invoice?: any;
  }> => {
    const response = await apiClient.post('/payments/subscriptions/', data);
    return response.data;
  },

  /**
   * Update subscription
   */
  updateSubscription: async (
    subscriptionId: string,
    data: {
      price_id?: string;
      payment_method_id?: string;
      proration_behavior?: 'create_prorations' | 'none' | 'always_invoice';
    }
  ): Promise<any> => {
    const response = await apiClient.patch(`/payments/subscriptions/${subscriptionId}/`, data);
    return response.data;
  },

  /**
   * Cancel subscription
   */
  cancelSubscription: async (
    subscriptionId: string,
    cancelAtPeriodEnd: boolean = true
  ): Promise<any> => {
    const response = await apiClient.post(`/payments/subscriptions/${subscriptionId}/cancel/`, {
      cancel_at_period_end: cancelAtPeriodEnd,
    });
    return response.data;
  },

  /**
   * Retry failed payment
   */
  retryPayment: async (id: string): Promise<Payment> => {
    const response = await apiClient.post(`/payments/${id}/retry/`);
    return response.data;
  },

  /**
   * Get payment disputes
   */
  getDisputes: async (): Promise<any[]> => {
    const response = await apiClient.get('/payments/disputes/');
    return response.data;
  },

  /**
   * Submit dispute evidence
   */
  submitDisputeEvidence: async (
    disputeId: string,
    evidence: Record<string, any>
  ): Promise<any> => {
    const response = await apiClient.post(`/payments/disputes/${disputeId}/evidence/`, evidence);
    return response.data;
  },

  /**
   * Get Stripe dashboard link
   */
  getStripeDashboardLink: async (): Promise<{ url: string }> => {
    const response = await apiClient.get('/payments/stripe-dashboard/');
    return response.data;
  },

  /**
   * Export payments to CSV
   */
  exportToCSV: async (filters?: FilterConfig): Promise<Blob> => {
    const queryString = buildQueryParams(filters || {});
    const response = await apiClient.get(`/payments/export/csv/${queryString}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Get payment timeline/history
   */
  getPaymentHistory: async (id: string): Promise<
    Array<{
      timestamp: string;
      event: string;
      description: string;
      amount?: number;
      status?: PaymentStatus;
    }>
  > => {
    const response = await apiClient.get(`/payments/${id}/history/`);
    return response.data;
  },

  /**
   * Verify webhook signature (for client-side webhook handling)
   */
  verifyWebhook: async (data: {
    payload: string;
    signature: string;
  }): Promise<{ verified: boolean }> => {
    const response = await apiClient.post('/payments/verify-webhook/', data);
    return response.data;
  },
};

export default paymentService;
