/**
 * Contract React Query hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { contractService } from '@services/contractService';
import type { ContractFormData, PaginationConfig, FilterConfig } from '@/types';

export const useContracts = (
  pagination?: PaginationConfig,
  filters?: FilterConfig,
) => {
  return useQuery({
    queryKey: ['contracts', pagination, filters],
    queryFn: () =>
      contractService.getContracts(
        pagination || { page: 1, page_size: 20 },
        filters,
      ),
  });
};

export const useContract = (id: string) => {
  return useQuery({
    queryKey: ['contract', id],
    queryFn: () => contractService.getContract(id),
    enabled: !!id,
  });
};

export const useCreateContract = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ContractFormData) => contractService.createContract(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] });
    },
  });
};

export const useSignContract = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, party, signature }: { id: string; party: 'client' | 'company'; signature: string }) =>
      contractService.signContract(id, party, signature),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] });
      queryClient.invalidateQueries({ queryKey: ['contract', variables.id] });
    },
  });
};

export const useCompleteMilestone = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (milestoneId: string) =>
      contractService.completeMilestone(milestoneId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['contracts'] });
    },
  });
};
