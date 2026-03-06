/**
 * Contract API Service
 */

import apiClient, { buildQueryParams } from './api';
import type {
  Contract,
  ContractFormData,
  ContractMilestone,
  PaginatedResponse,
  PaginationConfig,
  FilterConfig,
} from '@/types';

export const contractService = {
  getContracts: async (
    pagination: PaginationConfig = { page: 1, page_size: 20 },
    filters?: FilterConfig,
  ): Promise<PaginatedResponse<Contract>> => {
    const params = buildQueryParams({ ...pagination, ...filters });
    const response = await apiClient.get(`/contracts/${params}`);
    return response.data;
  },

  getContract: async (id: string): Promise<Contract> => {
    const response = await apiClient.get(`/contracts/${id}/`);
    return response.data;
  },

  createContract: async (data: ContractFormData): Promise<Contract> => {
    const response = await apiClient.post('/contracts/', data);
    return response.data;
  },

  updateContract: async (id: string, data: Partial<ContractFormData>): Promise<Contract> => {
    const response = await apiClient.patch(`/contracts/${id}/`, data);
    return response.data;
  },

  deleteContract: async (id: string): Promise<void> => {
    await apiClient.delete(`/contracts/${id}/`);
  },

  signContract: async (id: string, party: 'client' | 'company', signature: string): Promise<Contract> => {
    const response = await apiClient.post(`/contracts/${id}/sign/`, { party, signature });
    return response.data;
  },

  getContractStats: async (): Promise<any> => {
    const response = await apiClient.get('/contracts/stats/');
    return response.data;
  },

  getMilestones: async (contractId: string): Promise<ContractMilestone[]> => {
    const response = await apiClient.get(`/contracts/${contractId}/milestones/`);
    return response.data;
  },

  completeMilestone: async (milestoneId: string): Promise<ContractMilestone> => {
    const response = await apiClient.post(`/milestones/${milestoneId}/mark_complete/`);
    return response.data;
  },
};
