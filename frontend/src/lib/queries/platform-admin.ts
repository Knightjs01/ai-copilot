"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { platformAdminApiClient } from "@/lib/platform-admin-api-client";
import type {
  AccessRequestStats,
  ActionQueueItem,
  AdminCompanyDetail,
  AdminCompanySummary,
  AdminCompanyUser,
  AdminShadowJob,
  AdminShadowJobDetail,
  AuditEntry,
  CompanyAccessRequest,
  CompanyProfile,
  MfaEnableResponse,
  MfaSetupResponse,
  PlatformAdminAuditLogEntry,
  PlatformAdminSummary,
} from "@/lib/types";

export function usePlatformAdminMfaSetup() {
  return useMutation({
    mutationFn: () => platformAdminApiClient.post<MfaSetupResponse>("/platform-admin/mfa/setup"),
  });
}

export function usePlatformAdminMfaEnable() {
  return useMutation({
    mutationFn: (input: { secret: string; code: string }) =>
      platformAdminApiClient.post<MfaEnableResponse>("/platform-admin/mfa/enable", input),
  });
}

export function usePlatformAdminMfaDisable() {
  return useMutation({
    mutationFn: (password: string) =>
      platformAdminApiClient.post<void>("/platform-admin/mfa/disable", { password }),
  });
}

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

export function useActionQueue() {
  return useQuery({
    queryKey: ["platform-admin", "action-queue"],
    queryFn: () => platformAdminApiClient.get<ActionQueueItem[]>("/platform-admin/action-queue"),
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

export function useCompanyDetail(companyId: string) {
  return useQuery({
    queryKey: ["platform-admin", "companies", companyId],
    queryFn: () =>
      platformAdminApiClient.get<AdminCompanyDetail>(`/companies/${companyId}/detail`),
    enabled: !!companyId,
  });
}

export function useCompanyUsers(companyId: string) {
  return useQuery({
    queryKey: ["platform-admin", "companies", companyId, "users"],
    queryFn: () =>
      platformAdminApiClient.get<AdminCompanyUser[]>(`/companies/${companyId}/users`),
    enabled: !!companyId,
  });
}

export function useCompanyActivity(companyId: string) {
  return useQuery({
    queryKey: ["platform-admin", "companies", companyId, "activity"],
    queryFn: () =>
      platformAdminApiClient.get<AuditEntry[]>(`/companies/${companyId}/activity`),
    enabled: !!companyId,
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

export function useVerifyCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (companyId: string) => platformAdminApiClient.post(`/companies/${companyId}/verify`),
    onSuccess: () => invalidateCompanyQueues(queryClient),
  });
}

export function useUnverifyCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (companyId: string) =>
      platformAdminApiClient.post(`/companies/${companyId}/unverify`),
    onSuccess: () => invalidateCompanyQueues(queryClient),
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (input: { currentPassword: string; newPassword: string }) =>
      platformAdminApiClient.post<void>("/platform-admin/change-password", {
        current_password: input.currentPassword,
        new_password: input.newPassword,
      }),
  });
}

export function useAdminJobs(status?: string, companyId?: string) {
  return useQuery({
    queryKey: ["platform-admin", "jobs", "list", status ?? "all", companyId ?? "all"],
    queryFn: () => {
      const params = new URLSearchParams();
      if (status && status !== "all") params.set("status", status);
      if (companyId) params.set("company_id", companyId);
      const query = params.toString();
      return platformAdminApiClient.get<AdminShadowJob[]>(
        `/platform-admin/jobs${query ? `?${query}` : ""}`
      );
    },
  });
}

export function useAdminJob(jobId: string) {
  return useQuery({
    queryKey: ["platform-admin", "jobs", jobId],
    queryFn: () =>
      platformAdminApiClient.get<AdminShadowJobDetail>(`/platform-admin/jobs/${jobId}`),
    enabled: !!jobId,
  });
}

function invalidateJobQueues(queryClient: ReturnType<typeof useQueryClient>) {
  void queryClient.invalidateQueries({ queryKey: ["platform-admin", "jobs"] });
  void queryClient.invalidateQueries({ queryKey: ["platform-admin", "audit-log"] });
}

export function useApproveJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (jobId: string) =>
      platformAdminApiClient.post<AdminShadowJob>(`/platform-admin/jobs/${jobId}/approve`),
    onSuccess: () => invalidateJobQueues(queryClient),
  });
}

export function useRejectJob() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ jobId, reason }: { jobId: string; reason?: string }) =>
      platformAdminApiClient.post<AdminShadowJob>(`/platform-admin/jobs/${jobId}/reject`, {
        reason,
      }),
    onSuccess: () => invalidateJobQueues(queryClient),
  });
}

export function useAdmins() {
  return useQuery({
    queryKey: ["platform-admin", "admins"],
    queryFn: () => platformAdminApiClient.get<PlatformAdminSummary[]>("/platform-admin/admins"),
  });
}

export function useCreateAdmin() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { fullName: string; email: string; password: string; role: string }) =>
      platformAdminApiClient.post<PlatformAdminSummary>("/platform-admin/admins", {
        full_name: input.fullName,
        email: input.email,
        password: input.password,
        role: input.role,
      }),
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: ["platform-admin", "admins"] }),
  });
}

export function usePurgeAllData() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { confirmationPhrase: string; stepUpToken: string }) =>
      platformAdminApiClient.post<{ tables_cleared: number }>(
        "/platform-admin/danger-zone/purge",
        { confirmation_phrase: input.confirmationPhrase },
        input.stepUpToken
      ),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["platform-admin"] }),
  });
}
