/**
 * Payment API Service
 */

import apiClient, { buildQueryParams } from './api';
import type {
  Payment,
  PaginatedResponse,
  PaginationConfig,
  FilterConfig,
} from '@/types';

export const paymentService = {
  getPayments: async (
    pagination: PaginationConfig = { page: 1, page_size: 20 },
    filters?: FilterConfig,
  ): Promise<PaginatedResponse<Payment>> => {
    const params = buildQueryParams({ ...pagination, ...filters });
    const response = await apiClient.get(`/payments/${params}`);
    return response.data;
  },

  getPayment: async (id: string): Promise<Payment> => {
    const response = await apiClient.get(`/payments/${id}/`);
    return response.data;
  },

  refundPayment: async (id: string, amount: number, reason?: string): Promise<Payment> => {
    const response = await apiClient.post(`/payments/${id}/refund/`, {
      refund_amount: amount,
      reason,
    });
    return response.data;
  },

  getPaymentStats: async (): Promise<any> => {
    const response = await apiClient.get('/payments/stats/');
    return response.data;
  },
};
