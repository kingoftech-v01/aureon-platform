/**
 * Analytics API Service
 */

import apiClient from './api';
import type { DashboardStats, RevenueMetric, ActivityItem } from '@/types';

export const analyticsService = {
  getDashboard: async (): Promise<DashboardStats> => {
    const response = await apiClient.get('/analytics/dashboard/');
    return response.data;
  },

  getRevenue: async (): Promise<RevenueMetric[]> => {
    const response = await apiClient.get('/analytics/revenue/');
    return response.data;
  },

  getClientMetrics: async (): Promise<any[]> => {
    const response = await apiClient.get('/analytics/clients/');
    return response.data;
  },

  getActivity: async (): Promise<ActivityItem[]> => {
    const response = await apiClient.get('/analytics/activity/');
    return response.data;
  },
};
