/**
 * GlassTabBar - Custom glassmorphism bottom tab bar
 * Replaces default React Navigation tab bar
 */

import React from 'react';
import { View, Text, StyleSheet, Pressable, Platform } from 'react-native';
import { BlurView } from '@react-native-community/blur';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { BottomTabBarProps } from '@react-navigation/bottom-tabs';
import Icon from 'react-native-vector-icons/Ionicons';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';
import { glassPresets } from '@theme/glassmorphism';

const TAB_ICONS: Record<string, { active: string; inactive: string }> = {
  DashboardTab: { active: 'home', inactive: 'home-outline' },
  ClientsTab: { active: 'people', inactive: 'people-outline' },
  InvoicesTab: { active: 'receipt', inactive: 'receipt-outline' },
  AnalyticsTab: { active: 'bar-chart', inactive: 'bar-chart-outline' },
  MoreTab: { active: 'ellipsis-horizontal', inactive: 'ellipsis-horizontal-outline' },
};

const GlassTabBar: React.FC<BottomTabBarProps> = ({
  state,
  descriptors,
  navigation,
}) => {
  const insets = useSafeAreaInsets();
  const glass = glassPresets.tabBar;

  return (
    <View
      style={[
        styles.container,
        {
          paddingBottom: Math.max(insets.bottom, 8),
        },
        glass.shadow,
      ]}
    >
      <BlurView
        blurType={glass.blurType}
        blurAmount={glass.blurAmount}
        style={StyleSheet.absoluteFill}
        reducedTransparencyFallbackColor="white"
      />
      <View
        style={[
          StyleSheet.absoluteFill,
          { backgroundColor: glass.backgroundColor },
        ]}
      />
      <View
        style={[
          StyleSheet.absoluteFill,
          {
            borderTopWidth: glass.borderWidth,
            borderTopColor: glass.borderColor,
          },
        ]}
      />

      <View style={styles.tabs}>
        {state.routes.map((route, index) => {
          const { options } = descriptors[route.key];
          const label = options.tabBarLabel ?? options.title ?? route.name;
          const isFocused = state.index === index;
          const icons = TAB_ICONS[route.name] || {
            active: 'ellipse',
            inactive: 'ellipse-outline',
          };

          const onPress = () => {
            const event = navigation.emit({
              type: 'tabPress',
              target: route.key,
              canPreventDefault: true,
            });

            if (!isFocused && !event.defaultPrevented) {
              navigation.navigate(route.name);
            }
          };

          return (
            <Pressable
              key={route.key}
              onPress={onPress}
              style={styles.tab}
              hitSlop={4}
            >
              <Icon
                name={isFocused ? icons.active : icons.inactive}
                size={24}
                color={
                  isFocused ? colors.primary[500] : colors.text.muted
                }
              />
              <Text
                style={[
                  styles.label,
                  {
                    color: isFocused
                      ? colors.primary[500]
                      : colors.text.muted,
                    fontFamily: isFocused
                      ? fontFamily.semiBold
                      : fontFamily.regular,
                  },
                ]}
              >
                {typeof label === 'string' ? label : route.name}
              </Text>
            </Pressable>
          );
        })}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    overflow: 'hidden',
  },
  tabs: {
    flexDirection: 'row',
    paddingTop: 8,
    zIndex: 1,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 4,
  },
  label: {
    fontSize: fontSize.xs,
    marginTop: 2,
  },
});

export default GlassTabBar;
