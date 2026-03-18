import type {
  LoginRequest,
  MessageResponse,
  RecoveryCodesResponse,
  SessionResponse,
  TwoFactorSetupResponse,
  User,
} from '../types/auth';

const AUTH_API_URL = import.meta.env.VITE_AUTH_URL ?? '';

interface RegisterRequest {
  name: string;
  email: string;
  password: string;
}

interface ApiError {
  detail?: string;
  message?: string;
}

async function parseJson<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}

function buildUrl(path: string) {
  return `${AUTH_API_URL}${path}`;
}

async function request<T>(
  path: string,
  init: RequestInit = {}
): Promise<{ data: T; response: Response }> {
  const response = await fetch(buildUrl(path), {
    credentials: 'include',
    ...init,
  });
  const data = await parseJson<T>(response);
  return { data, response };
}

function getErrorMessage(result: ApiError | MessageResponse, fallback: string) {
  if ('detail' in result && result.detail) {
    return result.detail;
  }

  return result.message || fallback;
}

async function refreshSession(): Promise<SessionResponse> {
  const { data, response } = await request<SessionResponse | ApiError>(
    '/auth/refresh',
    {
      method: 'POST',
    }
  );

  if (!response.ok) {
    throw new Error(getErrorMessage(data as ApiError, 'Failed to refresh session'));
  }

  return data as SessionResponse;
}

async function requestWithSession<T>(
  path: string,
  init: RequestInit = {}
): Promise<T> {
  let { data, response } = await request<T | ApiError>(path, init);

  if (response.status === 401) {
    await refreshSession();
    ({ data, response } = await request<T | ApiError>(path, init));
  }

  if (!response.ok) {
    throw new Error(getErrorMessage(data as ApiError, 'Request failed'));
  }

  return data as T;
}

export async function registerUser(data: RegisterRequest) {
  const { data: result, response } = await request<
    { user_id: string; message: string } | ApiError
  >('/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(getErrorMessage(result as ApiError, 'Registration failed'));
  }

  return result as { user_id: string; message: string };
}

export async function loginUser(data: LoginRequest): Promise<SessionResponse> {
  const { data: result, response } = await request<SessionResponse | ApiError>(
    '/auth/login',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  );

  if (!response.ok) {
    throw new Error(getErrorMessage(result as ApiError, 'Login failed'));
  }

  return result as SessionResponse;
}

export async function logoutUser() {
  return requestWithSession<MessageResponse>('/auth/logout', {
    method: 'POST',
  });
}

export async function logoutAllDevices() {
  return requestWithSession<MessageResponse>('/auth/logout-all', {
    method: 'POST',
  });
}

export async function bootstrapSession(): Promise<User | null> {
  try {
    return await requestWithSession<User>('/auth/me');
  } catch {
    return null;
  }
}

export async function getCurrentUser() {
  return requestWithSession<User>('/auth/me');
}

export async function updateProfileName(name: string) {
  return requestWithSession<MessageResponse>('/auth/profile', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
}

export async function changePassword(
  currentPassword: string,
  newPassword: string
) {
  return requestWithSession<MessageResponse>('/auth/password', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
}

export async function verifyEmail(token: string) {
  const { data, response } = await request<MessageResponse | ApiError>(
    '/auth/verify-email',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
    }
  );

  if (!response.ok) {
    throw new Error(getErrorMessage(data as ApiError, 'Email verification failed'));
  }

  return data as MessageResponse;
}

export async function resendVerification(email: string) {
  const { data, response } = await request<MessageResponse | ApiError>(
    '/auth/resend-verification',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    }
  );

  if (!response.ok) {
    throw new Error(
      getErrorMessage(data as ApiError, 'Failed to resend verification email')
    );
  }

  return data as MessageResponse;
}

export async function requestPasswordReset(email: string) {
  const { data, response } = await request<MessageResponse | ApiError>(
    '/auth/password-reset/request',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email }),
    }
  );

  if (!response.ok) {
    throw new Error(
      getErrorMessage(data as ApiError, 'Failed to request password reset')
    );
  }

  return data as MessageResponse;
}

export async function confirmPasswordReset(token: string, newPassword: string) {
  const { data, response } = await request<MessageResponse | ApiError>(
    '/auth/password-reset/confirm',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, new_password: newPassword }),
    }
  );

  if (!response.ok) {
    throw new Error(getErrorMessage(data as ApiError, 'Failed to reset password'));
  }

  return data as MessageResponse;
}

export async function setup2FA() {
  return requestWithSession<TwoFactorSetupResponse>('/auth/2fa/setup', {
    method: 'POST',
  });
}

export async function enable2FA(code: string) {
  return requestWithSession<RecoveryCodesResponse>('/auth/2fa/enable', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  });
}

export async function regenerateRecoveryCodes(currentPassword: string) {
  return requestWithSession<RecoveryCodesResponse>(
    '/auth/2fa/recovery-codes/regenerate',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_password: currentPassword }),
    }
  );
}
