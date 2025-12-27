/**
 * Notification Management API Service
 * Aureon by Rhematek Solutions
 */

import apiClient from './api';
import type {
  Notification,
  NotificationType,
  PaginatedResponse,
  PaginationConfig,
} from '@/types';

export const notificationService = {
  /**
   * Get notifications with pagination
   */
  getNotifications: async (
    pagination?: PaginationConfig,
    filters?: {
      is_read?: boolean;
      type?: NotificationType;
    }
  ): Promise<PaginatedResponse<Notification>> => {
    const params = new URLSearchParams();
    if (pagination?.page) params.set('page', pagination.page.toString());
    if (pagination?.pageSize) params.set('page_size', pagination.pageSize.toString());
    if (filters?.is_read !== undefined) params.set('is_read', filters.is_read.toString());
    if (filters?.type) params.set('type', filters.type);

    const queryString = params.toString() ? `?${params.toString()}` : '';
    const response = await apiClient.get(`/notifications/${queryString}`);
    return response.data;
  },

  /**
   * Get unread notification count
   */
  getUnreadCount: async (): Promise<{ count: number }> => {
    const response = await apiClient.get('/notifications/unread-count/');
    return response.data;
  },

  /**
   * Get single notification
   */
  getNotification: async (id: string): Promise<Notification> => {
    const response = await apiClient.get(`/notifications/${id}/`);
    return response.data;
  },

  /**
   * Mark notification as read
   */
  markAsRead: async (id: string): Promise<Notification> => {
    const response = await apiClient.post(`/notifications/${id}/mark_read/`);
    return response.data;
  },

  /**
   * Mark notification as unread
   */
  markAsUnread: async (id: string): Promise<Notification> => {
    const response = await apiClient.post(`/notifications/${id}/mark_unread/`);
    return response.data;
  },

  /**
   * Mark all notifications as read
   */
  markAllAsRead: async (): Promise<{ updated: number }> => {
    const response = await apiClient.post('/notifications/mark_all_read/');
    return response.data;
  },

  /**
   * Delete notification
   */
  deleteNotification: async (id: string): Promise<void> => {
    await apiClient.delete(`/notifications/${id}/`);
  },

  /**
   * Delete all read notifications
   */
  deleteAllRead: async (): Promise<{ deleted: number }> => {
    const response = await apiClient.post('/notifications/delete_all_read/');
    return response.data;
  },

  /**
   * Get notification preferences
   */
  getPreferences: async (): Promise<{
    email_enabled: boolean;
    push_enabled: boolean;
    in_app_enabled: boolean;
    notification_types: Record<NotificationType, boolean>;
    digest_frequency?: 'immediate' | 'daily' | 'weekly';
  }> => {
    const response = await apiClient.get('/notifications/preferences/');
    return response.data;
  },

  /**
   * Update notification preferences
   */
  updatePreferences: async (preferences: {
    email_enabled?: boolean;
    push_enabled?: boolean;
    in_app_enabled?: boolean;
    notification_types?: Record<NotificationType, boolean>;
    digest_frequency?: 'immediate' | 'daily' | 'weekly';
  }): Promise<any> => {
    const response = await apiClient.patch('/notifications/preferences/', preferences);
    return response.data;
  },

  /**
   * Subscribe to push notifications
   */
  subscribeToPush: async (subscription: PushSubscription): Promise<void> => {
    await apiClient.post('/notifications/push-subscribe/', {
      subscription: subscription.toJSON(),
    });
  },

  /**
   * Unsubscribe from push notifications
   */
  unsubscribeFromPush: async (): Promise<void> => {
    await apiClient.post('/notifications/push-unsubscribe/');
  },

  /**
   * Test notification (development/testing)
   */
  sendTestNotification: async (data: {
    type: NotificationType;
    title: string;
    message: string;
  }): Promise<Notification> => {
    const response = await apiClient.post('/notifications/test/', data);
    return response.data;
  },

  /**
   * Get notification templates
   */
  getTemplates: async (): Promise<
    Array<{
      id: string;
      type: NotificationType;
      template: string;
      variables: string[];
    }>
  > => {
    const response = await apiClient.get('/notifications/templates/');
    return response.data;
  },

  /**
   * WebSocket connection for real-time notifications
   * Returns WebSocket URL with auth token
   */
  getWebSocketURL: async (): Promise<{ ws_url: string; token: string }> => {
    const response = await apiClient.get('/notifications/ws-url/');
    return response.data;
  },

  /**
   * Snooze notification
   */
  snoozeNotification: async (
    id: string,
    snooze_until: string
  ): Promise<Notification> => {
    const response = await apiClient.post(`/notifications/${id}/snooze/`, {
      snooze_until,
    });
    return response.data;
  },

  /**
   * Archive notification
   */
  archiveNotification: async (id: string): Promise<Notification> => {
    const response = await apiClient.post(`/notifications/${id}/archive/`);
    return response.data;
  },

  /**
   * Get archived notifications
   */
  getArchivedNotifications: async (
    pagination?: PaginationConfig
  ): Promise<PaginatedResponse<Notification>> => {
    const params = new URLSearchParams();
    if (pagination?.page) params.set('page', pagination.page.toString());
    if (pagination?.pageSize) params.set('page_size', pagination.pageSize.toString());

    const queryString = params.toString() ? `?${params.toString()}` : '';
    const response = await apiClient.get(`/notifications/archived/${queryString}`);
    return response.data;
  },
};

export default notificationService;
