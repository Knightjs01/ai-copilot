"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { fetchOrNull } from "@/lib/queries/helpers";
import type { HiringBlueprint } from "@/lib/types";

export function useHiringBlueprint(projectId: string | undefined) {
  return useQuery({
    queryKey: ["hiring-blueprint", projectId],
    queryFn: () =>
      fetchOrNull(() => apiClient.get<HiringBlueprint>(`/projects/${projectId}/hiring-blueprint`)),
    enabled: !!projectId,
  });
}

export function useGenerateHiringBlueprint(projectId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<HiringBlueprint>(`/projects/${projectId}/hiring-blueprint`),
    onSuccess: (data) => {
      queryClient.setQueryData(["hiring-blueprint", projectId], data);
    },
  });
}
