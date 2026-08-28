"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { fetchOrNull } from "@/lib/queries/helpers";
import type { Company, CompanyProfile, CompanyUpdateInput, ProfileStats } from "@/lib/types";

export function useMyCompany() {
  return useQuery({
    queryKey: ["company", "me"],
    queryFn: () => apiClient.get<Company>("/companies/me"),
  });
}

export function useUpdateCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CompanyUpdateInput) => apiClient.patch<Company>("/companies/me", input),
    onSuccess: (data) => {
      queryClient.setQueryData(["company", "me"], data);
      // team_size now comes from employee_count (part of this same PATCH) -- the stats card's
      // own query key needs invalidating too, or it keeps showing the pre-edit number.
      void queryClient.invalidateQueries({ queryKey: ["company", "me", "profile-stats"] });
    },
  });
}

// Internal-only real numbers (active roles, total hires, team size, pipeline) -- never part of
// the shared public/preview shape, see backend ProfileStats' own docstring for why.
export function useProfileStats() {
  return useQuery({
    queryKey: ["company", "me", "profile-stats"],
    queryFn: () => apiClient.get<ProfileStats>("/companies/me/profile-stats"),
  });
}

// Self-service, authenticated -- shows what candidates would see once approved, built from the
// live draft fields (not the published snapshot).
export function usePreviewCompanyProfile() {
  return useQuery({
    queryKey: ["company", "me", "preview"],
    queryFn: () => apiClient.get<CompanyProfile>("/companies/me/preview"),
  });
}

function useUploadCompanyMedia(path: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return apiClient.postForm<Company>(path, formData);
    },
    onSuccess: (data) => {
      queryClient.setQueryData(["company", "me"], data);
    },
  });
}

export function useUploadLogo() {
  return useUploadCompanyMedia("/companies/me/logo");
}

export function useUploadCoverImage() {
  return useUploadCompanyMedia("/companies/me/cover-image");
}

function useProfileAction(path: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<Company>(path),
    onSuccess: (data) => {
      queryClient.setQueryData(["company", "me"], data);
    },
  });
}

export function useSubmitForReview() {
  return useProfileAction("/companies/me/submit-for-review");
}

export function usePauseProfile() {
  return useProfileAction("/companies/me/pause");
}

export function useResumeProfile() {
  return useProfileAction("/companies/me/resume");
}

// Public /companies/{slug} -- no auth required, resolves a 404 to null (either the slug doesn't
// exist or the profile isn't currently visible -- both look identical, matching the backend's
// own non-leaking shape).
export function useCompanyProfile(slug: string | undefined) {
  return useQuery({
    queryKey: ["company", "profile", slug],
    queryFn: () => fetchOrNull(() => apiClient.get<CompanyProfile>(`/companies/${slug}`)),
    enabled: !!slug,
  });
}
