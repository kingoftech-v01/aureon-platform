/**
 * Contract Management API Service
 * Aureon by Rhematek Solutions
 */

import apiClient from './api';
import type {
  Contract,
  ContractFormData,
  ContractMilestone,
  ContractTemplate,
  ContractStatus,
  PaginatedResponse,
  PaginationConfig,
  FilterConfig,
  SortConfig,
} from '@/types';

/**
 * Build query string from params
 */
const buildQueryParams = (params: Record<string, any>): string => {
  const filteredParams = Object.entries(params)
    .filter(([_, value]) => value !== undefined && value !== null && value !== '')
    .reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {});

  const queryString = new URLSearchParams(filteredParams).toString();
  return queryString ? `?${queryString}` : '';
};

export const contractService = {
  /**
   * Get contracts with pagination, filtering, and sorting
   */
  getContracts: async (
    pagination?: PaginationConfig,
    filters?: FilterConfig,
    sort?: SortConfig
  ): Promise<PaginatedResponse<Contract>> => {
    const params = {
      page: pagination?.page,
      page_size: pagination?.pageSize,
      ordering: sort ? `${sort.direction === 'desc' ? '-' : ''}${sort.field}` : undefined,
      ...filters,
    };

    const queryString = buildQueryParams(params);
    const response = await apiClient.get(`/contracts/${queryString}`);
    return response.data;
  },

  /**
   * Get single contract by ID
   */
  getContract: async (id: string): Promise<Contract> => {
    const response = await apiClient.get(`/contracts/${id}/`);
    return response.data;
  },

  /**
   * Create new contract
   */
  createContract: async (data: ContractFormData): Promise<Contract> => {
    const response = await apiClient.post('/contracts/', data);
    return response.data;
  },

  /**
   * Update existing contract
   */
  updateContract: async (id: string, data: Partial<ContractFormData>): Promise<Contract> => {
    const response = await apiClient.patch(`/contracts/${id}/`, data);
    return response.data;
  },

  /**
   * Delete contract
   */
  deleteContract: async (id: string): Promise<void> => {
    await apiClient.delete(`/contracts/${id}/`);
  },

  /**
   * Sign contract (client or vendor)
   */
  signContract: async (
    id: string,
    signatureData: {
      signature: string;
      signed_by: string;
      ip_address?: string;
    }
  ): Promise<Contract> => {
    const response = await apiClient.post(`/contracts/${id}/sign/`, signatureData);
    return response.data;
  },

  /**
   * Update contract status
   */
  updateStatus: async (id: string, status: ContractStatus): Promise<Contract> => {
    const response = await apiClient.post(`/contracts/${id}/update_status/`, { status });
    return response.data;
  },

  /**
   * Get contract milestones
   */
  getMilestones: async (contractId: string): Promise<ContractMilestone[]> => {
    const response = await apiClient.get(`/contracts/${contractId}/milestones/`);
    return response.data;
  },

  /**
   * Create milestone
   */
  createMilestone: async (
    contractId: string,
    milestoneData: Partial<ContractMilestone>
  ): Promise<ContractMilestone> => {
    const response = await apiClient.post(`/contracts/${contractId}/milestones/`, milestoneData);
    return response.data;
  },

  /**
   * Update milestone
   */
  updateMilestone: async (
    contractId: string,
    milestoneId: string,
    data: Partial<ContractMilestone>
  ): Promise<ContractMilestone> => {
    const response = await apiClient.patch(
      `/contracts/${contractId}/milestones/${milestoneId}/`,
      data
    );
    return response.data;
  },

  /**
   * Complete milestone
   */
  completeMilestone: async (contractId: string, milestoneId: string): Promise<ContractMilestone> => {
    const response = await apiClient.post(
      `/contracts/${contractId}/milestones/${milestoneId}/complete/`
    );
    return response.data;
  },

  /**
   * Get contract templates
   */
  getTemplates: async (): Promise<ContractTemplate[]> => {
    const response = await apiClient.get('/contracts/templates/');
    return response.data;
  },

  /**
   * Get template by ID
   */
  getTemplate: async (id: string): Promise<ContractTemplate> => {
    const response = await apiClient.get(`/contracts/templates/${id}/`);
    return response.data;
  },

  /**
   * Create contract from template
   */
  createFromTemplate: async (
    templateId: string,
    data: {
      client_id: string;
      variables: Record<string, any>;
    }
  ): Promise<Contract> => {
    const response = await apiClient.post(`/contracts/templates/${templateId}/create/`, data);
    return response.data;
  },

  /**
   * Generate contract PDF
   */
  generatePDF: async (id: string): Promise<Blob> => {
    const response = await apiClient.get(`/contracts/${id}/pdf/`, {
      responseType: 'blob',
    });
    return response.data;
  },

  /**
   * Send contract for signature
   */
  sendForSignature: async (
    id: string,
    data: {
      recipient_email: string;
      message?: string;
    }
  ): Promise<void> => {
    await apiClient.post(`/contracts/${id}/send/`, data);
  },

  /**
   * Get contract statistics
   */
  getStats: async (): Promise<{
    total: number;
    active: number;
    completed: number;
    pending_signature: number;
    total_value: number;
  }> => {
    const response = await apiClient.get('/contracts/stats/');
    return response.data;
  },

  /**
   * Search contracts
   */
  searchContracts: async (query: string): Promise<Contract[]> => {
    const response = await apiClient.get(`/contracts/search/?q=${encodeURIComponent(query)}`);
    return response.data;
  },

  /**
   * Duplicate contract
   */
  duplicateContract: async (id: string): Promise<Contract> => {
    const response = await apiClient.post(`/contracts/${id}/duplicate/`);
    return response.data;
  },

  /**
   * Archive contract
   */
  archiveContract: async (id: string): Promise<Contract> => {
    const response = await apiClient.post(`/contracts/${id}/archive/`);
    return response.data;
  },

  /**
   * Unarchive contract
   */
  unarchiveContract: async (id: string): Promise<Contract> => {
    const response = await apiClient.post(`/contracts/${id}/unarchive/`);
    return response.data;
  },
};

export default contractService;
