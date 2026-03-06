/**
 * Notification Services
 * - pushNotificationService: Handles push notification registration and handling
 * - notificationService: API-backed in-app notification management
 */
import { Platform, Alert } from 'react-native';
import api from './api';

export interface PushNotification {
  id: string;
  title: string;
  body: string;
  data?: Record<string, any>;
  type?: string;
}

export const pushNotificationService = {
  /**
   * Request push notification permissions
   */
  requestPermissions: async (): Promise<boolean> => {
    try {
      // In a real implementation, this would use @react-native-firebase/messaging
      // or expo-notifications. For now, return true as a placeholder.
      if (Platform.OS === 'ios') {
        // iOS requires explicit permission request
        // const authStatus = await messaging().requestPermission();
        // return authStatus === messaging.AuthorizationStatus.AUTHORIZED;
      }
      return true;
    } catch {
      return false;
    }
  },

  /**
   * Get the device push token
   */
  getDeviceToken: async (): Promise<string | null> => {
    try {
      // const token = await messaging().getToken();
      // return token;
      return null; // Placeholder until Firebase is configured
    } catch {
      return null;
    }
  },

  /**
   * Register device token with backend
   */
  registerToken: async (token: string): Promise<void> => {
    try {
      await api.post('/notifications/register-device/', {
        token,
        platform: Platform.OS,
        device_name: Platform.OS === 'ios' ? 'iPhone' : 'Android',
      });
    } catch (error) {
      console.warn('Failed to register push token:', error);
    }
  },

  /**
   * Handle incoming notification when app is in foreground
   */
  handleForegroundNotification: (notification: PushNotification): void => {
    Alert.alert(
      notification.title,
      notification.body,
      [
        { text: 'Dismiss', style: 'cancel' },
        { text: 'View', onPress: () => pushNotificationService.handleNotificationPress(notification) },
      ]
    );
  },

  /**
   * Handle notification tap - navigate to relevant screen
   */
  handleNotificationPress: (notification: PushNotification): void => {
    const { type, data } = notification;
    // Navigation would be handled by passing to a navigation ref
    // For now, log the action
    console.log('Notification pressed:', type, data);
  },

  /**
   * Set up notification listeners
   */
  setupListeners: () => {
    // In a real implementation:
    // messaging().onMessage(async (remoteMessage) => { ... });
    // messaging().onNotificationOpenedApp((remoteMessage) => { ... });
    // messaging().getInitialNotification().then((remoteMessage) => { ... });
  },

  /**
   * Get notification badge count
   */
  getBadgeCount: async (): Promise<number> => {
    return 0; // Placeholder
  },

  /**
   * Clear badge count
   */
  clearBadgeCount: async (): Promise<void> => {
    // PushNotificationIOS.setApplicationIconBadgeNumber(0);
  },
};

/**
 * API-backed notification service for in-app notifications
 */
export const notificationService = {
  getNotifications: async (page = 1) => {
    const response = await api.get('/notifications/', { params: { page } });
    return response.data;
  },

  getUnreadCount: async () => {
    const response = await api.get('/notifications/unread_count/');
    return response.data;
  },

  markAsRead: async (id: string) => {
    const response = await api.post(`/notifications/${id}/mark_read/`);
    return response.data;
  },

  markAllAsRead: async () => {
    const response = await api.post('/notifications/mark_all_read/');
    return response.data;
  },
};

export default notificationService;
