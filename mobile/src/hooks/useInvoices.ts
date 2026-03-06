/**
 * Invoice React Query hooks
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { invoiceService } from '@services/invoiceService';
import type { InvoiceFormData, FilterConfig, PaginationConfig } from '@/types';

export const useInvoices = (
  pagination?: PaginationConfig,
  filters?: FilterConfig,
) => {
  return useQuery({
    queryKey: ['invoices', pagination, filters],
    queryFn: () =>
      invoiceService.getInvoices(
        pagination || { page: 1, page_size: 20 },
        filters,
      ),
  });
};

export const useInvoice = (id: string) => {
  return useQuery({
    queryKey: ['invoice', id],
    queryFn: () => invoiceService.getInvoice(id),
    enabled: !!id,
  });
};

export const useCreateInvoice = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: InvoiceFormData) => invoiceService.createInvoice(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    },
  });
};

export const useSendInvoice = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => invoiceService.sendInvoice(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
    },
  });
};

export const useMarkInvoicePaid = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      data: { payment_amount: number; payment_method: string };
    }) => invoiceService.markPaid(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invoices'] });
      queryClient.invalidateQueries({ queryKey: ['payments'] });
    },
  });
};
