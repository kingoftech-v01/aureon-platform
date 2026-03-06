import React, { useState, useEffect, useRef } from 'react';
import { View, Text, Animated, StyleSheet } from 'react-native';
import NetInfo from '@react-native-community/netinfo';
import Icon from 'react-native-vector-icons/Ionicons';
import { colors } from '@theme/colors';
import { fontFamily, fontSize } from '@theme/typography';

const NetworkBanner: React.FC = () => {
  const [isOffline, setIsOffline] = useState(false);
  const [wasOffline, setWasOffline] = useState(false);
  const slideAnim = useRef(new Animated.Value(-60)).current;

  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener((state) => {
      const offline = !state.isConnected;
      setIsOffline(offline);
      if (!offline && wasOffline) {
        // Show "Back online" briefly
        setTimeout(() => setWasOffline(false), 3000);
      }
      if (offline) setWasOffline(true);
    });
    return () => unsubscribe();
  }, [wasOffline]);

  useEffect(() => {
    Animated.spring(slideAnim, {
      toValue: isOffline || (wasOffline && !isOffline) ? 0 : -60,
      useNativeDriver: true,
      tension: 80,
      friction: 12,
    }).start();
  }, [isOffline, wasOffline]);

  const isReconnected = !isOffline && wasOffline;

  return (
    <Animated.View style={[
      styles.container,
      { transform: [{ translateY: slideAnim }] },
      isReconnected ? styles.reconnected : styles.offline,
    ]}>
      <Icon
        name={isReconnected ? 'wifi-outline' : 'cloud-offline-outline'}
        size={18}
        color="white"
      />
      <Text style={styles.text}>
        {isReconnected ? 'Back online' : 'No internet connection'}
      </Text>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    paddingHorizontal: 16,
    gap: 8,
    zIndex: 999,
  },
  offline: { backgroundColor: colors.danger },
  reconnected: { backgroundColor: colors.success },
  text: {
    fontFamily: fontFamily.medium,
    fontSize: fontSize.sm,
    color: 'white',
  },
});

export default NetworkBanner;
