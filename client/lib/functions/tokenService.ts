export const TokenService = {
  getAccessToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
  },

  getRefreshToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("refresh_token");
  },

  getTokenType(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("token_type");
  },

  setTokens(
    accessToken: string,
    refreshToken: string,
    tokenType: string = "bearer",
  ): void {
    if (typeof window === "undefined") return;
    localStorage.setItem("access_token", accessToken);
    localStorage.setItem("refresh_token", refreshToken);
    localStorage.setItem("token_type", tokenType);
  },

  updateAccessToken(accessToken: string): void {
    if (typeof window === "undefined") return;
    localStorage.setItem("access_token", accessToken);
  },

  clearTokens(): void {
    if (typeof window === "undefined") return;
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("token_type");
  },

  hasTokens(): boolean {
    return !!(this.getAccessToken() && this.getRefreshToken());
  },
};
