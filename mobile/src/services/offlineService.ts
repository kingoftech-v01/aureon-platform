/**
 * Offline Support Service
 * Persists React Query cache to AsyncStorage for offline access
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';

const CACHE_KEY = 'aureon_query_cache';
const CACHE_EXPIRY_MS = 24 * 60 * 60 * 1000; // 24 hours

export const offlineService = {
  /**
   * Save query cache to AsyncStorage
   */
  persistCache: async (queryClient: any) => {
    try {
      const cache = queryClient.getQueryCache().getAll();
      const serializable = cache
        .filter((query: any) => query.state.data !== undefined)
        .map((query: any) => ({
          queryKey: query.queryKey,
          data: query.state.data,
          dataUpdatedAt: query.state.dataUpdatedAt,
        }));
      await AsyncStorage.setItem(CACHE_KEY, JSON.stringify({
        timestamp: Date.now(),
        queries: serializable,
      }));
    } catch (error) {
      console.warn('Failed to persist query cache:', error);
    }
  },

  /**
   * Restore query cache from AsyncStorage
   */
  restoreCache: async (queryClient: any) => {
    try {
      const cached = await AsyncStorage.getItem(CACHE_KEY);
      if (!cached) return false;

      const { timestamp, queries } = JSON.parse(cached);
      if (Date.now() - timestamp > CACHE_EXPIRY_MS) {
        await AsyncStorage.removeItem(CACHE_KEY);
        return false;
      }

      for (const query of queries) {
        queryClient.setQueryData(query.queryKey, query.data);
      }
      return true;
    } catch (error) {
      console.warn('Failed to restore query cache:', error);
      return false;
    }
  },

  /**
   * Check network connectivity
   */
  isOnline: async (): Promise<boolean> => {
    try {
      const state = await NetInfo.fetch();
      return !!state.isConnected;
    } catch {
      return true; // Assume online if check fails
    }
  },

  /**
   * Subscribe to network changes
   */
  onNetworkChange: (callback: (isConnected: boolean) => void) => {
    return NetInfo.addEventListener((state) => {
      callback(!!state.isConnected);
    });
  },

  /**
   * Clear cached data
   */
  clearCache: async () => {
    await AsyncStorage.removeItem(CACHE_KEY);
  },
};
