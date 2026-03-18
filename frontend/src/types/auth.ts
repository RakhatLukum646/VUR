export interface User {
  id: string
  name: string
  email: string
  is_verified?: boolean
  two_factor_enabled?: boolean
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  user: User;
}