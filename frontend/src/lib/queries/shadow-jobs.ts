"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { candidateApiClient } from "@/lib/candidate-api-client";
import { fetchOrNull } from "@/lib/queries/helpers";
import type {
  ShadowApplication,
  ShadowJob,
  ShadowJobBoardListing,
  ShadowJobCreateInput,
  ShadowJobUpdateInput,
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
