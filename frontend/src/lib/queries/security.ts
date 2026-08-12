"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { MfaEnableResponse, MfaSetupResponse, SessionRead } from "@/lib/types";

export function useMfaSetup() {
  return useMutation({
    mutationFn: () => apiClient.post<MfaSetupResponse>("/auth/mfa/setup"),
  });
}

// /auth/me isn't cached through TanStack Query (AuthProvider holds it in plain React state) —
// callers must call useAuth().refreshUser() themselves after these succeed to pick up the new
// mfa_enabled value.
export function useMfaEnable() {
  return useMutation({
    mutationFn: (input: { secret: string; code: string }) =>
      apiClient.post<MfaEnableResponse>("/auth/mfa/enable", input),
  });
}

export function useMfaDisable() {
  return useMutation({
    mutationFn: (password: string) => apiClient.post<void>("/auth/mfa/disable", { password }),
  });
}

export function useSessions() {
  return useQuery({
    queryKey: ["auth", "sessions"],
    queryFn: () => apiClient.get<SessionRead[]>("/auth/sessions"),
  });
}

export function useRevokeSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => apiClient.delete<void>(`/auth/sessions/${sessionId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["auth", "sessions"] });
    },
  });
}

export function useRevokeOtherSessions() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<void>("/auth/sessions/revoke-others"),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["auth", "sessions"] });
    },
  });
}
