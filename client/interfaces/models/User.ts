export interface User {
  id: string;
  username: string;
  email: string;
  isVerified: boolean;
  createdAt?: string;
  updatedAt?: string;
}

export interface LoginResponse {
  message: string;
  access_token: string;
  token_type: string;
}

export interface RegisterResponse {
  user: User;
  message?: string;
}

export interface LoginPayload {
  identifier: string; // email or username
  password: string;
}
