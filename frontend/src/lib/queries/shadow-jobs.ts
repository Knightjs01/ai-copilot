"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { candidateApiClient } from "@/lib/candidate-api-client";
import { fetchOrNull } from "@/lib/queries/helpers";
import type {
  Interview,
  MessageThread,
  ShadowApplication,
  ShadowJob,
  ShadowJobBoardListing,
  ShadowJobCreateInput,
  ShadowJobUpdateInput,
  ShadowPipelineStage,
  ShadowProfile,
} from "@/lib/types";

// --- Company side (company auth, apiClient) --------------------------------------------------

export function useMyShadowJobs() {
  return useQuery({
    queryKey: ["shadow-jobs", "mine"],
    queryFn: () => apiClient.get<ShadowJob[]>("/shadow-jobs/mine"),
  });
}

export function useMyShadowJob(jobId: string | undefined) {
  return useQuery({
    queryKey: ["shadow-jobs", "mine", jobId],
    queryFn: () => apiClient.get<ShadowJob>(`/shadow-jobs/mine/${jobId}`),
    enabled: !!jobId,
  });
}

export function useCreateShadowJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ShadowJobCreateInput) => apiClient.post<ShadowJob>("/shadow-jobs", input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "mine"] });
    },
  });
}

export function useUpdateShadowJob(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ShadowJobUpdateInput) =>
      apiClient.patch<ShadowJob>(`/shadow-jobs/mine/${jobId}`, input),
    onSuccess: (data) => {
      queryClient.setQueryData(["shadow-jobs", "mine", jobId], data);
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "mine"] });
    },
  });
}

export function usePublishShadowJob(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<ShadowJob>(`/shadow-jobs/mine/${jobId}/publish`),
    onSuccess: (data) => {
      queryClient.setQueryData(["shadow-jobs", "mine", jobId], data);
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "mine"] });
    },
  });
}

export function useCloseShadowJob(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<ShadowJob>(`/shadow-jobs/mine/${jobId}/close`),
    onSuccess: (data) => {
      queryClient.setQueryData(["shadow-jobs", "mine", jobId], data);
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "mine"] });
    },
  });
}

export function useShadowJobApplicants(jobId: string | undefined) {
  return useQuery({
    queryKey: ["shadow-jobs", "applicants", jobId],
    queryFn: () => apiClient.get<ShadowProfile[]>(`/shadow-jobs/mine/${jobId}/applicants`),
    enabled: !!jobId,
  });
}

export function useProjectShadowJob(projectId: string | undefined) {
  return useQuery({
    queryKey: ["shadow-jobs", "project", projectId],
    queryFn: () =>
      fetchOrNull(() => apiClient.get<ShadowJob>(`/projects/${projectId}/shadow-job`)),
    enabled: !!projectId,
  });
}

export function useUpdateApplicantPipelineStage(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      applicationId,
      pipelineStage,
    }: {
      applicationId: string;
      pipelineStage: ShadowPipelineStage;
    }) =>
      apiClient.patch<ShadowProfile>(`/shadow-jobs/mine/${jobId}/applicants/${applicationId}`, {
        pipeline_stage: pipelineStage,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applicants", jobId] });
    },
  });
}

export function useApplicantMessages(jobId: string | undefined, applicationId: string | undefined) {
  return useQuery({
    queryKey: ["messages", "applicant-thread", jobId, applicationId],
    queryFn: () =>
      apiClient.get<MessageThread>(`/messages/mine/${jobId}/applicants/${applicationId}`),
    enabled: !!jobId && !!applicationId,
    refetchInterval: 20000,
  });
}

export function useSendCompanyMessage(jobId: string, applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) =>
      apiClient.post<MessageThread>(`/messages/mine/${jobId}/applicants/${applicationId}`, {
        body,
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["messages", "applicant-thread", jobId, applicationId], data);
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applicants", jobId] });
    },
  });
}

export function useApplicantInterviews(jobId: string | undefined, applicationId: string | undefined) {
  return useQuery({
    queryKey: ["interviews", "applicant", jobId, applicationId],
    queryFn: () =>
      apiClient.get<Interview[]>(`/interviews/mine/${jobId}/applicants/${applicationId}`),
    enabled: !!jobId && !!applicationId,
  });
}

interface ScheduleInterviewInput {
  scheduled_at: string;
  location?: string | null;
  meeting_link?: string | null;
  interviewer_user_ids?: string[];
}

export function useScheduleInterview(jobId: string, applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ScheduleInterviewInput) =>
      apiClient.post<Interview>(`/interviews/mine/${jobId}/applicants/${applicationId}`, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["interviews", "applicant", jobId, applicationId],
      });
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applicants", jobId] });
    },
  });
}

export function useUpdateInterview(jobId: string, applicationId: string, interviewId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ScheduleInterviewInput) =>
      apiClient.patch<Interview>(
        `/interviews/mine/${jobId}/applicants/${applicationId}/${interviewId}`,
        input
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["interviews", "applicant", jobId, applicationId],
      });
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applicants", jobId] });
    },
  });
}

export function useCancelInterview(jobId: string, applicationId: string, interviewId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<Interview>(
        `/interviews/mine/${jobId}/applicants/${applicationId}/${interviewId}/cancel`
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["interviews", "applicant", jobId, applicationId],
      });
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applicants", jobId] });
    },
  });
}

export function useCompleteInterview(jobId: string, applicationId: string, interviewId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<Interview>(
        `/interviews/mine/${jobId}/applicants/${applicationId}/${interviewId}/complete`
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ["interviews", "applicant", jobId, applicationId],
      });
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applicants", jobId] });
    },
  });
}

// --- Public job board (no auth required) ------------------------------------------------------

export interface ShadowBoardFilters {
  seniority?: string;
  remote_preference?: string;
  employment_type?: string;
  location?: string;
}

function boardQueryString(filters: ShadowBoardFilters): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value) params.set(key, value);
  }
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

export function useShadowBoard(filters: ShadowBoardFilters = {}) {
  return useQuery({
    queryKey: ["shadow-jobs", "board", filters],
    queryFn: () =>
      apiClient.get<ShadowJobBoardListing[]>(`/shadow-jobs/board${boardQueryString(filters)}`),
  });
}

export function useShadowBoardJob(jobId: string | undefined) {
  return useQuery({
    queryKey: ["shadow-jobs", "board", jobId],
    queryFn: () => apiClient.get<ShadowJobBoardListing>(`/shadow-jobs/board/${jobId}`),
    enabled: !!jobId,
  });
}

// --- Candidate side (candidate auth, candidateApiClient) ---------------------------------------

export function useApplyToShadowJob(jobId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      candidateApiClient.post<ShadowApplication>(`/shadow-jobs/board/${jobId}/apply`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applications", "me"] });
    },
  });
}

export function useMyApplications() {
  return useQuery({
    queryKey: ["shadow-jobs", "applications", "me"],
    queryFn: () => candidateApiClient.get<ShadowApplication[]>("/shadow-jobs/applications/me"),
  });
}

export function useMyApplication(applicationId: string | undefined) {
  return useQuery({
    queryKey: ["shadow-jobs", "applications", "me", applicationId],
    queryFn: () =>
      fetchOrNull(() =>
        candidateApiClient.get<ShadowApplication>(`/shadow-jobs/applications/me/${applicationId}`)
      ),
    enabled: !!applicationId,
  });
}

export function useWithdrawApplication(applicationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      candidateApiClient.post<ShadowApplication>(
        `/shadow-jobs/applications/me/${applicationId}/withdraw`
      ),
    onSuccess: (data) => {
      queryClient.setQueryData(["shadow-jobs", "applications", "me", applicationId], data);
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs", "applications", "me"] });
    },
  });
}
