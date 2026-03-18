import { useAuthStore } from '../store/useAuthStore';

// In Docker the Nginx gateway forwards /auth/ to the auth service.
// In local dev set VITE_AUTH_URL=http://localhost:8003 in .env.local.
const AUTH_API_URL = import.meta.env.VITE_AUTH_URL ?? '';

export interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  twofa_code?: string;
}

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  is_verified?: boolean;
  two_factor_enabled?: boolean;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  access_expires_in: number;
  refresh_expires_in: number;
  user: AuthUser;
}

export interface RefreshTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  access_expires_in: number;
  refresh_expires_in: number;
  user: AuthUser;
}

interface ApiError {
  detail?: string;
}

function getAuthHeaders(token: string, headers?: HeadersInit) {
  return {
    ...(headers ?? {}),
    Authorization: `Bearer ${token}`,
  };
}

async function parseJson<T>(response: Response): Promise<T> {
  return response.json() as Promise<T>;
}

export async function refreshAccessToken(
  refreshToken: string
): Promise<RefreshTokenResponse> {
  const response = await fetch(`${AUTH_API_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });

  const result = await parseJson<RefreshTokenResponse | { detail?: string }>(response);
  if (!response.ok) {
    throw new Error((result as ApiError).detail || 'Failed to refresh session');
  }

  return result as RefreshTokenResponse;
}

async function ensureFreshToken(): Promise<string> {
  const { token, refreshToken, updateTokens, updateUser, logout } =
    useAuthStore.getState();

  if (!token) {
    throw new Error('Not authenticated');
  }

  if (!refreshToken) {
    logout();
    throw new Error('Session expired');
  }

  const refreshed = await refreshAccessToken(refreshToken);
  updateTokens(refreshed.access_token, refreshed.refresh_token);
  updateUser(refreshed.user);
  return refreshed.access_token;
}

async function fetchWithAuth(
  path: string,
  init: RequestInit = {}
): Promise<Response> {
  const { token, logout } = useAuthStore.getState();

  if (!token) {
    throw new Error('Not authenticated');
  }

  const run = async (authToken: string) =>
    fetch(`${AUTH_API_URL}${path}`, {
      ...init,
      headers: getAuthHeaders(authToken, init.headers),
    });

  let response = await run(token);

  if (response.status === 401) {
    try {
      const freshToken = await ensureFreshToken();
      response = await run(freshToken);
    } catch (error) {
      logout();
      throw error;
    }
  }

  return response;
}

export async function registerUser(data: RegisterRequest) {
  const response = await fetch(`${AUTH_API_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || 'Registration failed');
  return result;
}

export async function loginUser(data: LoginRequest): Promise<LoginResponse> {
  const response = await fetch(`${AUTH_API_URL}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  const result = await response.json();

  if (!response.ok) {
    throw new Error(result.detail || 'Login failed');
  }

  return result;
}

export async function getCurrentUser() {
  const response = await fetchWithAuth('/auth/me');

  const result = await parseJson<AuthUser | ApiError>(response);
  if (!response.ok) {
    throw new Error((result as ApiError).detail || 'Failed to fetch profile');
  }
  return result as AuthUser;
}

export async function updateProfileName(name: string) {
  const response = await fetchWithAuth('/auth/profile', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });

  const result = await parseJson<{ message?: string; detail?: string }>(response);
  if (!response.ok) throw new Error(result.detail || 'Failed to update name');
  return result;
}

export async function changePassword(
  currentPassword: string,
  newPassword: string
) {
  const response = await fetchWithAuth('/auth/password', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });

  const result = await parseJson<{ message?: string; detail?: string }>(response);
  if (!response.ok) throw new Error(result.detail || 'Failed to change password');
  return result;
}

export async function verifyEmail(tokenValue: string) {
  const response = await fetch(`${AUTH_API_URL}/auth/verify-email`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token: tokenValue }),
  });

  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || 'Email verification failed');
  return result;
}

export async function resendVerification() {
  const response = await fetchWithAuth('/auth/resend-verification', {
    method: 'POST',
  });

  const result = await parseJson<{ message?: string; detail?: string }>(response);
  if (!response.ok) throw new Error(result.detail || 'Failed to resend email');
  return result;
}

export async function setup2FA() {
  const response = await fetchWithAuth('/auth/2fa/setup', {
    method: 'POST',
  });

  const result = await parseJson<
    { secret: string; otp_auth_url: string; detail?: string }
  >(response);
  if (!response.ok) throw new Error(result.detail || 'Failed to setup 2FA');
  return result;
}

export async function enable2FA(code: string) {
  const response = await fetchWithAuth('/auth/2fa/enable', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  });

  const result = await parseJson<{ message?: string; detail?: string }>(response);
  if (!response.ok) throw new Error(result.detail || 'Failed to enable 2FA');
  return result;
}
