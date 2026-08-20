"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { candidateApiClient } from "@/lib/candidate-api-client";
import type { MessageThread, MessageThreadSummary } from "@/lib/types";

// Candidate-side messaging (candidate auth, candidateApiClient). See lib/queries/shadow-jobs.ts
// for the company-side equivalents (useApplicantMessages/useSendCompanyMessage).

const POLL_INTERVAL_MS = 20000;

// `enabled` matters here specifically because this hook is also read from ShadowTopNav/
// ShadowMobileNav (for the unread badge), both mounted on the public board where a logged-out
// visitor has no candidate session -- without it, every anonymous page view would fire a doomed,
// unauthenticated request. Candidate-only pages don't need to pass it (always true there).
export function useMyMessageThreads(options?: { enabled?: boolean }) {
  const { enabled = true } = options ?? {};
  return useQuery({
    queryKey: ["messages", "threads"],
    queryFn: () => candidateApiClient.get<MessageThreadSummary[]>("/messages"),
    refetchInterval: POLL_INTERVAL_MS,
    enabled,
  });
}

export function useMessageThread(applicationId: string | undefined) {
  return useQuery({
    queryKey: ["messages", "thread", applicationId],
    queryFn: () => candidateApiClient.get<MessageThread>(`/messages/${applicationId}`),
    enabled: !!applicationId,
    refetchInterval: POLL_INTERVAL_MS,
  });
}

export function useSendCandidateMessage(applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) =>
      candidateApiClient.post<MessageThread>(`/messages/${applicationId}`, { body }),
    onSuccess: (data) => {
      queryClient.setQueryData(["messages", "thread", applicationId], data);
      void queryClient.invalidateQueries({ queryKey: ["messages", "threads"] });
    },
  });
}
