import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import type { User } from '../types/auth';

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  login: (user: User, token: string, refreshToken: string) => void;
  updateUser: (user: User) => void;
  updateTokens: (token: string, refreshToken: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,

      login: (user, token, refreshToken) =>
        set({
          user,
          token,
          refreshToken,
          isAuthenticated: true,
        }),

      updateUser: (user) =>
        set((state) => ({
          user,
          isAuthenticated: Boolean(state.token),
        })),

      updateTokens: (token, refreshToken) =>
        set((state) => ({
          token,
          refreshToken,
          isAuthenticated: Boolean(token),
          user: state.user,
        })),

      logout: () =>
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
        }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => sessionStorage),
    }
  )
);
