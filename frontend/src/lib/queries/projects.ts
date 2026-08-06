"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { Project, ProjectStatus } from "@/lib/types";

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

export function useUploadJd(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return apiClient.postForm<Project>(`/projects/${projectId}/jd`, formData);
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["projects", projectId], data);
    },
  });
}
