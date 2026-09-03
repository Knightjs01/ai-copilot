"use client";

import * as React from "react";

import {
  getPlatformAdminAccessToken,
  platformAdminApiClient,
  refreshPlatformAdminAccessToken,
  setPlatformAdminAccessToken,
} from "@/lib/platform-admin-api-client";
import type { MfaEnableResponse, MfaSetupResponse, PlatformAdmin } from "@/lib/types";

// Mirrors lib/auth-context.tsx's LoginResult exactly, with a third branch: Phantom Command
// requires MFA at login with no opt-out, so an admin who has never enrolled must be walked
// through enrollment (mfaEnrollmentRequired) rather than just being told MFA is required.
export type PlatformAdminLoginResult =
  | { mfaRequired: false; mfaEnrollmentRequired: false }
  | { mfaRequired: true; mfaEnrollmentRequired: false; challengeToken: string }
  | { mfaRequired: false; mfaEnrollmentRequired: true; pendingToken: string };

interface PlatformAdminAuthContextValue {
  admin: PlatformAdmin | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<PlatformAdminLoginResult>;
  verifyMfa: (challengeToken: string, code: string) => Promise<void>;
  getPendingMfaSetup: (pendingToken: string) => Promise<MfaSetupResponse>;
  enrollMfa: (
    pendingToken: string,
    secret: string,
    code: string
  ) => Promise<MfaEnableResponse>;
  logout: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  refreshAdmin: () => Promise<void>;
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

  const login = React.useCallback(
    async (email: string, password: string): Promise<PlatformAdminLoginResult> => {
      const res = await platformAdminApiClient.post<
        | { access_token: string }
        | { mfa_required: true; challenge_token: string }
        | { mfa_enrollment_required: true; pending_token: string }
      >("/platform-admin/login", { email, password });
      if ("mfa_required" in res) {
        return { mfaRequired: true, mfaEnrollmentRequired: false, challengeToken: res.challenge_token };
      }
      if ("mfa_enrollment_required" in res) {
        return { mfaRequired: false, mfaEnrollmentRequired: true, pendingToken: res.pending_token };
      }
      setPlatformAdminAccessToken(res.access_token);
      const me = await platformAdminApiClient.get<PlatformAdmin>("/platform-admin/me");
      setAdmin(me);
      return { mfaRequired: false, mfaEnrollmentRequired: false };
    },
    []
  );

  const verifyMfa = React.useCallback(async (challengeToken: string, code: string) => {
    const res = await platformAdminApiClient.post<{ access_token: string }>(
      "/platform-admin/mfa/verify",
      { challenge_token: challengeToken, code }
    );
    setPlatformAdminAccessToken(res.access_token);
    const me = await platformAdminApiClient.get<PlatformAdmin>("/platform-admin/me");
    setAdmin(me);
  }, []);

  const getPendingMfaSetup = React.useCallback(async (pendingToken: string) => {
    return platformAdminApiClient.post<MfaSetupResponse>("/platform-admin/mfa/pending/setup", {
      pending_token: pendingToken,
    });
  }, []);

  const enrollMfa = React.useCallback(
    async (pendingToken: string, secret: string, code: string) => {
      const res = await platformAdminApiClient.post<{
        access_token: string;
        backup_codes: string[];
      }>("/platform-admin/mfa/pending/enable", {
        pending_token: pendingToken,
        secret,
        code,
      });
      setPlatformAdminAccessToken(res.access_token);
      const me = await platformAdminApiClient.get<PlatformAdmin>("/platform-admin/me");
      setAdmin(me);
      return { backup_codes: res.backup_codes };
    },
    []
  );

  const logout = React.useCallback(async () => {
    try {
      await platformAdminApiClient.post("/platform-admin/logout");
    } finally {
      setPlatformAdminAccessToken(null);
      setAdmin(null);
    }
  }, []);

  const hasPermission = React.useCallback(
    (permission: string) => admin?.permissions.includes(permission) ?? false,
    [admin]
  );

  const refreshAdmin = React.useCallback(async () => {
    const me = await platformAdminApiClient.get<PlatformAdmin>("/platform-admin/me");
    setAdmin(me);
  }, []);

  const value = React.useMemo(
    () => ({
      admin,
      isLoading,
      login,
      verifyMfa,
      getPendingMfaSetup,
      enrollMfa,
      logout,
      hasPermission,
      refreshAdmin,
    }),
    [
      admin,
      isLoading,
      login,
      verifyMfa,
      getPendingMfaSetup,
      enrollMfa,
      logout,
      hasPermission,
      refreshAdmin,
    ]
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
