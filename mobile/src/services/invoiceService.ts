/**
 * Invoice API Service
 */

import apiClient, { buildQueryParams } from './api';
import type {
  Invoice,
  InvoiceFormData,
  PaginatedResponse,
  PaginationConfig,
  FilterConfig,
} from '@/types';

export const invoiceService = {
  getInvoices: async (
    pagination: PaginationConfig = { page: 1, page_size: 20 },
    filters?: FilterConfig,
  ): Promise<PaginatedResponse<Invoice>> => {
    const params = buildQueryParams({ ...pagination, ...filters });
    const response = await apiClient.get(`/invoices/${params}`);
    return response.data;
  },

  getInvoice: async (id: string): Promise<Invoice> => {
    const response = await apiClient.get(`/invoices/${id}/`);
    return response.data;
  },

  createInvoice: async (data: InvoiceFormData): Promise<Invoice> => {
    const response = await apiClient.post('/invoices/', data);
    return response.data;
  },

  updateInvoice: async (id: string, data: Partial<InvoiceFormData>): Promise<Invoice> => {
    const response = await apiClient.patch(`/invoices/${id}/`, data);
    return response.data;
  },

  deleteInvoice: async (id: string): Promise<void> => {
    await apiClient.delete(`/invoices/${id}/`);
  },

  sendInvoice: async (id: string): Promise<void> => {
    await apiClient.post(`/invoices/${id}/send/`);
  },

  markPaid: async (
    id: string,
    data: { payment_amount: number; payment_method: string; payment_reference?: string },
  ): Promise<Invoice> => {
    const response = await apiClient.post(`/invoices/${id}/mark_paid/`, data);
    return response.data;
  },

  getInvoiceStats: async (): Promise<any> => {
    const response = await apiClient.get('/invoices/stats/');
    return response.data;
  },
};
