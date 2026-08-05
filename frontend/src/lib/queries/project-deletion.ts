"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";

interface BurnProjectResponse {
  candidate_count: number;
}

export function useBurnProject(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<BurnProjectResponse>(`/projects/${projectId}/burn`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.removeQueries({ queryKey: ["projects", projectId] });
    },
  });
}
