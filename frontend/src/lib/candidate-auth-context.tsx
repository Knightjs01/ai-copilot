"use client";

import * as React from "react";

import {
  candidateApiClient,
  refreshCandidateAccessToken,
  setCandidateAccessToken,
} from "@/lib/candidate-api-client";
import type {
  CandidateMeResponse,
  CandidateMfaChallengeResponse,
  CandidateTokenResponse,
} from "@/lib/types";

export type CandidateLoginResult =
  | { mfaRequired: false }
  | { mfaRequired: true; challengeToken: string };

interface CandidateAuthContextValue {
  candidate: CandidateMeResponse | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<CandidateLoginResult>;
  verifyMfa: (challengeToken: string, code: string) => Promise<void>;
  signup: (
    email: string,
    password: string,
    firstName: string,
    lastName?: string | null
  ) => Promise<void>;
  logout: () => Promise<void>;
}

const CandidateAuthContext = React.createContext<CandidateAuthContextValue | null>(null);

// Mirrors lib/auth-context.tsx's isMfaChallenge exactly, against the candidate response shape.
function isMfaChallenge(
  res: CandidateTokenResponse | CandidateMfaChallengeResponse
): res is CandidateMfaChallengeResponse {
  return "mfa_required" in res;
}

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
    async (email: string, password: string): Promise<CandidateLoginResult> => {
      const res = await candidateApiClient.post<CandidateTokenResponse | CandidateMfaChallengeResponse>(
        "/candidate-auth/login",
        { email, password }
      );
      if (isMfaChallenge(res)) {
        return { mfaRequired: true, challengeToken: res.challenge_token };
      }
      setCandidateAccessToken(res.access_token);
      await loadMe();
      return { mfaRequired: false };
    },
    [loadMe]
  );

  const verifyMfa = React.useCallback(
    async (challengeToken: string, code: string) => {
      const res = await candidateApiClient.post<CandidateTokenResponse>("/candidate-auth/mfa/verify", {
        challenge_token: challengeToken,
        code,
      });
      setCandidateAccessToken(res.access_token);
      await loadMe();
    },
    [loadMe]
  );

  const signup = React.useCallback(
    async (email: string, password: string, firstName: string, lastName?: string | null) => {
      const res = await candidateApiClient.post<CandidateTokenResponse>(
        "/candidate-auth/signup",
        { email, password, first_name: firstName, last_name: lastName || null }
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
    () => ({ candidate, isLoading, login, verifyMfa, signup, logout }),
    [candidate, isLoading, login, verifyMfa, signup, logout]
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
