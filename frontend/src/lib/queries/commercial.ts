"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { platformAdminApiClient } from "@/lib/platform-admin-api-client";
import type { Company, CommercialPlan, CompanyCommercialSummary } from "@/lib/types";

export function useCommercialSummary() {
  return useQuery({
    queryKey: ["commercial", "summary"],
    queryFn: () => apiClient.get<CompanyCommercialSummary>("/companies/me/commercial-summary"),
  });
}

export function useCommercialPlans() {
  return useQuery({
    queryKey: ["platform-admin", "commercial", "plans"],
    queryFn: () =>
      platformAdminApiClient.get<CommercialPlan[]>("/platform-admin/commercial/plans"),
  });
}

export function useUpdateCompanyCommercial() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: {
      companyId: string;
      planCode?: string;
      activeRoleLimitOverride?: number | null;
      reason?: string;
    }) =>
      platformAdminApiClient.post<Company>(
        `/platform-admin/commercial/companies/${input.companyId}`,
        {
          plan_code: input.planCode,
          active_role_limit_override: input.activeRoleLimitOverride,
          reason: input.reason,
        }
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["platform-admin", "companies"] });
      void queryClient.invalidateQueries({ queryKey: ["platform-admin", "audit-log"] });
    },
  });
}
