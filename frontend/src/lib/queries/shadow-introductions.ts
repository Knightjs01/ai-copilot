"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { candidateApiClient } from "@/lib/candidate-api-client";
import type { CandidateIntroductionRequestRead, IntroductionRequestRead } from "@/lib/types";

// --- Company side -----------------------------------------------------------------------------

export function useRequestIntroduction(jobId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ callsign, message }: { callsign: string; message?: string }) =>
      apiClient.post<IntroductionRequestRead>(
        `/introductions/mine/${jobId}/candidates/${callsign}/request`,
        { message: message || null }
      ),
    onSuccess: () => {
      // The candidate's relationship badge (introduction_pending) is computed inside the search
      // response itself, so refetching the search results is what makes it update immediately.
      void queryClient.invalidateQueries({ queryKey: ["matches", "candidates", jobId] });
    },
  });
}

export function useCompanyIntroductionRequests(jobId: string | undefined) {
  return useQuery({
    queryKey: ["introductions", "mine", jobId],
    queryFn: () => apiClient.get<IntroductionRequestRead[]>(`/introductions/mine/${jobId}`),
    enabled: !!jobId,
  });
}

// --- Candidate side ---------------------------------------------------------------------------

const POLL_INTERVAL_MS = 20000;

export function useMyIntroductionRequests() {
  return useQuery({
    queryKey: ["introductions", "my-requests"],
    queryFn: () =>
      candidateApiClient.get<CandidateIntroductionRequestRead[]>("/introductions/my-requests"),
    refetchInterval: POLL_INTERVAL_MS,
  });
}

export function useRespondToIntroductionRequest(requestId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (approve: boolean) =>
      candidateApiClient.post<CandidateIntroductionRequestRead>(
        `/introductions/requests/me/${requestId}/respond`,
        { approve }
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["introductions", "my-requests"] });
    },
  });
}
