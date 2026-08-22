"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { JdUploadResult, Project, ProjectActivityEntry, ProjectStatus } from "@/lib/types";

export function useProjects() {
  return useQuery({
    queryKey: ["projects"],
    queryFn: () => apiClient.get<Project[]>("/projects"),
  });
}

export function useProject(projectId: string | undefined) {
  return useQuery({
    queryKey: ["projects", projectId],
    queryFn: () => apiClient.get<Project>(`/projects/${projectId}`),
    enabled: !!projectId,
  });
}

interface CreateProjectInput {
  title: string;
  department?: string;
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateProjectInput) => apiClient.post<Project>("/projects", input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

interface UpdateProjectInput {
  title?: string;
  department?: string;
  status?: ProjectStatus;
  role_brief?: string;
  hiring_manager_id?: string | null;
  // Tri-state: omit the key to leave the field alone, include it as `null` to explicitly clear
  // it (e.g. the recruiter clears a wrong AI-suggested value) -- matches the backend's
  // model_fields_set-driven handling for these four fields specifically.
  seniority?: string | null;
  location?: string | null;
  salary_min?: number | null;
  salary_max?: number | null;
}

export function useUpdateProject(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: UpdateProjectInput) =>
      apiClient.patch<Project>(`/projects/${projectId}`, input),
    onSuccess: (data) => {
      queryClient.setQueryData(["projects", projectId], data);
      void queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}

// Returns a preview only -- nothing is saved server-side, so this deliberately does NOT touch
// the ["projects", projectId] query cache. The caller holds the preview in local state until an
// explicit useUpdateProject call persists it.
export function useUploadJd(projectId: string) {
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return apiClient.postForm<JdUploadResult>(`/projects/${projectId}/jd`, formData);
    },
  });
}

export function usePostToShadow(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<Project>(`/projects/${projectId}/post-to-shadow`),
    onSuccess: (data) => {
      queryClient.setQueryData(["projects", projectId], data);
      void queryClient.invalidateQueries({ queryKey: ["projects"] });
      void queryClient.invalidateQueries({ queryKey: ["shadow-jobs"] });
    },
  });
}

export function useProjectActivity(projectId: string | undefined) {
  return useQuery({
    queryKey: ["projects", projectId, "activity"],
    queryFn: () => apiClient.get<ProjectActivityEntry[]>(`/projects/${projectId}/activity`),
    enabled: !!projectId,
  });
}

export function useSaveAsDraft(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<Project>(`/projects/${projectId}/save-as-draft`),
    onSuccess: (data) => {
      queryClient.setQueryData(["projects", projectId], data);
      void queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });
}
