"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { PurgeCertificate } from "@/lib/types";

interface BurnProjectResponse {
  candidate_count: number;
  certificate: PurgeCertificate;
}

export function useBurnProject(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (stepUpToken: string) =>
      apiClient.post<BurnProjectResponse>(`/projects/${projectId}/burn`, undefined, stepUpToken),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["projects"] });
      queryClient.removeQueries({ queryKey: ["projects", projectId] });
    },
  });
}
