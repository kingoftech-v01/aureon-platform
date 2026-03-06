/**
 * App Store - Zustand
 * Manages app-level state (theme, onboarding)
 */

import { create } from 'zustand';

type ThemeMode = 'light' | 'dark' | 'system';

interface AppState {
  theme: ThemeMode;
  hasCompletedOnboarding: boolean;
  setTheme: (theme: ThemeMode) => void;
  setOnboardingComplete: () => void;
}

export const useAppStore = create<AppState>((set) => ({
  theme: 'light',
  hasCompletedOnboarding: false,

  setTheme: (theme: ThemeMode) => set({ theme }),
  setOnboardingComplete: () => set({ hasCompletedOnboarding: true }),
}));
