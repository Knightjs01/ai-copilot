"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { candidateApiClient } from "@/lib/candidate-api-client";
import type {
  CandidateTalentPoolRequest,
  TalentPoolBulkRequestResult,
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

export function useBulkRequestTalentPool() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      jobId,
      callsigns,
      note,
    }: {
      jobId: string;
      callsigns: string[];
      note?: string;
    }) =>
      apiClient.post<TalentPoolBulkRequestResult>("/talent-pool/mine/search/request-bulk", {
        job_id: jobId,
        callsigns,
        note: note || null,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["talent-pool", "mine"] });
    },
  });
}

// Granted candidates eligible to be added to this project's pipeline (company_wide grants plus
// project_only grants scoped to this exact project) -- powers "Add existing candidate," the
// consent-gated replacement for manually creating a brand-new Candidate row.
export function useEligibleTalentPoolForProject(projectId: string | undefined) {
  return useQuery({
    queryKey: ["talent-pool", "eligible", projectId],
    queryFn: () =>
      apiClient.get<TalentPoolPoolListItem[]>(`/talent-pool/mine/projects/${projectId}/eligible`),
    enabled: !!projectId,
  });
}

export function useCompanyTalentPool() {
  return useQuery({
    queryKey: ["talent-pool", "mine"],
    queryFn: () => apiClient.get<TalentPoolPoolListItem[]>("/talent-pool/mine"),
  });
}

// Sets (or clears, with pool_name: null) the organizational pool label on one or more of the
// caller's own granted rows. See TalentPoolGrant.pool_name's backend docstring -- a pool is just
// "rows sharing this string," not a separate entity, so this is the only write operation needed.
export function useAssignTalentPool() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ grantIds, poolName }: { grantIds: string[]; poolName: string | null }) =>
      apiClient.post<void>("/talent-pool/mine/pools/assign", {
        grant_ids: grantIds,
        pool_name: poolName,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["talent-pool", "mine"] });
    },
  });
}

export function useRenameTalentPool() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ oldName, newName }: { oldName: string; newName: string }) =>
      apiClient.post<{ updated: number }>("/talent-pool/mine/pools/rename", {
        old_name: oldName,
        new_name: newName,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["talent-pool", "mine"] });
    },
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
