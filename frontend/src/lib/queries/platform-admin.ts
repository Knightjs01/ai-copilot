"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { platformAdminApiClient } from "@/lib/platform-admin-api-client";
import type {
  AccessRequestStats,
  ActionQueueItem,
  AdminCandidateDetail,
  AdminCandidateListResponse,
  AdminCompanyDetail,
  AdminCompanyListResponse,
  AdminCompanyUser,
  AdminShadowJob,
  AdminShadowJobDetail,
  AdminShadowJobListResponse,
  AuditEntry,
  CompanyAccessRequest,
  CompanyProfile,
  GlobalSearchResultItem,
  MfaEnableResponse,
  MfaSetupResponse,
  PlatformAdminAuditLogListResponse,
  PlatformAdminNotificationListResponse,
  PlatformAdminSummary,
} from "@/lib/types";

interface AdminListOptions {
  search?: string;
  page?: number;
  pageSize?: number;
}

const NOTIFICATION_POLL_INTERVAL_MS = 20000;

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

export function useAuditLog(
  options: { action?: string; adminId?: string; page?: number; pageSize?: number } = {}
) {
  const { action, adminId, page = 1, pageSize = 50 } = options;
  return useQuery({
    queryKey: ["platform-admin", "audit-log", action ?? "", adminId ?? "", page, pageSize],
    queryFn: () => {
      const params = new URLSearchParams();
      if (action) params.set("action", action);
      if (adminId) params.set("admin_id", adminId);
      params.set("limit", String(pageSize));
      params.set("offset", String((page - 1) * pageSize));
      return platformAdminApiClient.get<PlatformAdminAuditLogListResponse>(
        `/company-access/audit-log?${params.toString()}`
      );
    },
  });
}

export function useUnreadNotificationCount() {
  return useQuery({
    queryKey: ["platform-admin", "notifications", "unread-count"],
    queryFn: () =>
      platformAdminApiClient.get<{ unread_count: number }>(
        "/platform-admin/notifications/unread-count"
      ),
    refetchInterval: NOTIFICATION_POLL_INTERVAL_MS,
  });
}

export function useNotifications(options: { page?: number; pageSize?: number } = {}) {
  const { page = 1, pageSize = 20 } = options;
  return useQuery({
    queryKey: ["platform-admin", "notifications", "list", page, pageSize],
    queryFn: () => {
      const params = new URLSearchParams();
      params.set("limit", String(pageSize));
      params.set("offset", String((page - 1) * pageSize));
      return platformAdminApiClient.get<PlatformAdminNotificationListResponse>(
        `/platform-admin/notifications?${params.toString()}`
      );
    },
  });
}

export function useMarkNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      platformAdminApiClient.post<void>("/platform-admin/notifications/mark-read"),
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: ["platform-admin", "notifications"] }),
  });
}

export function useAllCompanies(options: AdminListOptions = {}) {
  const { search, page = 1, pageSize = 25 } = options;
  return useQuery({
    queryKey: ["platform-admin", "companies", "list", search ?? "", page, pageSize],
    queryFn: () => {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      params.set("limit", String(pageSize));
      params.set("offset", String((page - 1) * pageSize));
      return platformAdminApiClient.get<AdminCompanyListResponse>(
        `/companies?${params.toString()}`
      );
    },
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
    queryFn: async () => {
      const response = await platformAdminApiClient.get<AdminCompanyListResponse>(
        "/companies?profile_status=pending_review"
      );
      return response.items;
    },
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

export function useAdminJobs(status?: string, companyId?: string, options: AdminListOptions = {}) {
  const { search, page = 1, pageSize = 100 } = options;
  return useQuery({
    queryKey: [
      "platform-admin",
      "jobs",
      "list",
      status ?? "all",
      companyId ?? "all",
      search ?? "",
      page,
      pageSize,
    ],
    queryFn: () => {
      const params = new URLSearchParams();
      if (status && status !== "all") params.set("status", status);
      if (companyId) params.set("company_id", companyId);
      if (search) params.set("search", search);
      params.set("limit", String(pageSize));
      params.set("offset", String((page - 1) * pageSize));
      return platformAdminApiClient.get<AdminShadowJobListResponse>(
        `/platform-admin/jobs?${params.toString()}`
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

export function useAdminCandidates(verificationStatus?: string, options: AdminListOptions = {}) {
  const { search, page = 1, pageSize = 25 } = options;
  return useQuery({
    queryKey: [
      "platform-admin",
      "candidates",
      "list",
      verificationStatus ?? "all",
      search ?? "",
      page,
      pageSize,
    ],
    queryFn: () => {
      const params = new URLSearchParams();
      if (verificationStatus && verificationStatus !== "all") {
        params.set("verification_status", verificationStatus);
      }
      if (search) params.set("search", search);
      params.set("limit", String(pageSize));
      params.set("offset", String((page - 1) * pageSize));
      return platformAdminApiClient.get<AdminCandidateListResponse>(
        `/platform-admin/candidates?${params.toString()}`
      );
    },
  });
}

export function useGlobalSearch(query: string) {
  return useQuery({
    queryKey: ["platform-admin", "search", query],
    queryFn: () =>
      platformAdminApiClient.get<GlobalSearchResultItem[]>(
        `/platform-admin/search?q=${encodeURIComponent(query)}`
      ),
    enabled: query.trim().length >= 2,
  });
}

export function useAdminCandidate(passportId: string) {
  return useQuery({
    queryKey: ["platform-admin", "candidates", passportId],
    queryFn: () =>
      platformAdminApiClient.get<AdminCandidateDetail>(
        `/platform-admin/candidates/${passportId}`
      ),
    enabled: !!passportId,
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
