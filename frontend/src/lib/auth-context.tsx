"use client";

import * as React from "react";

import { apiClient, refreshAccessToken, setAccessToken } from "@/lib/api-client";
import type { MeResponse, MfaChallengeResponse, TokenResponse } from "@/lib/types";

interface AuthContextValue {
  user: MeResponse | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (
    companyName: string,
    email: string,
    password: string,
    fullName: string
  ) => Promise<void>;
  acceptInvite: (token: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = React.createContext<AuthContextValue | null>(null);

function isMfaChallenge(
  res: TokenResponse | MfaChallengeResponse
): res is MfaChallengeResponse {
  return "mfa_required" in res;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<MeResponse | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  const loadMe = React.useCallback(async () => {
    const me = await apiClient.get<MeResponse>("/auth/me");
    setUser(me);
  }, []);

  React.useEffect(() => {
    (async () => {
      const token = await refreshAccessToken();
      if (token) {
        try {
          await loadMe();
        } catch {
          setAccessToken(null);
        }
      }
      setIsLoading(false);
    })();
  }, [loadMe]);

  const login = React.useCallback(
    async (email: string, password: string) => {
      const res = await apiClient.post<TokenResponse | MfaChallengeResponse>("/auth/login", {
        email,
        password,
      });
      if (isMfaChallenge(res)) {
        throw new Error(
          "This account has multi-factor authentication enabled, which this preview UI doesn't support yet — disable MFA on the account or use the API directly."
        );
      }
      setAccessToken(res.access_token);
      await loadMe();
    },
    [loadMe]
  );

  const signup = React.useCallback(
    async (companyName: string, email: string, password: string, fullName: string) => {
      const res = await apiClient.post<TokenResponse>("/auth/signup", {
        company_name: companyName,
        email,
        password,
        full_name: fullName,
      });
      setAccessToken(res.access_token);
      await loadMe();
    },
    [loadMe]
  );

  const acceptInvite = React.useCallback(
    async (token: string, password: string) => {
      const res = await apiClient.post<TokenResponse>("/users/accept-invite", {
        token,
        password,
      });
      setAccessToken(res.access_token);
      await loadMe();
    },
    [loadMe]
  );

  const logout = React.useCallback(async () => {
    try {
      await apiClient.post("/auth/logout");
    } catch {
      // Best-effort — clear local state regardless of whether the network call succeeded.
    }
    setAccessToken(null);
    setUser(null);
  }, []);

  const hasPermission = React.useCallback(
    (permission: string) => user?.permissions.includes(permission) ?? false,
    [user]
  );

  const value = React.useMemo(
    () => ({ user, isLoading, login, signup, acceptInvite, logout, hasPermission }),
    [user, isLoading, login, signup, acceptInvite, logout, hasPermission]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
