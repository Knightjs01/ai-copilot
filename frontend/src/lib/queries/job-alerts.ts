"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { candidateApiClient } from "@/lib/candidate-api-client";
import type { JobAlert, JobAlertCreateInput, JobAlertUpdateInput } from "@/lib/types";

export function useJobAlerts(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: ["job-alerts", "mine"],
    queryFn: () => candidateApiClient.get<JobAlert[]>("/job-alerts"),
    enabled: options?.enabled ?? true,
  });
}

export function useCreateJobAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: JobAlertCreateInput) =>
      candidateApiClient.post<JobAlert>("/job-alerts", input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["job-alerts", "mine"] });
    },
  });
}

export function useUpdateJobAlert(alertId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: JobAlertUpdateInput) =>
      candidateApiClient.patch<JobAlert>(`/job-alerts/${alertId}`, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["job-alerts", "mine"] });
    },
  });
}

export function useDeleteJobAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (alertId: string) => candidateApiClient.delete<void>(`/job-alerts/${alertId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["job-alerts", "mine"] });
    },
  });
}
