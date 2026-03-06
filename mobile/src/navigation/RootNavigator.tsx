/**
 * Root Navigator - Conditional auth/main navigation
 */

import React, { useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { useAuthStore } from '@store/authStore';
import AuthStack from './AuthStack';
import MainTabNavigator from './MainTabNavigator';
import SplashScreen from '@screens/auth/SplashScreen';

const RootNavigator: React.FC = () => {
  const { isAuthenticated, isHydrated, hydrate } = useAuthStore();

  useEffect(() => {
    hydrate();
  }, []);

  if (!isHydrated) {
    return <SplashScreen />;
  }

  return (
    <NavigationContainer>
      {isAuthenticated ? <MainTabNavigator /> : <AuthStack />}
    </NavigationContainer>
  );
};

export default RootNavigator;
