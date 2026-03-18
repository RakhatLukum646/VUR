import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { AppState } from '../types';

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // Connection state
      isConnected: false,
      connectionStatus: 'disconnected',

      // Translation state
      isTranslating: false,
      sessionId: `session-${Date.now()}`,
      detectedSigns: [],
      currentSentence: '',
      confidence: 0,
      language: 'ru',

      // History
      translationHistory: [],

      // Actions
      setConnected: (connected) => set({ isConnected: connected }),

      setConnectionStatus: (status) => set({ connectionStatus: status }),

      startTranslation: () => set({
        isTranslating: true,
        connectionStatus: 'connecting',
      }),

      stopTranslation: () => set({
        isTranslating: false,
        connectionStatus: 'disconnected',
      }),

      addDetectedSign: (sign) => set((state) => ({
        detectedSigns: [...state.detectedSigns, sign],
      })),

      setCurrentSentence: (sentence) => set({ currentSentence: sentence }),

      setConfidence: (confidence) => set({ confidence }),

      setLanguage: (language) => set({ language }),

      clearSession: () => set({
        detectedSigns: [],
        currentSentence: '',
        confidence: 0,
        sessionId: `session-${Date.now()}`,
      }),

      addToHistory: (item) => set((state) => ({
        translationHistory: [...state.translationHistory, item],
      })),
    }),
    {
      name: 'app-storage',
      partialize: (state) => ({ language: state.language }),
    }
  )
);
