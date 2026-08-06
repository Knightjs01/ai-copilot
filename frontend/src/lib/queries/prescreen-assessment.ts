"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { invalidateProjectAnalytics } from "@/lib/queries/analytics";
import { fetchOrNull } from "@/lib/queries/helpers";
import type { PrescreenAssessment } from "@/lib/types";

export function usePrescreenAssessment(candidateId: string | undefined) {
  return useQuery({
    queryKey: ["prescreen-assessment", candidateId],
    queryFn: () =>
      fetchOrNull(() =>
        apiClient.get<PrescreenAssessment>(`/candidates/${candidateId}/prescreen-assessment`)
      ),
    enabled: !!candidateId,
  });
}

export function useGeneratePrescreenAssessment(candidateId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<PrescreenAssessment>(`/candidates/${candidateId}/prescreen-assessment`),
    onSuccess: (data) => {
      queryClient.setQueryData(["prescreen-assessment", candidateId], data);
      invalidateProjectAnalytics(queryClient);
    },
  });
}

export function useGenerateHandoffRecommendations(candidateId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      apiClient.post<PrescreenAssessment>(
        `/candidates/${candidateId}/prescreen-assessment/handoff`
      ),
    onSuccess: (data) => {
      queryClient.setQueryData(["prescreen-assessment", candidateId], data);
    },
  });
}
