import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import toast from "react-hot-toast";
import { RefreshTokenResponse } from "@features/auth/types/User";
import { TokenService } from "@shared/auth/tokenService";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value?: unknown) => void;
  reject: (reason?: any) => void;
}> = [];

const handleVerificationRequired = (error: AxiosError): boolean => {
  const detail = (error.response?.data as any)?.detail;
  if (error.response?.status !== 403 || detail !== "Email not verified") {
    return false;
  }

  if (typeof window !== "undefined") {
    const mark = "__email_not_verified_toast__";
    if (!(window as any)[mark]) {
      (window as any)[mark] = true;
      toast.error("Please verify your email to continue");
      setTimeout(() => {
        (window as any)[mark] = false;
      }, 2000);
    }

    if (!window.location.pathname.startsWith("/auth/verify-email")) {
      window.location.assign("/auth/verify-email-notice");
    }
  }

  return true;
};

const processQueue = (
  error: AxiosError | null,
  token: string | null = null,
) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = TokenService.getAccessToken();
    if (token && config.headers) {
      const tokenType = TokenService.getTokenType() || "Bearer";
      config.headers.Authorization = `${tokenType} ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (handleVerificationRequired(error)) {
      return Promise.reject(error);
    }

    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (
        originalRequest.url?.includes("/auth/login") ||
        originalRequest.url?.includes("/auth/register") ||
        originalRequest.url?.includes("/auth/refresh")
      ) {
        return Promise.reject(error);
      }

      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await axios.post<RefreshTokenResponse>(
          `${API_BASE_URL}/auth/refresh`,
          {},
          {
            headers: {
              "Content-Type": "application/json",
            },
            withCredentials: true,
          },
        );

        const { access_token, token_type } = response.data;

        TokenService.updateAccessToken(access_token);
        if (token_type) {
          TokenService.setTokens(access_token, token_type);
        }

        if (originalRequest.headers) {
          const headerTokenType = token_type || "Bearer";
          originalRequest.headers.Authorization = `${headerTokenType} ${access_token}`;
        }

        processQueue(null, access_token);
        isRefreshing = false;

        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError as AxiosError, null);
        isRefreshing = false;
        TokenService.clearTokens();

        if (typeof window !== "undefined") {
          window.dispatchEvent(new Event("token-expired"));
        }

        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  },
);

export default api;
