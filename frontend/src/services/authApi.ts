import type { LoginRequest, LoginResponse } from '../types/auth';

export async function loginUser(
  data: LoginRequest
): Promise<LoginResponse> {
  await new Promise((resolve) => setTimeout(resolve, 700));

  if (data.email === 'test@test.com' && data.password === '123456') {
    return {
      token: 'mock-jwt-token',
      user: {
        id: '1',
        name: 'Vladislav',
        email: data.email,
        role: 'Student',
      },
    };
  }

  throw new Error('Invalid credentials');
}