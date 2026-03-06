/**
 * Main Tab Navigator with custom GlassTabBar
 */

import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { GlassTabBar } from '@components/glass';

// Screens
import DashboardScreen from '@screens/dashboard/DashboardScreen';
import ClientListScreen from '@screens/clients/ClientListScreen';
import ClientDetailScreen from '@screens/clients/ClientDetailScreen';
import ClientCreateScreen from '@screens/clients/ClientCreateScreen';
import InvoiceListScreen from '@screens/invoices/InvoiceListScreen';
import InvoiceDetailScreen from '@screens/invoices/InvoiceDetailScreen';
import InvoiceCreateScreen from '@screens/invoices/InvoiceCreateScreen';
import ContractListScreen from '@screens/contracts/ContractListScreen';
import ContractDetailScreen from '@screens/contracts/ContractDetailScreen';
import AnalyticsScreen from '@screens/analytics/AnalyticsScreen';
import SettingsScreen from '@screens/settings/SettingsScreen';
import PaymentListScreen from '@screens/payments/PaymentListScreen';
import ClientEditScreen from '@screens/clients/ClientEditScreen';
import ContractCreateScreen from '@screens/contracts/ContractCreateScreen';
import ProfileScreen from '@screens/settings/ProfileScreen';
import PaymentDetailScreen from '@screens/payments/PaymentDetailScreen';

import type { MainTabParamList } from '@types/navigation';

// Stack navigators for each tab
const DashboardStack = createNativeStackNavigator();
const ClientStack = createNativeStackNavigator();
const InvoiceStack = createNativeStackNavigator();
const AnalyticsStack = createNativeStackNavigator();
const MoreStack = createNativeStackNavigator();

const DashboardStackScreen = () => (
  <DashboardStack.Navigator screenOptions={{ headerShown: false }}>
    <DashboardStack.Screen name="Dashboard" component={DashboardScreen} />
  </DashboardStack.Navigator>
);

const ClientStackScreen = () => (
  <ClientStack.Navigator screenOptions={{ headerShown: false }}>
    <ClientStack.Screen name="ClientList" component={ClientListScreen} />
    <ClientStack.Screen name="ClientDetail" component={ClientDetailScreen} />
    <ClientStack.Screen name="ClientCreate" component={ClientCreateScreen} />
    <ClientStack.Screen name="ClientEdit" component={ClientEditScreen} />
  </ClientStack.Navigator>
);

const InvoiceStackScreen = () => (
  <InvoiceStack.Navigator screenOptions={{ headerShown: false }}>
    <InvoiceStack.Screen name="InvoiceList" component={InvoiceListScreen} />
    <InvoiceStack.Screen name="InvoiceDetail" component={InvoiceDetailScreen} />
    <InvoiceStack.Screen name="InvoiceCreate" component={InvoiceCreateScreen} />
    <InvoiceStack.Screen name="ContractList" component={ContractListScreen} />
    <InvoiceStack.Screen name="ContractDetail" component={ContractDetailScreen} />
    <InvoiceStack.Screen name="ContractCreate" component={ContractCreateScreen} />
  </InvoiceStack.Navigator>
);

const AnalyticsStackScreen = () => (
  <AnalyticsStack.Navigator screenOptions={{ headerShown: false }}>
    <AnalyticsStack.Screen name="Analytics" component={AnalyticsScreen} />
  </AnalyticsStack.Navigator>
);

const MoreStackScreen = () => (
  <MoreStack.Navigator screenOptions={{ headerShown: false }}>
    <MoreStack.Screen name="Settings" component={SettingsScreen} />
    <MoreStack.Screen name="PaymentList" component={PaymentListScreen} />
    <MoreStack.Screen name="ContractListAll" component={ContractListScreen} />
    <MoreStack.Screen name="ContractDetailAll" component={ContractDetailScreen} />
    <MoreStack.Screen name="Profile" component={ProfileScreen} />
    <MoreStack.Screen name="PaymentDetail" component={PaymentDetailScreen} />
  </MoreStack.Navigator>
);

const Tab = createBottomTabNavigator<MainTabParamList>();

const MainTabNavigator: React.FC = () => {
  return (
    <Tab.Navigator
      tabBar={(props) => <GlassTabBar {...props} />}
      screenOptions={{ headerShown: false }}
    >
      <Tab.Screen
        name="DashboardTab"
        component={DashboardStackScreen}
        options={{ tabBarLabel: 'Home' }}
      />
      <Tab.Screen
        name="ClientsTab"
        component={ClientStackScreen}
        options={{ tabBarLabel: 'Clients' }}
      />
      <Tab.Screen
        name="InvoicesTab"
        component={InvoiceStackScreen}
        options={{ tabBarLabel: 'Invoices' }}
      />
      <Tab.Screen
        name="AnalyticsTab"
        component={AnalyticsStackScreen}
        options={{ tabBarLabel: 'Analytics' }}
      />
      <Tab.Screen
        name="MoreTab"
        component={MoreStackScreen}
        options={{ tabBarLabel: 'More' }}
      />
    </Tab.Navigator>
  );
};

export default MainTabNavigator;
