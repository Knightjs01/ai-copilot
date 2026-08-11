"use client";

import * as React from "react";

import {
  candidateApiClient,
  refreshCandidateAccessToken,
  setCandidateAccessToken,
} from "@/lib/candidate-api-client";
import type { CandidateMeResponse, CandidateTokenResponse } from "@/lib/types";

interface CandidateAuthContextValue {
  candidate: CandidateMeResponse | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
}

const CandidateAuthContext = React.createContext<CandidateAuthContextValue | null>(null);

export function CandidateAuthProvider({ children }: { children: React.ReactNode }) {
  const [candidate, setCandidate] = React.useState<CandidateMeResponse | null>(null);
  const [isLoading, setIsLoading] = React.useState(true);

  const loadMe = React.useCallback(async () => {
    const me = await candidateApiClient.get<CandidateMeResponse>("/candidate-auth/me");
    setCandidate(me);
  }, []);

  React.useEffect(() => {
    (async () => {
      const token = await refreshCandidateAccessToken();
      if (token) {
        try {
          await loadMe();
        } catch {
          setCandidateAccessToken(null);
        }
      }
      setIsLoading(false);
    })();
  }, [loadMe]);

  const login = React.useCallback(
    async (email: string, password: string) => {
      const res = await candidateApiClient.post<CandidateTokenResponse>("/candidate-auth/login", {
        email,
        password,
      });
      setCandidateAccessToken(res.access_token);
      await loadMe();
    },
    [loadMe]
  );

  const signup = React.useCallback(
    async (email: string, password: string, fullName: string) => {
      const res = await candidateApiClient.post<CandidateTokenResponse>(
        "/candidate-auth/signup",
        { email, password, full_name: fullName }
      );
      setCandidateAccessToken(res.access_token);
      await loadMe();
    },
    [loadMe]
  );

  const logout = React.useCallback(async () => {
    try {
      await candidateApiClient.post("/candidate-auth/logout");
    } catch {
      // Best-effort — clear local state regardless of whether the network call succeeded.
    }
    setCandidateAccessToken(null);
    setCandidate(null);
  }, []);

  const value = React.useMemo(
    () => ({ candidate, isLoading, login, signup, logout }),
    [candidate, isLoading, login, signup, logout]
  );

  return (
    <CandidateAuthContext.Provider value={value}>{children}</CandidateAuthContext.Provider>
  );
}

export function useCandidateAuth(): CandidateAuthContextValue {
  const ctx = React.useContext(CandidateAuthContext);
  if (!ctx) throw new Error("useCandidateAuth must be used within CandidateAuthProvider");
  return ctx;
}
