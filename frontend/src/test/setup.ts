import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { afterEach } from 'vitest';
import { useAppStore } from '../store/useAppStore';
import { useAuthStore } from '../store/useAuthStore';

afterEach(() => {
  cleanup();
  useAuthStore.setState({
    user: null,
    isAuthenticated: false,
    isBootstrapped: false,
    isBootstrapping: false,
  });
  useAppStore.setState({
    isConnected: false,
    connectionStatus: 'disconnected',
    isTranslating: false,
    sessionId: 'session-test',
    detectedSigns: [],
    currentSentence: '',
    confidence: 0,
    language: 'ru',
    translationHistory: [],
  });
});
