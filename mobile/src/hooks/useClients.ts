/**
 * Client React Query hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { clientService } from '@services/clientService';
import type { ClientFormData, FilterConfig, PaginationConfig } from '@/types';

export const useClients = (
  pagination?: PaginationConfig,
  filters?: FilterConfig,
) => {
  return useQuery({
    queryKey: ['clients', pagination, filters],
    queryFn: () =>
      clientService.getClients(
        pagination || { page: 1, page_size: 20 },
        filters,
      ),
  });
};

export const useClient = (id: string) => {
  return useQuery({
    queryKey: ['client', id],
    queryFn: () => clientService.getClient(id),
    enabled: !!id,
  });
};

export const useCreateClient = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ClientFormData) => clientService.createClient(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
  });
};

export const useUpdateClient = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ClientFormData> }) =>
      clientService.updateClient(id, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
      queryClient.invalidateQueries({ queryKey: ['client', variables.id] });
    },
  });
};

export const useDeleteClient = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => clientService.deleteClient(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] });
    },
  });
};
