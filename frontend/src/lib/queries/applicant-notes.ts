"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { ApplicantNote } from "@/lib/types";

export function useApplicantNotes(jobId: string | undefined, applicationId: string | undefined) {
  return useQuery({
    queryKey: ["applicant-notes", jobId, applicationId],
    queryFn: () =>
      apiClient.get<ApplicantNote[]>(`/shadow-jobs/mine/${jobId}/applicants/${applicationId}/notes`),
    enabled: !!jobId && !!applicationId,
  });
}

export function useCreateApplicantNote(jobId: string, applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) =>
      apiClient.post<ApplicantNote>(`/shadow-jobs/mine/${jobId}/applicants/${applicationId}/notes`, {
        body,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["applicant-notes", jobId, applicationId],
      });
    },
  });
}
