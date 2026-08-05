"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { fetchOrNull } from "@/lib/queries/helpers";
import type { SanitizedProfile } from "@/lib/types";

export function useSanitizedProfile(candidateId: string | undefined) {
  return useQuery({
    queryKey: ["sanitized-profile", candidateId],
    queryFn: () =>
      fetchOrNull(() =>
        apiClient.get<SanitizedProfile>(`/candidates/${candidateId}/sanitized-profile`)
      ),
    enabled: !!candidateId,
  });
}

export function useSanitizeCandidate(candidateId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<SanitizedProfile>(`/candidates/${candidateId}/sanitize`),
    onSuccess: (data) => {
      queryClient.setQueryData(["sanitized-profile", candidateId], data);
    },
  });
}
