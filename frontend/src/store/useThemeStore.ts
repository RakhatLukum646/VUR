import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type ColorScheme = 'light' | 'dark' | 'system';

export type ColorblindMode = 'none' | 'protanopia' | 'deuteranopia' | 'tritanopia';

type ThemeState = {
  colorScheme: ColorScheme;
  colorblindMode: ColorblindMode;
  setColorScheme: (value: ColorScheme) => void;
  setColorblindMode: (value: ColorblindMode) => void;
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      colorScheme: 'system',
      colorblindMode: 'none',
      setColorScheme: (colorScheme) => set({ colorScheme }),
      setColorblindMode: (colorblindMode) => set({ colorblindMode }),
    }),
    { name: 'signzhan-theme' }
  )
);
