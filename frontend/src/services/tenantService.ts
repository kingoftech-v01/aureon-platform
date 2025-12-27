/**
 * Tenant Management API Service
 * Aureon by Rhematek Solutions
 * Multi-tenancy support
 */

import apiClient from './api';
import type {
  Tenant,
  Domain,
  SubscriptionPlan,
} from '@/types';

export const tenantService = {
  /**
   * Get current tenant information
   */
  getCurrentTenant: async (): Promise<Tenant> => {
    const response = await apiClient.get('/tenants/current/');
    return response.data;
  },

  /**
   * Update current tenant
   */
  updateTenant: async (data: Partial<Tenant>): Promise<Tenant> => {
    const response = await apiClient.patch('/tenants/current/', data);
    return response.data;
  },

  /**
   * Get tenant settings
   */
  getSettings: async (): Promise<{
    branding: {
      logo_url?: string;
      primary_color?: string;
      secondary_color?: string;
      company_name: string;
    };
    features: {
      contracts_enabled: boolean;
      invoicing_enabled: boolean;
      payments_enabled: boolean;
      analytics_enabled: boolean;
      multi_currency_enabled: boolean;
      webhooks_enabled: boolean;
    };
    limits: {
      max_users: number;
      max_clients: number;
      max_contracts_per_month: number;
      max_invoices_per_month: number;
      storage_limit_mb: number;
    };
    integrations: {
      stripe_connected: boolean;
      email_configured: boolean;
      calendar_connected: boolean;
    };
  }> => {
    const response = await apiClient.get('/tenants/settings/');
    return response.data;
  },

  /**
   * Update tenant settings
   */
  updateSettings: async (settings: any): Promise<any> => {
    const response = await apiClient.patch('/tenants/settings/', settings);
    return response.data;
  },

  /**
   * Upload tenant logo
   */
  uploadLogo: async (file: File): Promise<{ logo_url: string }> => {
    const formData = new FormData();
    formData.append('logo', file);

    const response = await apiClient.post('/tenants/logo/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  /**
   * Get tenant domains
   */
  getDomains: async (): Promise<Domain[]> => {
    const response = await apiClient.get('/tenants/domains/');
    return response.data;
  },

  /**
   * Add custom domain
   */
  addDomain: async (domain: string, isPrimary: boolean = false): Promise<Domain> => {
    const response = await apiClient.post('/tenants/domains/', {
      domain,
      is_primary: isPrimary,
    });
    return response.data;
  },

  /**
   * Verify domain
   */
  verifyDomain: async (domainId: string): Promise<{
    verified: boolean;
    dns_records: Array<{
      type: string;
      name: string;
      value: string;
    }>;
  }> => {
    const response = await apiClient.post(`/tenants/domains/${domainId}/verify/`);
    return response.data;
  },

  /**
   * Set primary domain
   */
  setPrimaryDomain: async (domainId: string): Promise<Domain> => {
    const response = await apiClient.post(`/tenants/domains/${domainId}/set_primary/`);
    return response.data;
  },

  /**
   * Delete domain
   */
  deleteDomain: async (domainId: string): Promise<void> => {
    await apiClient.delete(`/tenants/domains/${domainId}/`);
  },

  /**
   * Get subscription information
   */
  getSubscription: async (): Promise<{
    plan: SubscriptionPlan;
    status: 'active' | 'trial' | 'past_due' | 'canceled' | 'paused';
    current_period_start: string;
    current_period_end: string;
    trial_end?: string;
    cancel_at_period_end: boolean;
    stripe_subscription_id?: string;
  }> => {
    const response = await apiClient.get('/tenants/subscription/');
    return response.data;
  },

  /**
   * Get available subscription plans
   */
  getPlans: async (): Promise<SubscriptionPlan[]> => {
    const response = await apiClient.get('/tenants/plans/');
    return response.data;
  },

  /**
   * Upgrade/change subscription plan
   */
  changePlan: async (planId: string, billingCycle: 'monthly' | 'yearly'): Promise<{
    subscription: any;
    proration_amount?: number;
    next_invoice_amount: number;
  }> => {
    const response = await apiClient.post('/tenants/subscription/change-plan/', {
      plan_id: planId,
      billing_cycle: billingCycle,
    });
    return response.data;
  },

  /**
   * Cancel subscription
   */
  cancelSubscription: async (cancelAtPeriodEnd: boolean = true): Promise<any> => {
    const response = await apiClient.post('/tenants/subscription/cancel/', {
      cancel_at_period_end: cancelAtPeriodEnd,
    });
    return response.data;
  },

  /**
   * Resume canceled subscription
   */
  resumeSubscription: async (): Promise<any> => {
    const response = await apiClient.post('/tenants/subscription/resume/');
    return response.data;
  },

  /**
   * Get billing history
   */
  getBillingHistory: async (): Promise<
    Array<{
      id: string;
      date: string;
      amount: number;
      status: 'paid' | 'pending' | 'failed';
      invoice_url?: string;
      description: string;
    }>
  > => {
    const response = await apiClient.get('/tenants/billing/history/');
    return response.data;
  },

  /**
   * Get upcoming invoice
   */
  getUpcomingInvoice: async (): Promise<{
    amount: number;
    date: string;
    items: Array<{
      description: string;
      amount: number;
    }>;
  }> => {
    const response = await apiClient.get('/tenants/billing/upcoming/');
    return response.data;
  },

  /**
   * Update payment method
   */
  updatePaymentMethod: async (paymentMethodId: string): Promise<void> => {
    await apiClient.post('/tenants/billing/payment-method/', {
      payment_method_id: paymentMethodId,
    });
  },

  /**
   * Get usage statistics
   */
  getUsageStats: async (): Promise<{
    current_period: {
      users: { current: number; limit: number };
      clients: { current: number; limit: number };
      contracts: { current: number; limit: number };
      invoices: { current: number; limit: number };
      storage_mb: { current: number; limit: number };
    };
    historical: Array<{
      period: string;
      users: number;
      clients: number;
      contracts: number;
      invoices: number;
      storage_mb: number;
    }>;
  }> => {
    const response = await apiClient.get('/tenants/usage/');
    return response.data;
  },

  /**
   * Get team members
   */
  getTeamMembers: async (): Promise<
    Array<{
      id: string;
      email: string;
      first_name: string;
      last_name: string;
      role: string;
      is_active: boolean;
      last_login?: string;
      created_at: string;
    }>
  > => {
    const response = await apiClient.get('/tenants/team/');
    return response.data;
  },

  /**
   * Invite team member
   */
  inviteTeamMember: async (data: {
    email: string;
    role: string;
    first_name?: string;
    last_name?: string;
  }): Promise<{
    invitation_id: string;
    email: string;
    expires_at: string;
  }> => {
    const response = await apiClient.post('/tenants/team/invite/', data);
    return response.data;
  },

  /**
   * Resend team invitation
   */
  resendInvitation: async (invitationId: string): Promise<void> => {
    await apiClient.post(`/tenants/team/invitations/${invitationId}/resend/`);
  },

  /**
   * Cancel team invitation
   */
  cancelInvitation: async (invitationId: string): Promise<void> => {
    await apiClient.delete(`/tenants/team/invitations/${invitationId}/`);
  },

  /**
   * Update team member role
   */
  updateTeamMemberRole: async (userId: string, role: string): Promise<any> => {
    const response = await apiClient.patch(`/tenants/team/${userId}/`, { role });
    return response.data;
  },

  /**
   * Remove team member
   */
  removeTeamMember: async (userId: string): Promise<void> => {
    await apiClient.delete(`/tenants/team/${userId}/`);
  },

  /**
   * Get audit logs
   */
  getAuditLogs: async (params?: {
    page?: number;
    page_size?: number;
    user_id?: string;
    action?: string;
    start_date?: string;
    end_date?: string;
  }): Promise<{
    results: Array<{
      id: string;
      timestamp: string;
      user: { id: string; name: string };
      action: string;
      resource_type: string;
      resource_id?: string;
      ip_address?: string;
      user_agent?: string;
      changes?: Record<string, any>;
    }>;
    count: number;
    next?: string;
    previous?: string;
  }> => {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set('page', params.page.toString());
    if (params?.page_size) queryParams.set('page_size', params.page_size.toString());
    if (params?.user_id) queryParams.set('user_id', params.user_id);
    if (params?.action) queryParams.set('action', params.action);
    if (params?.start_date) queryParams.set('start_date', params.start_date);
    if (params?.end_date) queryParams.set('end_date', params.end_date);

    const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const response = await apiClient.get(`/tenants/audit-logs/${queryString}`);
    return response.data;
  },

  /**
   * Export tenant data
   */
  exportData: async (format: 'json' | 'csv' = 'json'): Promise<Blob> => {
    const response = await apiClient.get(`/tenants/export/?format=${format}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Delete tenant account (danger zone)
   */
  deleteTenant: async (confirmation: string): Promise<void> => {
    await apiClient.post('/tenants/delete/', { confirmation });
  },

  /**
   * Get API keys
   */
  getAPIKeys: async (): Promise<
    Array<{
      id: string;
      name: string;
      key_prefix: string;
      created_at: string;
      last_used?: string;
      expires_at?: string;
    }>
  > => {
    const response = await apiClient.get('/tenants/api-keys/');
    return response.data;
  },

  /**
   * Create API key
   */
  createAPIKey: async (data: {
    name: string;
    expires_in_days?: number;
    scopes?: string[];
  }): Promise<{
    id: string;
    name: string;
    key: string;
    expires_at?: string;
  }> => {
    const response = await apiClient.post('/tenants/api-keys/', data);
    return response.data;
  },

  /**
   * Revoke API key
   */
  revokeAPIKey: async (keyId: string): Promise<void> => {
    await apiClient.delete(`/tenants/api-keys/${keyId}/`);
  },
};

export default tenantService;
