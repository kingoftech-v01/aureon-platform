/**
 * Analytics React Query hooks
 */

import { useQuery } from '@tanstack/react-query';
import { analyticsService } from '@services/analyticsService';

export const useDashboardStats = () => {
  return useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => analyticsService.getDashboard(),
    staleTime: 5 * 60 * 1000,
  });
};

export const useRevenue = () => {
  return useQuery({
    queryKey: ['revenue'],
    queryFn: () => analyticsService.getRevenue(),
    staleTime: 5 * 60 * 1000,
  });
};

export const useClientMetrics = () => {
  return useQuery({
    queryKey: ['client-metrics'],
    queryFn: () => analyticsService.getClientMetrics(),
    staleTime: 5 * 60 * 1000,
  });
};

export const useActivity = () => {
  return useQuery({
    queryKey: ['activity'],
    queryFn: () => analyticsService.getActivity(),
    staleTime: 2 * 60 * 1000,
  });
};
