const AUTH_API_URL = 'http://localhost:8003';

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
  token_type: string;
  user: AuthUser;
}

function getAuthHeaders(token: string) {
  return {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  };
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

export async function getCurrentUser(token: string) {
  const response = await fetch(`${AUTH_API_URL}/auth/me`, {
    headers: getAuthHeaders(token),
  });

  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || 'Failed to fetch profile');
  return result;
}

export async function updateProfileName(token: string, name: string) {
  const response = await fetch(`${AUTH_API_URL}/auth/profile`, {
    method: 'PATCH',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ name }),
  });

  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || 'Failed to update name');
  return result;
}

export async function changePassword(
  token: string,
  currentPassword: string,
  newPassword: string
) {
  const response = await fetch(`${AUTH_API_URL}/auth/password`, {
    method: 'PATCH',
    headers: getAuthHeaders(token),
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });

  const result = await response.json();
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

export async function resendVerification(token: string) {
  const response = await fetch(`${AUTH_API_URL}/auth/resend-verification`, {
    method: 'POST',
    headers: getAuthHeaders(token),
  });

  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || 'Failed to resend email');
  return result;
}

export async function setup2FA(token: string) {
  const response = await fetch(`${AUTH_API_URL}/auth/2fa/setup`, {
    method: 'POST',
    headers: getAuthHeaders(token),
  });

  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || 'Failed to setup 2FA');
  return result;
}

export async function enable2FA(token: string, code: string) {
  const response = await fetch(`${AUTH_API_URL}/auth/2fa/enable`, {
    method: 'POST',
    headers: getAuthHeaders(token),
    body: JSON.stringify({ code }),
  });

  const result = await response.json();
  if (!response.ok) throw new Error(result.detail || 'Failed to enable 2FA');
  return result;
}