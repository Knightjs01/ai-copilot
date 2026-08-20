"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { candidateApiClient } from "@/lib/candidate-api-client";
import type { SavedShadowJob } from "@/lib/types";

const SAVED_JOBS_KEY = ["saved-jobs"] as const;

// `enabled` matters here specifically because this hook is also called from the public job
// board, which a logged-out visitor can reach -- without it, every anonymous board view would
// fire a doomed, unauthenticated request. Candidate-only pages under (candidate)/ don't need to
// pass it (always true there), same as every other candidate query hook in this codebase.
export function useSavedJobs(options?: { collectionName?: string; enabled?: boolean }) {
  const { collectionName, enabled = true } = options ?? {};
  return useQuery({
    queryKey: [...SAVED_JOBS_KEY, collectionName ?? "all"],
    queryFn: () =>
      candidateApiClient.get<SavedShadowJob[]>(
        collectionName
          ? `/saved-jobs?collection_name=${encodeURIComponent(collectionName)}`
          : "/saved-jobs"
      ),
    enabled,
  });
}

export function useSaveJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { shadowJobId: string; collectionName?: string }) =>
      candidateApiClient.post<SavedShadowJob>("/saved-jobs", {
        shadow_job_id: input.shadowJobId,
        collection_name: input.collectionName ?? null,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: SAVED_JOBS_KEY });
    },
  });
}

export function useUnsaveJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (shadowJobId: string) =>
      candidateApiClient.delete<void>(`/saved-jobs/${shadowJobId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: SAVED_JOBS_KEY });
    },
  });
}

export function useUpdateSavedJobCollection() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { shadowJobId: string; collectionName: string | null }) =>
      candidateApiClient.patch<SavedShadowJob>(`/saved-jobs/${input.shadowJobId}`, {
        collection_name: input.collectionName,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: SAVED_JOBS_KEY });
    },
  });
}
