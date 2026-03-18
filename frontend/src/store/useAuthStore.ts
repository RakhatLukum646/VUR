import { create } from 'zustand';
import type { User } from '../types/auth';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isBootstrapped: boolean;
  isBootstrapping: boolean;
  beginBootstrap: () => void;
  completeBootstrap: (user: User | null) => void;
  login: (user: User) => void;
  updateUser: (user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()((set) => ({
  user: null,
  isAuthenticated: false,
  isBootstrapped: false,
  isBootstrapping: false,

  beginBootstrap: () =>
    set((state) =>
      state.isBootstrapped || state.isBootstrapping
        ? state
        : { ...state, isBootstrapping: true }
    ),

  completeBootstrap: (user) =>
    set({
      user,
      isAuthenticated: Boolean(user),
      isBootstrapped: true,
      isBootstrapping: false,
    }),

  login: (user) =>
    set({
      user,
      isAuthenticated: true,
      isBootstrapped: true,
      isBootstrapping: false,
    }),

  updateUser: (user) =>
    set({
      user,
      isAuthenticated: true,
      isBootstrapped: true,
      isBootstrapping: false,
    }),

  logout: () =>
    set({
      user: null,
      isAuthenticated: false,
      isBootstrapped: true,
      isBootstrapping: false,
    }),
}));
