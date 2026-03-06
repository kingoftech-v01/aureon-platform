// API Configuration
// In development, point to your local Django server
// For Android emulator, use 10.0.2.2 instead of localhost
// For iOS simulator, localhost works fine
import { Platform } from 'react-native';

const DEV_API_HOST = Platform.select({
  android: 'http://10.0.2.2:8000',
  ios: 'http://localhost:8000',
  default: 'http://localhost:8000',
});

const PROD_API_HOST = 'https://api.aureon.finance';

export const API_CONFIG = {
  baseURL: __DEV__ ? `${DEV_API_HOST}/api` : `${PROD_API_HOST}/api`,
  timeout: 30000,
  retryAttempts: 3,
};
