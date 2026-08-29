"use client";

import { useMutation } from "@tanstack/react-query";

import { candidateApiClient } from "@/lib/candidate-api-client";
import type { CandidateMfaEnableResponse, CandidateMfaSetupResponse } from "@/lib/types";

// Mirrors lib/queries/security.ts (the company equivalent) exactly, against
// /candidate-auth/mfa/* instead of /auth/mfa/*. candidate.mfa_enabled isn't cached through
// TanStack Query (CandidateAuthProvider holds it in plain React state) -- callers must call
// useCandidateAuth().refreshCandidate() themselves after these succeed to pick up the new value.

export function useCandidateMfaSetup() {
  return useMutation({
    mutationFn: () => candidateApiClient.post<CandidateMfaSetupResponse>("/candidate-auth/mfa/setup"),
  });
}

export function useCandidateMfaEnable() {
  return useMutation({
    mutationFn: (input: { secret: string; code: string }) =>
      candidateApiClient.post<CandidateMfaEnableResponse>("/candidate-auth/mfa/enable", input),
  });
}

export function useCandidateMfaDisable() {
  return useMutation({
    mutationFn: (password: string) =>
      candidateApiClient.post<void>("/candidate-auth/mfa/disable", { password }),
  });
}
