"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { platformAdminApiClient } from "@/lib/platform-admin-api-client";
import type { CommercialPlan, Company, CompanyUpdateInput, RoleName } from "@/lib/types";

// Company Onboarding Phase 1 -- every hook here hits a platform-admin-only route (see
// backend companies/api.py's admin_router additions), reachable only from the platform-admin
// portal. Nothing under frontend/src/app/(app)/ calls any of these.

function onboardingProfileKey(companyId: string | undefined) {
  return ["platform-admin", "companies", companyId, "onboarding-profile"] as const;
}

export interface AdminCreateCompanyInput {
  companyName: string;
  ownerEmail: string;
  ownerFullName: string;
  commercialPlanCode: string | null;
}

export function useAdminCreateCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: AdminCreateCompanyInput) =>
      platformAdminApiClient.post<Company>("/companies", {
        company_name: input.companyName,
        owner_email: input.ownerEmail,
        owner_full_name: input.ownerFullName,
        commercial_plan_code: input.commercialPlanCode,
      }),
    onSuccess: () =>
      void queryClient.invalidateQueries({ queryKey: ["platform-admin", "companies"] }),
  });
}

export function useAdminCompanyProfile(companyId: string | undefined) {
  return useQuery({
    queryKey: onboardingProfileKey(companyId),
    queryFn: () => platformAdminApiClient.get<Company>(`/companies/${companyId}/profile`),
    enabled: !!companyId,
  });
}

export function useAdminUpdateCompanyProfile(companyId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CompanyUpdateInput) =>
      platformAdminApiClient.patch<Company>(`/companies/${companyId}/profile`, input),
    onSuccess: (data) => queryClient.setQueryData(onboardingProfileKey(companyId), data),
  });
}

function useAdminUploadCompanyMedia(companyId: string | undefined, segment: "logo" | "cover-image") {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return platformAdminApiClient.postForm<Company>(
        `/companies/${companyId}/${segment}`,
        formData
      );
    },
    onSuccess: (data) => queryClient.setQueryData(onboardingProfileKey(companyId), data),
  });
}

export function useAdminUploadLogo(companyId: string | undefined) {
  return useAdminUploadCompanyMedia(companyId, "logo");
}

export function useAdminUploadCoverImage(companyId: string | undefined) {
  return useAdminUploadCompanyMedia(companyId, "cover-image");
}

export interface AdminInviteCompanyUserInput {
  email: string;
  fullName: string;
  roleName: RoleName;
}

export function useAdminInviteCompanyUser(companyId: string | undefined) {
  return useMutation({
    mutationFn: (input: AdminInviteCompanyUserInput) =>
      platformAdminApiClient.post(`/companies/${companyId}/users/invite`, {
        email: input.email,
        full_name: input.fullName,
        role_name: input.roleName,
      }),
  });
}

export function useAdminActivateCompany(companyId: string | undefined) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => platformAdminApiClient.post<Company>(`/companies/${companyId}/activate`),
    onSuccess: (data) => {
      queryClient.setQueryData(onboardingProfileKey(companyId), data);
      void queryClient.invalidateQueries({ queryKey: ["platform-admin", "companies"] });
    },
  });
}

export function useAdminCommercialPlans() {
  return useQuery({
    queryKey: ["platform-admin", "commercial-plans"],
    queryFn: () =>
      platformAdminApiClient.get<CommercialPlan[]>("/platform-admin/commercial/plans"),
  });
}
