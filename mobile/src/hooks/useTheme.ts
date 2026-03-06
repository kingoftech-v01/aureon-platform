/**
 * useTheme - Dark mode theme hook
 *
 * Provides the current color scheme based on the app store's theme setting
 * and the system color scheme. Returns themed colors, isDark flag, and
 * helpers to toggle or set the theme mode.
 */

import { useCallback } from 'react';
import { useColorScheme } from 'react-native';
import { useAppStore } from '@store/index';
import { colors as lightColors } from '@theme/colors';

// Dark theme color overrides
const darkColors = {
  ...lightColors,
  background: {
    primary: '#0f172a',
    secondary: '#1e293b',
    tertiary: '#334155',
    gradient: ['#0f172a', '#001933'] as const,
    gradientAccent: ['#004a99', '#00ae9a'] as const,
  },
  text: {
    primary: '#f1f5f9',
    secondary: '#94a3b8',
    muted: '#64748b',
    inverse: '#0f172a',
    link: '#3396ff',
  },
  glass: {
    ...lightColors.glass,
    bg: 'rgba(30, 41, 59, 0.75)',
    bgStrong: 'rgba(30, 41, 59, 0.9)',
    bgDark: 'rgba(0, 0, 0, 0.4)',
    border: 'rgba(148, 163, 184, 0.15)',
    borderSubtle: 'rgba(148, 163, 184, 0.1)',
    borderDark: 'rgba(148, 163, 184, 0.08)',
    shadow: 'rgba(0, 0, 0, 0.25)',
  },
};

export const useTheme = () => {
  const { theme, setTheme } = useAppStore();
  const systemScheme = useColorScheme();

  const isDark =
    theme === 'dark' || (theme === 'system' && systemScheme === 'dark');
  const currentColors = isDark ? darkColors : lightColors;

  const toggleTheme = useCallback(() => {
    setTheme(isDark ? 'light' : 'dark');
  }, [isDark, setTheme]);

  return { isDark, colors: currentColors, theme, setTheme, toggleTheme };
};
