"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { platformAdminApiClient } from "@/lib/platform-admin-api-client";
import type {
  AccessRequestStats,
  AdminCompanySummary,
  CompanyAccessRequest,
  CompanyProfile,
  PlatformAdminAuditLogEntry,
} from "@/lib/types";

export function useAccessRequests(status: string = "pending") {
  return useQuery({
    queryKey: ["platform-admin", "requests", status],
    queryFn: () =>
      platformAdminApiClient.get<CompanyAccessRequest[]>(
        `/company-access/requests?status=${status}`
      ),
  });
}

export function useDashboardStats() {
  return useQuery({
    queryKey: ["platform-admin", "stats"],
    queryFn: () => platformAdminApiClient.get<AccessRequestStats>("/company-access/stats"),
  });
}

export function useAuditLog() {
  return useQuery({
    queryKey: ["platform-admin", "audit-log"],
    queryFn: () =>
      platformAdminApiClient.get<PlatformAdminAuditLogEntry[]>("/company-access/audit-log"),
  });
}

export function useAllCompanies() {
  return useQuery({
    queryKey: ["platform-admin", "companies"],
    queryFn: () => platformAdminApiClient.get<AdminCompanySummary[]>("/companies"),
  });
}

export function useProfileReviews() {
  return useQuery({
    queryKey: ["platform-admin", "companies", "profile-reviews"],
    queryFn: () =>
      platformAdminApiClient.get<AdminCompanySummary[]>("/companies?profile_status=pending_review"),
  });
}

function invalidateRequestQueues(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.invalidateQueries({ queryKey: ["platform-admin", "requests"] });
  void queryClient.invalidateQueries({ queryKey: ["platform-admin", "stats"] });
  void queryClient.invalidateQueries({ queryKey: ["platform-admin", "audit-log"] });
}

export function useApproveAccessRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (requestId: string) =>
      platformAdminApiClient.post<CompanyAccessRequest>(
        `/company-access/requests/${requestId}/approve`
      ),
    onSuccess: () => invalidateRequestQueues(queryClient),
  });
}

export function useRejectAccessRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ requestId, reason }: { requestId: string; reason?: string }) =>
      platformAdminApiClient.post<CompanyAccessRequest>(
        `/company-access/requests/${requestId}/reject`,
        { reason }
      ),
    onSuccess: () => invalidateRequestQueues(queryClient),
  });
}

export function useRequestMoreInfo() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ requestId, message }: { requestId: string; message: string }) =>
      platformAdminApiClient.post<CompanyAccessRequest>(
        `/company-access/requests/${requestId}/request-info`,
        { message }
      ),
    onSuccess: () => invalidateRequestQueues(queryClient),
  });
}

function invalidateCompanyQueues(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.invalidateQueries({ queryKey: ["platform-admin", "companies"] });
  void queryClient.invalidateQueries({ queryKey: ["platform-admin", "stats"] });
  void queryClient.invalidateQueries({ queryKey: ["platform-admin", "audit-log"] });
}

export function useAdminProfilePreview(companyId: string | undefined) {
  return useQuery({
    queryKey: ["platform-admin", "companies", companyId, "profile-preview"],
    queryFn: () =>
      platformAdminApiClient.get<CompanyProfile>(
        `/companies/${companyId}/profile-review/preview`
      ),
    enabled: !!companyId,
  });
}

export function useApproveProfileReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (companyId: string) =>
      platformAdminApiClient.post(`/companies/${companyId}/profile-review/approve`),
    onSuccess: () => invalidateCompanyQueues(queryClient),
  });
}

export function useRejectProfileReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ companyId, reason }: { companyId: string; reason?: string }) =>
      platformAdminApiClient.post(`/companies/${companyId}/profile-review/reject`, { reason }),
    onSuccess: () => invalidateCompanyQueues(queryClient),
  });
}

export function useSuspendCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (companyId: string) =>
      platformAdminApiClient.post(`/companies/${companyId}/suspend`),
    onSuccess: () => invalidateCompanyQueues(queryClient),
  });
}

export function useReactivateCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (companyId: string) =>
      platformAdminApiClient.post(`/companies/${companyId}/reactivate`),
    onSuccess: () => invalidateCompanyQueues(queryClient),
  });
}
