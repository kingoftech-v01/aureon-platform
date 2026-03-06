/**
 * Aureon Mobile Color Tokens
 * Figma wireframe palette + Aureon brand colors
 */

export const colors = {
  // Figma wireframe palette (from Screen 23)
  figma: {
    darkText: '#424753',
    mutedText: '#8e99af',
    darkerElements: '#878e9f',
    lighterElements: '#cacfdb',
    borders: '#cdd2de',
  },

  // Aureon brand
  primary: {
    50: '#e6f2ff',
    100: '#cce5ff',
    200: '#99cbff',
    300: '#66b0ff',
    400: '#3396ff',
    500: '#007cff',
    600: '#0063cc',
    700: '#004a99',
    800: '#003166',
    900: '#001933',
  },

  accent: {
    50: '#e6fffa',
    100: '#ccfff5',
    200: '#99ffeb',
    300: '#66ffe1',
    400: '#33ffd7',
    500: '#00d9c0',
    600: '#00ae9a',
    700: '#008273',
    800: '#00574d',
    900: '#002b26',
  },

  // Semantic
  success: '#10b981',
  successLight: '#d1fae5',
  warning: '#f59e0b',
  warningLight: '#fef3c7',
  danger: '#ef4444',
  dangerLight: '#fee2e2',
  info: '#3b82f6',
  infoLight: '#dbeafe',

  // Glass-specific
  glass: {
    bg: 'rgba(255, 255, 255, 0.15)',
    bgStrong: 'rgba(255, 255, 255, 0.25)',
    bgDark: 'rgba(0, 0, 0, 0.25)',
    border: 'rgba(255, 255, 255, 0.25)',
    borderSubtle: 'rgba(255, 255, 255, 0.15)',
    borderDark: 'rgba(255, 255, 255, 0.1)',
    shadow: 'rgba(0, 0, 0, 0.1)',
  },

  // Surface
  background: {
    primary: '#F0F2F5',
    secondary: '#FFFFFF',
    gradient: ['#004a99', '#001933'] as const,
    gradientAccent: ['#007cff', '#00d9c0'] as const,
  },

  // Text
  text: {
    primary: '#424753',
    secondary: '#8e99af',
    muted: '#878e9f',
    inverse: '#FFFFFF',
    link: '#007cff',
  },

  // Misc
  white: '#FFFFFF',
  black: '#000000',
  transparent: 'transparent',
  overlay: 'rgba(0, 0, 0, 0.5)',
};
