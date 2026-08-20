"use client";

import { useQuery } from "@tanstack/react-query";

import { candidateApiClient } from "@/lib/candidate-api-client";
import type { CandidateInterviewSummary } from "@/lib/types";

// Candidate-side interviews (candidate auth, candidateApiClient), view-only. See
// lib/queries/shadow-jobs.ts for the company-side scheduling hooks.
//
// `enabled` matters here because this hook is also read from the command palette's dynamic
// group via cache reads, not fetched there directly -- but any future nav consumer would need
// the same guard as useMyMessageThreads, so it's included for consistency even though nothing
// calls it with `enabled: false` yet.
export function useMyInterviews(options?: { enabled?: boolean }) {
  const { enabled = true } = options ?? {};
  return useQuery({
    queryKey: ["interviews", "mine"],
    queryFn: () => candidateApiClient.get<CandidateInterviewSummary[]>("/interviews"),
    enabled,
  });
}
