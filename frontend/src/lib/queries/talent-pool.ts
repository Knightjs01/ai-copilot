"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { candidateApiClient } from "@/lib/candidate-api-client";
import type {
  CandidateTalentPoolRequest,
  TalentPoolGrantRead,
  TalentPoolPoolListItem,
  TalentPoolScope,
} from "@/lib/types";

// --- Company side --------------------------------------------------------------------------

export function useRequestTalentPool(jobId: string, applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (note: string) =>
      apiClient.post<TalentPoolGrantRead>(
        `/talent-pool/mine/${jobId}/applicants/${applicationId}/request`,
        { note: note || null }
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applicants", jobId] });
    },
  });
}

export function useCompanyTalentPool() {
  return useQuery({
    queryKey: ["talent-pool", "mine"],
    queryFn: () => apiClient.get<TalentPoolPoolListItem[]>("/talent-pool/mine"),
  });
}

// --- Candidate side -------------------------------------------------------------------------

export function useMyTalentPoolRequests() {
  return useQuery({
    queryKey: ["talent-pool", "my-requests"],
    queryFn: () =>
      candidateApiClient.get<CandidateTalentPoolRequest[]>("/talent-pool/my-requests"),
  });
}

export function useRespondToTalentPoolRequest(grantId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ approve, scope }: { approve: boolean; scope?: TalentPoolScope }) =>
      candidateApiClient.post<CandidateTalentPoolRequest>(
        `/talent-pool/requests/me/${grantId}/respond`,
        { approve, scope }
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["talent-pool", "my-requests"] });
    },
  });
}

export function useWithdrawTalentPoolGrant(grantId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      candidateApiClient.post<CandidateTalentPoolRequest>(
        `/talent-pool/requests/me/${grantId}/withdraw`,
        {}
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["talent-pool", "my-requests"] });
    },
  });
}
