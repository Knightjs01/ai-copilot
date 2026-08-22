"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { fetchOrNull } from "@/lib/queries/helpers";
import type { InterviewKit } from "@/lib/types";

export function useInterviewKit(projectId: string | undefined) {
  return useQuery({
    queryKey: ["interview-kit", projectId],
    queryFn: () =>
      fetchOrNull(() => apiClient.get<InterviewKit>(`/projects/${projectId}/interview-kit`)),
    enabled: !!projectId,
  });
}

export function useGenerateInterviewKit(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<InterviewKit>(`/projects/${projectId}/interview-kit`),
    onSuccess: (data) => {
      queryClient.setQueryData(["interview-kit", projectId], data);
    },
  });
}

export function useUpdateInterviewKitSelection(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (includedFlags: boolean[]) =>
      apiClient.patch<InterviewKit>(`/projects/${projectId}/interview-kit/selection`, {
        included_flags: includedFlags,
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["interview-kit", projectId], data);
    },
  });
}
