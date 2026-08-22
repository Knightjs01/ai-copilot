"use client";

import { useMutation, useQuery } from "@tanstack/react-query";

import { candidateApiClient } from "@/lib/candidate-api-client";
import type { BoardFilters, ShadowJobMatch, TalentPoolOpportunity } from "@/lib/types";

// `enabled` matters on every hook here for the same reason it does in saved-jobs.ts: the board
// and job detail pages are reachable by logged-out visitors, and matching additionally requires
// an approved Passport -- callers pass `enabled: !!candidate` (and, where relevant, gate further
// on an approved Passport) rather than firing a doomed request.

export function useJobMatch(jobId: string | undefined, options?: { enabled?: boolean }) {
  const { enabled = true } = options ?? {};
  return useQuery({
    queryKey: ["passport-matching", "match", jobId],
    queryFn: () => candidateApiClient.get<ShadowJobMatch>(`/matches/${jobId}`),
    enabled: enabled && !!jobId,
    retry: false, // a 400 (no approved Passport) or 404 (job gone) won't resolve by retrying
  });
}

export function useBatchJobMatches(jobIds: string[], options?: { enabled?: boolean }) {
  const { enabled = true } = options ?? {};
  return useQuery({
    queryKey: ["passport-matching", "batch", jobIds],
    queryFn: () =>
      candidateApiClient.post<ShadowJobMatch[]>("/matches/batch", { shadow_job_ids: jobIds }),
    enabled: enabled && jobIds.length > 0,
    retry: false,
  });
}

export function useNlJobSearch() {
  return useMutation({
    mutationFn: (query: string) =>
      candidateApiClient.post<BoardFilters>("/matches/search", { query }),
  });
}

// Real matches companies have computed against the candidate's own Talent Pool grants -- the
// candidate side of the opportunity workflow (see talent_pool/__init__.py).
export function useTalentPoolOpportunities() {
  return useQuery({
    queryKey: ["passport-matching", "talent-pool-opportunities"],
    queryFn: () =>
      candidateApiClient.get<TalentPoolOpportunity[]>("/matches/my-talent-pool-opportunities"),
    retry: false,
  });
}
