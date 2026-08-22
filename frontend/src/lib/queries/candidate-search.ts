"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { CandidateSearchResult, TalentPoolMatchResult } from "@/lib/types";

// Company side (company auth, apiClient) — job-anchored AI-matched search over discoverable
// Shadow candidates. See lib/queries/passport-matching.ts for the reverse axis (candidate
// searching across jobs).
export function useCandidateSearch(jobId: string | undefined, options?: { enabled?: boolean }) {
  const { enabled = true } = options ?? {};
  return useQuery({
    queryKey: ["matches", "candidates", jobId],
    queryFn: () => apiClient.get<CandidateSearchResult[]>(`/matches/mine/${jobId}/candidates`),
    enabled: enabled && !!jobId,
  });
}

// Same job-anchored search, scoped to this company's granted Talent Pool instead of every
// discoverable Shadow candidate. See talent_pool/__init__.py for the permission model this pulls
// its candidate pool from.
export function useTalentPoolMatches(jobId: string | undefined, options?: { enabled?: boolean }) {
  const { enabled = true } = options ?? {};
  return useQuery({
    queryKey: ["matches", "talent-pool", jobId],
    queryFn: () =>
      apiClient.get<TalentPoolMatchResult[]>(`/matches/mine/${jobId}/talent-pool`),
    enabled: enabled && !!jobId,
  });
}
