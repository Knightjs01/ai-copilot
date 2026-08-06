"use client";

import { useQuery, type QueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { ProjectAnalytics } from "@/lib/types";

export function useProjectAnalytics(projectId: string | undefined) {
  return useQuery({
    queryKey: ["projects", projectId, "analytics"],
    queryFn: () => apiClient.get<ProjectAnalytics>(`/projects/${projectId}/analytics`),
    enabled: !!projectId,
  });
}

// Called from every mutation that can change what the snapshot shows (candidate created/
// updated, assessment generated) — a predicate match rather than a specific projectId since
// several of those call sites (e.g. prescreen-assessment mutations) only have a candidateId in
// scope, not the project it belongs to.
export function invalidateProjectAnalytics(queryClient: QueryClient): void {
  void queryClient.invalidateQueries({
    predicate: (query) => query.queryKey[0] === "projects" && query.queryKey[2] === "analytics",
  });
}
