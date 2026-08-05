"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { fetchOrNull } from "@/lib/queries/helpers";
import type { IntelligencePack } from "@/lib/types";

export function useIntelligencePack(candidateId: string | undefined) {
  return useQuery({
    queryKey: ["intelligence-pack", candidateId],
    queryFn: () =>
      fetchOrNull(() =>
        apiClient.get<IntelligencePack>(`/candidates/${candidateId}/intelligence-pack`)
      ),
    enabled: !!candidateId,
  });
}

export function useGenerateIntelligencePack(candidateId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<IntelligencePack>(`/candidates/${candidateId}/intelligence-pack`),
    onSuccess: (data) => {
      queryClient.setQueryData(["intelligence-pack", candidateId], data);
    },
  });
}
