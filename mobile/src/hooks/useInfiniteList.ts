import { useState, useCallback } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';

interface UseInfiniteListOptions<T> {
  queryKey: string[];
  queryFn: (params: { page: number; page_size: number; [key: string]: any }) => Promise<{ count: number; results: T[] }>;
  pageSize?: number;
  filters?: Record<string, any>;
}

export function useInfiniteList<T>({ queryKey, queryFn, pageSize = 20, filters = {} }: UseInfiniteListOptions<T>) {
  const query = useInfiniteQuery({
    queryKey: [...queryKey, filters],
    queryFn: ({ pageParam = 1 }) => queryFn({ page: pageParam, page_size: pageSize, ...filters }),
    getNextPageParam: (lastPage, allPages) => {
      const totalLoaded = allPages.reduce((sum, p) => sum + p.results.length, 0);
      return totalLoaded < lastPage.count ? allPages.length + 1 : undefined;
    },
    initialPageParam: 1,
  });

  const data = query.data?.pages.flatMap(p => p.results) || [];
  const totalCount = query.data?.pages[0]?.count || 0;

  const onEndReached = useCallback(() => {
    if (query.hasNextPage && !query.isFetchingNextPage) {
      query.fetchNextPage();
    }
  }, [query]);

  return {
    data,
    totalCount,
    isLoading: query.isLoading,
    isRefreshing: query.isRefetching && !query.isFetchingNextPage,
    isFetchingMore: query.isFetchingNextPage,
    hasMore: !!query.hasNextPage,
    onEndReached,
    onRefresh: query.refetch,
    error: query.error,
  };
}
