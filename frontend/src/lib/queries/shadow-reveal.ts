"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient, ApiError } from "@/lib/api-client";
import { candidateApiClient } from "@/lib/candidate-api-client";
import { fetchOrNull } from "@/lib/queries/helpers";
import type { CandidateRevealRequest, RevealedIdentity, RevealRequest } from "@/lib/types";

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

// Not-yet-approved is a normal state (400 RevealNotApprovedError), not an error to surface —
// callers render "not revealed yet" for a null result the same way fetchOrNull's 404 case works.
export function useRevealedIdentity(jobId: string, applicationId: string | undefined) {
  return useQuery({
    queryKey: ["shadow-reveal", "identity", jobId, applicationId],
    queryFn: async () => {
      try {
        return await apiClient.get<RevealedIdentity>(
          `/shadow-reveal/mine/${jobId}/applicants/${applicationId}`
        );
      } catch (err) {
        if (err instanceof ApiError && (err.status === 400 || err.status === 404)) return null;
        throw err;
      }
    },
    enabled: !!applicationId,
  });
}

// --- Candidate side -------------------------------------------------------------------------

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
    mutationFn: (approve: boolean) =>
      candidateApiClient.post<CandidateRevealRequest>(
        `/shadow-reveal/applications/me/${applicationId}/respond`,
        { approve }
      ),
    onSuccess: (data) => {
      queryClient.setQueryData(["shadow-reveal", "me", applicationId], data);
      void queryClient.invalidateQueries({
        queryKey: ["shadow-jobs", "applications", "me", applicationId],
      });
    },
  });
}
