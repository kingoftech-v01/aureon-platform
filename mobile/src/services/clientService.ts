/**
 * Client API Service
 */

import apiClient, { buildQueryParams } from './api';
import type {
  Client,
  ClientFormData,
  PaginatedResponse,
  PaginationConfig,
  FilterConfig,
} from '@/types';

export const clientService = {
  getClients: async (
    pagination: PaginationConfig = { page: 1, page_size: 20 },
    filters?: FilterConfig,
  ): Promise<PaginatedResponse<Client>> => {
    const params = buildQueryParams({ ...pagination, ...filters });
    const response = await apiClient.get(`/clients/${params}`);
    return response.data;
  },

  getClient: async (id: string): Promise<Client> => {
    const response = await apiClient.get(`/clients/${id}/`);
    return response.data;
  },

  createClient: async (data: ClientFormData): Promise<Client> => {
    const response = await apiClient.post('/clients/', data);
    return response.data;
  },

  updateClient: async (id: string, data: Partial<ClientFormData>): Promise<Client> => {
    const response = await apiClient.patch(`/clients/${id}/`, data);
    return response.data;
  },

  deleteClient: async (id: string): Promise<void> => {
    await apiClient.delete(`/clients/${id}/`);
  },

  getClientStats: async (): Promise<any> => {
    const response = await apiClient.get('/clients/stats/');
    return response.data;
  },
};
