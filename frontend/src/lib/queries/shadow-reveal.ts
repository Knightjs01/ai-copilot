"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { candidateApiClient } from "@/lib/candidate-api-client";
import { fetchOrNull } from "@/lib/queries/helpers";
import type {
  CandidateRevealHistoryItem,
  CandidateRevealRequest,
  RevealedIdentity,
  RevealRequest,
  ShadowField,
} from "@/lib/types";

// --- Company side --------------------------------------------------------------------------

export function useRequestReveal(jobId: string, applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (reason: string) =>
      apiClient.post<RevealRequest>(
        `/shadow-reveal/mine/${jobId}/applicants/${applicationId}/request`,
        { reason: reason || null }
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applicants", jobId] });
    },
  });
}

// Viewing a revealed identity is step-up-gated (see backend security/zero-trust-overhaul), so
// this can no longer be an auto-fetching useQuery — the user has to re-confirm their password
// first. Call this from a manual "View identity" action after obtaining a step-up token, not on
// render.
export function useFetchRevealedIdentity(jobId: string) {
  return useMutation({
    mutationFn: ({
      applicationId,
      stepUpToken,
    }: {
      applicationId: string;
      stepUpToken: string;
    }) =>
      apiClient.get<RevealedIdentity>(
        `/shadow-reveal/mine/${jobId}/applicants/${applicationId}`,
        stepUpToken
      ),
  });
}

// --- Candidate side -------------------------------------------------------------------------

// The candidate-wide "Identity Activity" timeline -- every reveal request/response across every
// application, not scoped to one like useMyRevealRequest below.
export function useMyRevealHistory() {
  return useQuery({
    queryKey: ["shadow-reveal", "my-history"],
    queryFn: () => candidateApiClient.get<CandidateRevealHistoryItem[]>("/shadow-reveal/my-history"),
  });
}

export function useMyRevealRequest(applicationId: string | undefined) {
  return useQuery({
    queryKey: ["shadow-reveal", "me", applicationId],
    queryFn: () =>
      fetchOrNull(() =>
        candidateApiClient.get<CandidateRevealRequest>(
          `/shadow-reveal/applications/me/${applicationId}`
        )
      ),
    enabled: !!applicationId,
  });
}

export function useRespondToRevealRequest(applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      approve,
      disclosedFields,
    }: {
      approve: boolean;
      disclosedFields?: ShadowField[];
    }) =>
      candidateApiClient.post<CandidateRevealRequest>(
        `/shadow-reveal/applications/me/${applicationId}/respond`,
        { approve, disclosed_fields: disclosedFields }
      ),
    onSuccess: (data) => {
      queryClient.setQueryData(["shadow-reveal", "me", applicationId], data);
      void queryClient.invalidateQueries({
        queryKey: ["shadow-jobs", "applications", "me", applicationId],
      });
    },
  });
}
