/**
 * Payment React Query hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { paymentService } from '@services/paymentService';
import type { PaginationConfig, FilterConfig } from '@/types';

export const usePayments = (
  pagination?: PaginationConfig,
  filters?: FilterConfig,
) => {
  return useQuery({
    queryKey: ['payments', pagination, filters],
    queryFn: () =>
      paymentService.getPayments(
        pagination || { page: 1, page_size: 20 },
        filters,
      ),
  });
};

export const usePayment = (id: string) => {
  return useQuery({
    queryKey: ['payment', id],
    queryFn: () => paymentService.getPayment(id),
    enabled: !!id,
  });
};

export const useRefundPayment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, amount, reason }: { id: string; amount: number; reason?: string }) =>
      paymentService.refundPayment(id, amount, reason),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['payments'] });
      queryClient.invalidateQueries({ queryKey: ['payment', variables.id] });
    },
  });
};
