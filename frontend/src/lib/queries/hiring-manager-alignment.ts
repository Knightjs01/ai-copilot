"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { fetchOrNull } from "@/lib/queries/helpers";
import type { HiringManagerAlignment } from "@/lib/types";

export function useHiringManagerAlignment(projectId: string | undefined) {
  return useQuery({
    queryKey: ["hiring-manager-alignment", projectId],
    queryFn: () =>
      fetchOrNull(() =>
        apiClient.get<HiringManagerAlignment>(`/projects/${projectId}/hiring-manager-alignment`)
      ),
    enabled: !!projectId,
  });
}

export function useSubmitHiringManagerAlignment(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (topRequirements: string[]) =>
      apiClient.put<HiringManagerAlignment>(`/projects/${projectId}/hiring-manager-alignment`, {
        top_requirements: topRequirements,
      }),
    onSuccess: (data) => {
      queryClient.setQueryData(["hiring-manager-alignment", projectId], data);
    },
  });
}
