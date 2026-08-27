"use client";

import * as React from "react";

import {
  getPlatformAdminAccessToken,
  platformAdminApiClient,
  refreshPlatformAdminAccessToken,
  setPlatformAdminAccessToken,
} from "@/lib/platform-admin-api-client";
import type { PlatformAdmin } from "@/lib/types";

interface PlatformAdminAuthContextValue {
  admin: PlatformAdmin | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const PlatformAdminAuthContext = React.createContext<PlatformAdminAuthContextValue | null>(null);

export function PlatformAdminAuthProvider({ children }: { children: React.ReactNode }) {
  const [admin, setAdmin] = React.useState<PlatformAdmin | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    (async () => {
      // A fresh page load has no in-memory access token — try the httponly refresh cookie first
      // so a reload silently re-establishes the session instead of bouncing to the login page.
      if (!getPlatformAdminAccessToken()) {
        await refreshPlatformAdminAccessToken();
      }
      if (getPlatformAdminAccessToken()) {
        try {
          const me = await platformAdminApiClient.get<PlatformAdmin>("/platform-admin/me");
          setAdmin(me);
        } catch {
          setPlatformAdminAccessToken(null);
        }
      }
      setIsLoading(false);
    })();
  }, []);

  const login = React.useCallback(async (email: string, password: string) => {
    const res = await platformAdminApiClient.post<{ access_token: string }>(
      "/platform-admin/login",
      { email, password }
    );
    setPlatformAdminAccessToken(res.access_token);
    const me = await platformAdminApiClient.get<PlatformAdmin>("/platform-admin/me");
    setAdmin(me);
  }, []);

  const logout = React.useCallback(async () => {
    try {
      await platformAdminApiClient.post("/platform-admin/logout");
    } finally {
      setPlatformAdminAccessToken(null);
      setAdmin(null);
    }
  }, []);

  const value = React.useMemo(
    () => ({ admin, isLoading, login, logout }),
    [admin, isLoading, login, logout]
  );

  return (
    <PlatformAdminAuthContext.Provider value={value}>{children}</PlatformAdminAuthContext.Provider>
  );
}

export function usePlatformAdminAuth(): PlatformAdminAuthContextValue {
  const ctx = React.useContext(PlatformAdminAuthContext);
  if (!ctx) throw new Error("usePlatformAdminAuth must be used within PlatformAdminAuthProvider");
  return ctx;
}
