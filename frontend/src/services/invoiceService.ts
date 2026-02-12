/**
 * Invoice Management API Service
 * Aureon by Rhematek Solutions
 */

import apiClient, { buildQueryParams } from './api';
import type {
  Invoice,
  InvoiceFormData,
  InvoiceItem,
  InvoiceStatus,
  RecurringInvoice,
  PaginatedResponse,
  PaginationConfig,
  FilterConfig,
  SortConfig,
} from '@/types';

export const invoiceService = {
  /**
   * Get invoices with pagination, filtering, and sorting
   */
  getInvoices: async (
    pagination?: PaginationConfig,
    filters?: FilterConfig,
    sort?: SortConfig
  ): Promise<PaginatedResponse<Invoice>> => {
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
    const response = await apiClient.get(`/invoices/${queryString}`);
    return response.data;
  },

  /**
   * Get single invoice by ID
   */
  getInvoice: async (id: string): Promise<Invoice> => {
    const response = await apiClient.get(`/invoices/${id}/`);
    return response.data;
  },

  /**
   * Create new invoice
   */
  createInvoice: async (data: InvoiceFormData): Promise<Invoice> => {
    const response = await apiClient.post('/invoices/', data);
    return response.data;
  },

  /**
   * Update existing invoice
   */
  updateInvoice: async (id: string, data: Partial<InvoiceFormData>): Promise<Invoice> => {
    const response = await apiClient.patch(`/invoices/${id}/`, data);
    return response.data;
  },

  /**
   * Delete invoice
   */
  deleteInvoice: async (id: string): Promise<void> => {
    await apiClient.delete(`/invoices/${id}/`);
  },

  /**
   * Update invoice status
   */
  updateStatus: async (id: string, status: InvoiceStatus): Promise<Invoice> => {
    const response = await apiClient.post(`/invoices/${id}/update_status/`, { status });
    return response.data;
  },

  /**
   * Send invoice to client via email
   */
  sendInvoice: async (
    id: string,
    data?: {
      recipient_email?: string;
      cc_emails?: string[];
      message?: string;
    }
  ): Promise<void> => {
    await apiClient.post(`/invoices/${id}/send/`, data || {});
  },

  /**
   * Mark invoice as paid
   */
  markAsPaid: async (
    id: string,
    data: {
      payment_date?: string;
      payment_method?: string;
      transaction_id?: string;
      notes?: string;
    }
  ): Promise<Invoice> => {
    const response = await apiClient.post(`/invoices/${id}/mark_paid/`, data);
    return response.data;
  },

  /**
   * Mark invoice as void
   */
  markAsVoid: async (id: string, reason?: string): Promise<Invoice> => {
    const response = await apiClient.post(`/invoices/${id}/void/`, { reason });
    return response.data;
  },

  /**
   * Generate invoice PDF
   */
  generatePDF: async (id: string): Promise<Blob> => {
    const response = await apiClient.get(`/invoices/${id}/pdf/`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Download invoice PDF
   */
  downloadPDF: async (id: string, filename?: string): Promise<void> => {
    const blob = await invoiceService.generatePDF(id);
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `invoice-${id}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  },

  /**
   * Preview invoice (without saving)
   */
  previewInvoice: async (data: InvoiceFormData): Promise<Blob> => {
    const response = await apiClient.post('/invoices/preview/', data, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Get invoice items
   */
  getItems: async (invoiceId: string): Promise<InvoiceItem[]> => {
    const response = await apiClient.get(`/invoices/${invoiceId}/items/`);
    return response.data;
  },

  /**
   * Add invoice item
   */
  addItem: async (invoiceId: string, item: Partial<InvoiceItem>): Promise<InvoiceItem> => {
    const response = await apiClient.post(`/invoices/${invoiceId}/items/`, item);
    return response.data;
  },

  /**
   * Update invoice item
   */
  updateItem: async (
    invoiceId: string,
    itemId: string,
    data: Partial<InvoiceItem>
  ): Promise<InvoiceItem> => {
    const response = await apiClient.patch(`/invoices/${invoiceId}/items/${itemId}/`, data);
    return response.data;
  },

  /**
   * Delete invoice item
   */
  deleteItem: async (invoiceId: string, itemId: string): Promise<void> => {
    await apiClient.delete(`/invoices/${invoiceId}/items/${itemId}/`);
  },

  /**
   * Get recurring invoices
   */
  getRecurringInvoices: async (): Promise<RecurringInvoice[]> => {
    const response = await apiClient.get('/invoices/recurring/');
    return response.data;
  },

  /**
   * Create recurring invoice
   */
  createRecurringInvoice: async (data: Partial<RecurringInvoice>): Promise<RecurringInvoice> => {
    const response = await apiClient.post('/invoices/recurring/', data);
    return response.data;
  },

  /**
   * Update recurring invoice
   */
  updateRecurringInvoice: async (
    id: string,
    data: Partial<RecurringInvoice>
  ): Promise<RecurringInvoice> => {
    const response = await apiClient.patch(`/invoices/recurring/${id}/`, data);
    return response.data;
  },

  /**
   * Pause recurring invoice
   */
  pauseRecurringInvoice: async (id: string): Promise<RecurringInvoice> => {
    const response = await apiClient.post(`/invoices/recurring/${id}/pause/`);
    return response.data;
  },

  /**
   * Resume recurring invoice
   */
  resumeRecurringInvoice: async (id: string): Promise<RecurringInvoice> => {
    const response = await apiClient.post(`/invoices/recurring/${id}/resume/`);
    return response.data;
  },

  /**
   * Cancel recurring invoice
   */
  cancelRecurringInvoice: async (id: string): Promise<RecurringInvoice> => {
    const response = await apiClient.post(`/invoices/recurring/${id}/cancel/`);
    return response.data;
  },

  /**
   * Get invoice statistics
   */
  getStats: async (): Promise<{
    total: number;
    paid: number;
    unpaid: number;
    overdue: number;
    total_amount: number;
    paid_amount: number;
    unpaid_amount: number;
  }> => {
    const response = await apiClient.get('/invoices/stats/');
    return response.data;
  },

  /**
   * Get overdue invoices
   */
  getOverdueInvoices: async (): Promise<Invoice[]> => {
    const response = await apiClient.get('/invoices/overdue/');
    return response.data;
  },

  /**
   * Send payment reminder
   */
  sendReminder: async (id: string, message?: string): Promise<void> => {
    await apiClient.post(`/invoices/${id}/send_reminder/`, { message });
  },

  /**
   * Duplicate invoice
   */
  duplicateInvoice: async (id: string): Promise<Invoice> => {
    const response = await apiClient.post(`/invoices/${id}/duplicate/`);
    return response.data;
  },

  /**
   * Apply discount to invoice
   */
  applyDiscount: async (
    id: string,
    discount: {
      type: 'percentage' | 'fixed';
      value: number;
      reason?: string;
    }
  ): Promise<Invoice> => {
    const response = await apiClient.post(`/invoices/${id}/apply_discount/`, discount);
    return response.data;
  },

  /**
   * Apply tax to invoice
   */
  applyTax: async (
    id: string,
    tax: {
      name: string;
      rate: number;
      type?: 'vat' | 'gst' | 'sales_tax';
    }
  ): Promise<Invoice> => {
    const response = await apiClient.post(`/invoices/${id}/apply_tax/`, tax);
    return response.data;
  },

  /**
   * Search invoices
   */
  searchInvoices: async (query: string): Promise<Invoice[]> => {
    const response = await apiClient.get(`/invoices/search/?q=${encodeURIComponent(query)}`);
    return response.data;
  },

  /**
   * Export invoices to CSV
   */
  exportToCSV: async (filters?: FilterConfig): Promise<Blob> => {
    const queryString = buildQueryParams(filters || {});
    const response = await apiClient.get(`/invoices/export/csv/${queryString}`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Get payment link for invoice
   */
  getPaymentLink: async (id: string): Promise<{ payment_url: string }> => {
    const response = await apiClient.get(`/invoices/${id}/payment_link/`);
    return response.data;
  },
};

export default invoiceService;
