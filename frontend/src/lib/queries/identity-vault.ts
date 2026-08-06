"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { CandidateIdentitySnapshot, VaultDashboardStats, VaultListItem } from "@/lib/types";

export function useRevealIdentity(candidateId: string) {
  return useMutation({
    mutationFn: (reason: string) =>
      apiClient.post<CandidateIdentitySnapshot>(`/identity-vault/candidates/${candidateId}/reveal`, {
        reason,
      }),
  });
}

export function useCloseReveal() {
  return useMutation({
    mutationFn: ({ eventId, durationSeconds }: { eventId: string; durationSeconds: number }) =>
      apiClient.post<void>(`/identity-vault/reveal-events/${eventId}/close`, {
        duration_seconds: durationSeconds,
      }),
  });
}

interface UpdateVaultFieldsInput {
  location?: string;
  current_employer?: string;
  current_title?: string;
  linkedin_url?: string;
}

export function useUpdateVaultFields(candidateId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: UpdateVaultFieldsInput) =>
      apiClient.patch(`/identity-vault/candidates/${candidateId}`, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["identity-vault", "project"] });
    },
  });
}

export function useProjectVault(projectId: string | undefined) {
  return useQuery({
    queryKey: ["identity-vault", "project", projectId],
    queryFn: () => apiClient.get<VaultListItem[]>(`/identity-vault/projects/${projectId}`),
    enabled: !!projectId,
  });
}

export function useVaultDashboard(projectId: string | undefined) {
  return useQuery({
    queryKey: ["identity-vault", "dashboard", projectId],
    queryFn: () =>
      apiClient.get<VaultDashboardStats>(`/identity-vault/projects/${projectId}/dashboard`),
    enabled: !!projectId,
  });
}
