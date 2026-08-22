"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { invalidateProjectAnalytics } from "@/lib/queries/analytics";
import type {
  Candidate,
  CandidateSource,
  CandidateStatus,
  NoticePeriod,
  PrescreenOutcome,
} from "@/lib/types";

export function useCandidates(projectId: string | undefined) {
  return useQuery({
    queryKey: ["candidates", { projectId }],
    queryFn: () => apiClient.get<Candidate[]>(`/candidates?project_id=${projectId}&limit=500`),
    enabled: !!projectId,
  });
}

// Cross-project — powers the Pipeline view. Same real GET /candidates endpoint with project_id
// omitted; the backend already returns every candidate across accessible projects for both
// org-wide and project-scoped actors (see backend/app/modules/candidates/repository.py).
export function useAllCandidates() {
  return useQuery({
    queryKey: ["candidates", "all"],
    queryFn: () => apiClient.get<Candidate[]>("/candidates?limit=500"),
  });
}

export function useCandidate(candidateId: string | undefined) {
  return useQuery({
    queryKey: ["candidates", candidateId],
    queryFn: () => apiClient.get<Candidate>(`/candidates/${candidateId}`),
    enabled: !!candidateId,
  });
}

interface UpdateCandidateInput {
  source?: CandidateSource;
  status?: CandidateStatus;
  interview_scheduled_at?: string;
  prescreen_outcome?: PrescreenOutcome;
  prescreen_notes?: string;
  expected_salary?: number;
  agency_name?: string;
  notice_period?: NoticePeriod;
}

export function useUpdateCandidate(candidateId: string, projectId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: UpdateCandidateInput) =>
      apiClient.patch<Candidate>(`/candidates/${candidateId}`, input),
    onSuccess: (data) => {
      queryClient.setQueryData(["candidates", candidateId], data);
      if (projectId) {
        void queryClient.invalidateQueries({ queryKey: ["candidates", { projectId }] });
      }
      invalidateProjectAnalytics(queryClient);
    },
  });
}

export function useUploadResume(candidateId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return apiClient.postForm<Candidate>(`/candidates/${candidateId}/resume`, formData);
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["candidates", candidateId], data);
    },
  });
}
