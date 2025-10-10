import axios from "axios";
import { LoginResponse, LoginPayload } from "../../interfaces/models/User";

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export const registerUser = async (data: {
  username: string;
  email: string;
  full_name: string;
  password: string;
}) => {
  const response = await api.post("/auth/register/", data);
  return response.data;
};

export const verifyOtp = async (email: string, otp: string) =>
  api.post("/auth/verify-otp/", null, { params: { email, otp } });

export const verifyLink = async (token: string) =>
  api.post("/auth/verify-link/", null, { params: { token } });

export const resendVerification = async (email: string) =>
  api.post("/auth/resend-verification", { email });

export const login = async (payload: LoginPayload): Promise<LoginResponse> => {
  try {
    const response = await api.post("/auth/login", payload);
    return response.data as LoginResponse;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || "Login failed");
  }
};

export const getProfile = async (token: string) => {
  const response = await api.get("/auth/profile", {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};

export const requestPasswordReset = async (email: string) =>
  api.post("/auth/request-password-reset", { email });

export const resetPassword = async (data: {
  email: string;
  reset_method: "otp" | "token";
  new_password: string;
  otp?: string;
  token?: string;
}) => api.post("/auth/reset-password", data);

export const logoutUser = async (token: string) => {
  const response = await api.post("/auth/logout", null, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return response.data;
};
