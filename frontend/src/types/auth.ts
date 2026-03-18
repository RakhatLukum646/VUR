export interface User {
  id: string;
  name: string;
  email: string;
  is_verified?: boolean;
  two_factor_enabled?: boolean;
}

export interface LoginRequest {
  email: string;
  password: string;
  twofa_code?: string;
  recovery_code?: string;
}

export interface SessionResponse {
  token_type: 'session';
  access_expires_in: number;
  refresh_expires_in: number;
  user: User;
}

export interface MessageResponse {
  message: string;
}

export interface TwoFactorSetupResponse {
  secret: string;
  otp_auth_url: string;
}

export interface RecoveryCodesResponse extends MessageResponse {
  recovery_codes: string[];
}
