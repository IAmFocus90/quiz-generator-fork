export interface User {
  id: string;
  username: string;
  email: string;
  is_verified: boolean;
  isVerified?: boolean;
  full_name?: string;
  bio?: string;
  location?: string;
  website?: string;
  avatar_color?: string;
  role?: "user" | "admin" | string;
  createdAt?: string;
  updatedAt?: string;
}

export interface UpdateProfilePayload {
  full_name?: string;
  bio?: string;
  location?: string;
  website?: string;
  avatar_color?: string;
}

export interface UpdateProfileResponse {
  message: string;
  user: User;
}

export interface LoginResponse {
  message: string;
  access_token: string;
  token_type: string;
  is_verified?: boolean;
}

export interface RefreshTokenResponse {
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
