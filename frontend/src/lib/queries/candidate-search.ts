"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type {
  CandidateSearchResult,
  PassReason,
  ShadowJobMatch,
  TalentPoolMatchResult,
} from "@/lib/types";

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

// Optional pre-scoring filters (Phase 4) -- applied server-side in list_discoverable_candidates,
// before the per-candidate LLM scoring loop, not a post-hoc client-side narrowing. Every field is
// optional and defaults to "no filter" so an empty object behaves exactly like no filters at all.
export interface CandidateSearchFilters {
  location?: string;
  seniority?: string;
  minYearsExperience?: number;
  skills?: string[];
}

function buildSearchQueryString(filters: CandidateSearchFilters): string {
  const params = new URLSearchParams();
  if (filters.location) params.set("location", filters.location);
  if (filters.seniority) params.set("seniority", filters.seniority);
  if (filters.minYearsExperience != null) {
    params.set("min_years_experience", String(filters.minYearsExperience));
  }
  for (const skill of filters.skills ?? []) {
    params.append("skills", skill);
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

// Company side (company auth, apiClient) — job-anchored AI-matched search over discoverable
// Shadow candidates. See lib/queries/passport-matching.ts for the reverse axis (candidate
// searching across jobs). `filters` is included in the query key so each distinct filter
// combination caches separately -- clearing a filter re-fetches, it doesn't silently reuse a
// narrower cached result.
export function useCandidateSearch(
  jobId: string | undefined,
  filters: CandidateSearchFilters = {},
  options?: { enabled?: boolean }
) {
  const { enabled = true } = options ?? {};
  return useQuery({
    queryKey: ["matches", "candidates", jobId, filters],
    queryFn: () =>
      apiClient.get<CandidateSearchResult[]>(
        `/matches/mine/${jobId}/candidates${buildSearchQueryString(filters)}`
      ),
    enabled: enabled && !!jobId,
  });
}

// Excludes this candidate from future searches for this job (job_id set) or every job at this
// company (job_id null). Invalidates the search results for the job just passed on so the card
// disappears immediately.
export function usePassCandidate(jobId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ callsign, reason }: { callsign: string; reason?: PassReason }) =>
      apiClient.post<void>(`/matches/mine/candidates/${callsign}/pass`, {
        job_id: jobId ?? null,
        reason: reason ?? null,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["matches", "candidates", jobId] });
    },
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
