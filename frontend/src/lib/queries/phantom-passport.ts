"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { candidateApiClient } from "@/lib/candidate-api-client";
import { fetchOrNull } from "@/lib/queries/helpers";
import type { CvParseResult, PassportUpdateInput, PhantomPassport } from "@/lib/types";

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
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append("file", file);
      return candidateApiClient.postForm<CvParseResult>("/phantom-passport/parse-cv", formData);
    },
  });
}
