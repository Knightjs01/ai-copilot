"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import { fetchOrNull } from "@/lib/queries/helpers";
import type { Company, CompanyProfile, CompanyUpdateInput } from "@/lib/types";

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
    },
  });
}

// Public /companies/{slug} -- no auth required, resolves a 404 to null (either the slug doesn't
// exist or the company hasn't opted in -- both look identical, matching the backend's own
// non-leaking shape).
export function useCompanyProfile(slug: string | undefined) {
  return useQuery({
    queryKey: ["company", "profile", slug],
    queryFn: () => fetchOrNull(() => apiClient.get<CompanyProfile>(`/companies/${slug}`)),
    enabled: !!slug,
  });
}
