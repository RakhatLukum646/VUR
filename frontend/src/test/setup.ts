import { cleanup } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { afterEach } from 'vitest';
import { useAuthStore } from '../store/useAuthStore';

afterEach(() => {
  cleanup();
  useAuthStore.setState({
    user: null,
    isAuthenticated: false,
    isBootstrapped: false,
    isBootstrapping: false,
  });
});
