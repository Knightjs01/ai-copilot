"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { candidateApiClient } from "@/lib/candidate-api-client";
import { fetchOrNull } from "@/lib/queries/helpers";
import type {
  CvDocumentStatus,
  CvParseResult,
  IndustriesSuggestionRequest,
  IndustriesSuggestionResponse,
  PassportUpdateInput,
  PassportVersionSummary,
  PhantomPassport,
  SkillsSuggestionRequest,
  SkillsSuggestionResponse,
  SummaryImprovementRequest,
  SummaryImprovementResponse,
} from "@/lib/types";

export function useMyPassport() {
  return useQuery({
    queryKey: ["phantom-passport", "me"],
    queryFn: () => fetchOrNull(() => candidateApiClient.get<PhantomPassport>("/phantom-passport/me")),
  });
}

export function useSavePassport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: PassportUpdateInput) =>
      candidateApiClient.put<PhantomPassport>("/phantom-passport/me", input),
    onSuccess: (data) => {
      queryClient.setQueryData(["phantom-passport", "me"], data);
    },
  });
}

export function useParseCv() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return candidateApiClient.postForm<CvParseResult>("/phantom-passport/parse-cv", formData);
    },
    onSuccess: () => {
      // parse-cv now also persists the original file into the Candidate Vault as a side effect.
      queryClient.invalidateQueries({ queryKey: ["phantom-passport", "original-cv"] });
    },
  });
}

export function useOriginalCvStatus() {
  return useQuery({
    queryKey: ["phantom-passport", "original-cv"],
    queryFn: () =>
      fetchOrNull(() => candidateApiClient.get<CvDocumentStatus>("/phantom-passport/original-cv")),
  });
}

export function useDownloadOriginalCv() {
  return useMutation({
    mutationFn: async () => {
      const { blob, filename } = await candidateApiClient.getBlob(
        "/phantom-passport/original-cv/download"
      );
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename ?? "cv";
      link.click();
      URL.revokeObjectURL(url);
    },
  });
}

export function useDeleteOriginalCv() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => candidateApiClient.delete<void>("/phantom-passport/original-cv"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["phantom-passport", "original-cv"] });
    },
  });
}

export function useApprovePassport() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () =>
      candidateApiClient.post<PassportVersionSummary>("/phantom-passport/me/approve"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["phantom-passport", "me"] });
      queryClient.invalidateQueries({ queryKey: ["phantom-passport", "versions"] });
    },
  });
}

export function usePassportVersions() {
  return useQuery({
    queryKey: ["phantom-passport", "versions"],
    queryFn: () =>
      candidateApiClient.get<PassportVersionSummary[]>("/phantom-passport/versions"),
  });
}

// AI co-pilot suggestions — always returned for the candidate to review, never applied
// automatically. Not tied to query invalidation; callers apply/dismiss the result themselves.
export function useSuggestSummary() {
  return useMutation({
    mutationFn: (input: SummaryImprovementRequest) =>
      candidateApiClient.post<SummaryImprovementResponse>(
        "/phantom-passport/suggest-summary",
        input
      ),
  });
}

export function useSuggestSkills() {
  return useMutation({
    mutationFn: (input: SkillsSuggestionRequest) =>
      candidateApiClient.post<SkillsSuggestionResponse>(
        "/phantom-passport/suggest-skills",
        input
      ),
  });
}

export function useSuggestIndustries() {
  return useMutation({
    mutationFn: (input: IndustriesSuggestionRequest) =>
      candidateApiClient.post<IndustriesSuggestionResponse>(
        "/phantom-passport/suggest-industries",
        input
      ),
  });
}
