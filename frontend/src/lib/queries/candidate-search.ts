"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { CandidateSearchResult, ShadowJobMatch, TalentPoolMatchResult } from "@/lib/types";

// Company side, one applicant already on this page — not a search, just the real cached (or
// freshly computed) match between this one applicant's frozen Passport snapshot and the job
// they applied to. Same response shape as the candidate-side useJobMatch (ShadowJobMatch).
export function useApplicantMatch(jobId: string | undefined, applicationId: string | undefined) {
  return useQuery({
    queryKey: ["matches", "applicant", jobId, applicationId],
    queryFn: () =>
      apiClient.get<ShadowJobMatch>(`/matches/mine/${jobId}/applicants/${applicationId}`),
    enabled: !!jobId && !!applicationId,
    retry: false,
  });
}

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
