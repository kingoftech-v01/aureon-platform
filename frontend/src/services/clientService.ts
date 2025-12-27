/**
 * Client/CRM API Service
 * Aureon by Rhematek Solutions
 */

import apiClient, { buildQueryParams } from './api';
import type {
  Client,
  ClientFormData,
  ClientNote,
  PaginatedResponse,
  PaginationConfig,
  FilterConfig,
  SortConfig,
} from '@/types';

export const clientService = {
  /**
   * Get all clients with pagination and filters
   */
  getClients: async (
    pagination?: PaginationConfig,
    filters?: FilterConfig,
    sort?: SortConfig
  ): Promise<PaginatedResponse<Client>> => {
    const params = {
      page: pagination?.page,
      page_size: pagination?.page_size,
      ordering: sort ? `${sort.direction === 'desc' ? '-' : ''}${sort.field}` : undefined,
      ...filters,
    };

    const queryString = buildQueryParams(params);
    const response = await apiClient.get(`/clients/${queryString}`);
    return response.data;
  },

  /**
   * Get single client by ID
   */
  getClient: async (id: string): Promise<Client> => {
    const response = await apiClient.get(`/clients/${id}/`);
    return response.data;
  },

  /**
   * Create new client
   */
  createClient: async (data: ClientFormData): Promise<Client> => {
    const response = await apiClient.post('/clients/', data);
    return response.data;
  },

  /**
   * Update client
   */
  updateClient: async (id: string, data: Partial<ClientFormData>): Promise<Client> => {
    const response = await apiClient.patch(`/clients/${id}/`, data);
    return response.data;
  },

  /**
   * Delete client
   */
  deleteClient: async (id: string): Promise<void> => {
    await apiClient.delete(`/clients/${id}/`);
  },

  /**
   * Get client notes
   */
  getClientNotes: async (clientId: string): Promise<ClientNote[]> => {
    const response = await apiClient.get(`/clients/${clientId}/notes/`);
    return response.data;
  },

  /**
   * Add note to client
   */
  addClientNote: async (clientId: string, content: string): Promise<ClientNote> => {
    const response = await apiClient.post(`/clients/${clientId}/notes/`, { content });
    return response.data;
  },

  /**
   * Update client note
   */
  updateClientNote: async (
    clientId: string,
    noteId: string,
    content: string
  ): Promise<ClientNote> => {
    const response = await apiClient.patch(`/clients/${clientId}/notes/${noteId}/`, {
      content,
    });
    return response.data;
  },

  /**
   * Delete client note
   */
  deleteClientNote: async (clientId: string, noteId: string): Promise<void> => {
    await apiClient.delete(`/clients/${clientId}/notes/${noteId}/`);
  },

  /**
   * Enable client portal access
   */
  enablePortalAccess: async (clientId: string): Promise<{ portal_url: string }> => {
    const response = await apiClient.post(`/clients/${clientId}/enable-portal/`);
    return response.data;
  },

  /**
   * Disable client portal access
   */
  disablePortalAccess: async (clientId: string): Promise<void> => {
    await apiClient.post(`/clients/${clientId}/disable-portal/`);
  },

  /**
   * Search clients
   */
  searchClients: async (query: string): Promise<Client[]> => {
    const response = await apiClient.get(`/clients/?search=${encodeURIComponent(query)}`);
    return response.data.results;
  },

  /**
   * Get client statistics
   */
  getClientStats: async (clientId: string): Promise<{
    total_revenue: number;
    total_contracts: number;
    total_invoices: number;
    total_payments: number;
    average_invoice_value: number;
  }> => {
    const response = await apiClient.get(`/clients/${clientId}/stats/`);
    return response.data;
  },
};

export default clientService;
