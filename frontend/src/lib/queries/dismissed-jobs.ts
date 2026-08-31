"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { candidateApiClient } from "@/lib/candidate-api-client";

const DISMISSED_JOBS_KEY = ["dismissed-jobs"] as const;

export function useDismissedJobIds(options?: { enabled?: boolean }) {
  const { enabled = true } = options ?? {};
  return useQuery({
    queryKey: DISMISSED_JOBS_KEY,
    queryFn: () => candidateApiClient.get<string[]>("/dismissed-jobs"),
    enabled,
  });
}

export function useDismissJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (shadowJobId: string) =>
      candidateApiClient.post<void>("/dismissed-jobs", { shadow_job_id: shadowJobId }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: DISMISSED_JOBS_KEY });
    },
  });
}

export function useUndismissJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (shadowJobId: string) =>
      candidateApiClient.delete<void>(`/dismissed-jobs/${shadowJobId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: DISMISSED_JOBS_KEY });
    },
  });
}
