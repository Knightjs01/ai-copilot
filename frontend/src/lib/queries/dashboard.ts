"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { DashboardStats } from "@/lib/types";

export function useDashboardStats() {
  return useQuery({
    queryKey: ["dashboard"],
    queryFn: () => apiClient.get<DashboardStats>("/dashboard"),
  });
}

// Scoped to one role -- powers Role Health. Unlike the company-wide call, the backend does not
// truncate action_items here (see backend/app/modules/dashboard/service.py), so this always
// reflects the role's real, complete gap count.
export function useProjectDashboardStats(projectId: string | undefined) {
  return useQuery({
    queryKey: ["dashboard", { projectId }],
    queryFn: () => apiClient.get<DashboardStats>(`/dashboard?project_id=${projectId}`),
    enabled: !!projectId,
  });
}
