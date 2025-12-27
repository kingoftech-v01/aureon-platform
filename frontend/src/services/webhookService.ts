/**
 * Webhook Management API Service
 * Aureon by Rhematek Solutions
 */

import apiClient from './api';
import type {
  Webhook,
  WebhookEvent,
  PaginatedResponse,
  PaginationConfig,
} from '@/types';

export const webhookService = {
  /**
   * Get webhooks with pagination
   */
  getWebhooks: async (
    pagination?: PaginationConfig
  ): Promise<PaginatedResponse<Webhook>> => {
    const params = new URLSearchParams();
    if (pagination?.page) params.set('page', pagination.page.toString());
    if (pagination?.pageSize) params.set('page_size', pagination.pageSize.toString());

    const queryString = params.toString() ? `?${params.toString()}` : '';
    const response = await apiClient.get(`/webhooks/${queryString}`);
    return response.data;
  },

  /**
   * Get single webhook by ID
   */
  getWebhook: async (id: string): Promise<Webhook> => {
    const response = await apiClient.get(`/webhooks/${id}/`);
    return response.data;
  },

  /**
   * Create webhook
   */
  createWebhook: async (data: {
    url: string;
    events: string[];
    description?: string;
    secret?: string;
    is_active?: boolean;
    headers?: Record<string, string>;
  }): Promise<Webhook> => {
    const response = await apiClient.post('/webhooks/', data);
    return response.data;
  },

  /**
   * Update webhook
   */
  updateWebhook: async (
    id: string,
    data: {
      url?: string;
      events?: string[];
      description?: string;
      is_active?: boolean;
      headers?: Record<string, string>;
    }
  ): Promise<Webhook> => {
    const response = await apiClient.patch(`/webhooks/${id}/`, data);
    return response.data;
  },

  /**
   * Delete webhook
   */
  deleteWebhook: async (id: string): Promise<void> => {
    await apiClient.delete(`/webhooks/${id}/`);
  },

  /**
   * Test webhook
   */
  testWebhook: async (id: string): Promise<{
    success: boolean;
    status_code?: number;
    response_time_ms?: number;
    error?: string;
  }> => {
    const response = await apiClient.post(`/webhooks/${id}/test/`);
    return response.data;
  },

  /**
   * Enable webhook
   */
  enableWebhook: async (id: string): Promise<Webhook> => {
    const response = await apiClient.post(`/webhooks/${id}/enable/`);
    return response.data;
  },

  /**
   * Disable webhook
   */
  disableWebhook: async (id: string): Promise<Webhook> => {
    const response = await apiClient.post(`/webhooks/${id}/disable/`);
    return response.data;
  },

  /**
   * Regenerate webhook secret
   */
  regenerateSecret: async (id: string): Promise<{ secret: string }> => {
    const response = await apiClient.post(`/webhooks/${id}/regenerate-secret/`);
    return response.data;
  },

  /**
   * Get webhook events/deliveries
   */
  getWebhookEvents: async (
    webhookId: string,
    pagination?: PaginationConfig
  ): Promise<PaginatedResponse<WebhookEvent>> => {
    const params = new URLSearchParams();
    if (pagination?.page) params.set('page', pagination.page.toString());
    if (pagination?.pageSize) params.set('page_size', pagination.pageSize.toString());

    const queryString = params.toString() ? `?${params.toString()}` : '';
    const response = await apiClient.get(`/webhooks/${webhookId}/events/${queryString}`);
    return response.data;
  },

  /**
   * Get single webhook event
   */
  getWebhookEvent: async (webhookId: string, eventId: string): Promise<WebhookEvent> => {
    const response = await apiClient.get(`/webhooks/${webhookId}/events/${eventId}/`);
    return response.data;
  },

  /**
   * Retry failed webhook event
   */
  retryWebhookEvent: async (webhookId: string, eventId: string): Promise<{
    success: boolean;
    status_code?: number;
    error?: string;
  }> => {
    const response = await apiClient.post(`/webhooks/${webhookId}/events/${eventId}/retry/`);
    return response.data;
  },

  /**
   * Get available webhook event types
   */
  getEventTypes: async (): Promise<
    Array<{
      event: string;
      description: string;
      category: string;
      payload_example: Record<string, any>;
    }>
  > => {
    const response = await apiClient.get('/webhooks/event-types/');
    return response.data;
  },

  /**
   * Get webhook statistics
   */
  getWebhookStats: async (webhookId: string): Promise<{
    total_events: number;
    successful_deliveries: number;
    failed_deliveries: number;
    success_rate: number;
    average_response_time_ms: number;
    last_delivery?: string;
    recent_failures: Array<{
      timestamp: string;
      error: string;
      status_code?: number;
    }>;
  }> => {
    const response = await apiClient.get(`/webhooks/${webhookId}/stats/`);
    return response.data;
  },

  /**
   * Get all webhook deliveries (across all webhooks)
   */
  getAllDeliveries: async (
    pagination?: PaginationConfig,
    filters?: {
      status?: 'success' | 'failed' | 'pending';
      event_type?: string;
      start_date?: string;
      end_date?: string;
    }
  ): Promise<PaginatedResponse<WebhookEvent>> => {
    const params = new URLSearchParams();
    if (pagination?.page) params.set('page', pagination.page.toString());
    if (pagination?.pageSize) params.set('page_size', pagination.pageSize.toString());
    if (filters?.status) params.set('status', filters.status);
    if (filters?.event_type) params.set('event_type', filters.event_type);
    if (filters?.start_date) params.set('start_date', filters.start_date);
    if (filters?.end_date) params.set('end_date', filters.end_date);

    const queryString = params.toString() ? `?${params.toString()}` : '';
    const response = await apiClient.get(`/webhooks/deliveries/${queryString}`);
    return response.data;
  },

  /**
   * Bulk retry failed deliveries
   */
  bulkRetryFailed: async (webhookId: string, since?: string): Promise<{
    queued: number;
  }> => {
    const data = since ? { since } : {};
    const response = await apiClient.post(`/webhooks/${webhookId}/bulk-retry/`, data);
    return response.data;
  },

  /**
   * Clear webhook event history
   */
  clearHistory: async (
    webhookId: string,
    olderThan?: string
  ): Promise<{ deleted: number }> => {
    const data = olderThan ? { older_than: olderThan } : {};
    const response = await apiClient.post(`/webhooks/${webhookId}/clear-history/`, data);
    return response.data;
  },

  /**
   * Validate webhook signature (for incoming webhooks)
   */
  validateSignature: async (data: {
    payload: string;
    signature: string;
    secret: string;
  }): Promise<{ valid: boolean }> => {
    const response = await apiClient.post('/webhooks/validate-signature/', data);
    return response.data;
  },

  /**
   * Get webhook logs
   */
  getWebhookLogs: async (
    webhookId: string,
    params?: {
      page?: number;
      page_size?: number;
      level?: 'info' | 'warning' | 'error';
      start_date?: string;
      end_date?: string;
    }
  ): Promise<
    PaginatedResponse<{
      timestamp: string;
      level: string;
      message: string;
      event_id?: string;
      metadata?: Record<string, any>;
    }>
  > => {
    const queryParams = new URLSearchParams();
    if (params?.page) queryParams.set('page', params.page.toString());
    if (params?.page_size) queryParams.set('page_size', params.page_size.toString());
    if (params?.level) queryParams.set('level', params.level);
    if (params?.start_date) queryParams.set('start_date', params.start_date);
    if (params?.end_date) queryParams.set('end_date', params.end_date);

    const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
    const response = await apiClient.get(`/webhooks/${webhookId}/logs/${queryString}`);
    return response.data;
  },

  /**
   * Export webhook events to CSV
   */
  exportEvents: async (
    webhookId: string,
    filters?: {
      status?: string;
      start_date?: string;
      end_date?: string;
    }
  ): Promise<Blob> => {
    const params = new URLSearchParams();
    if (filters?.status) params.set('status', filters.status);
    if (filters?.start_date) params.set('start_date', filters.start_date);
    if (filters?.end_date) params.set('end_date', filters.end_date);

    const queryString = params.toString() ? `?${params.toString()}` : '';
    const response = await apiClient.get(`/webhooks/${webhookId}/export/${queryString}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Subscribe to webhook events via SSE (Server-Sent Events)
   */
  subscribeToEvents: async (webhookId?: string): Promise<{ stream_url: string }> => {
    const url = webhookId ? `/webhooks/${webhookId}/subscribe/` : '/webhooks/subscribe/';
    const response = await apiClient.get(url);
    return response.data;
  },

  /**
   * Get webhook health status
   */
  getHealthStatus: async (webhookId: string): Promise<{
    status: 'healthy' | 'degraded' | 'down';
    last_success?: string;
    consecutive_failures: number;
    uptime_percentage: number;
  }> => {
    const response = await apiClient.get(`/webhooks/${webhookId}/health/`);
    return response.data;
  },
};

export default webhookService;
