"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { CandidateSearchResult } from "@/lib/types";

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
