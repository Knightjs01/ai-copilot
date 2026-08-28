"use client";

import { useQuery } from "@tanstack/react-query";

import { candidateApiClient } from "@/lib/candidate-api-client";
import type { LocationSuggestion } from "@/lib/types";

export function useLocationAutocomplete(text: string) {
  return useQuery({
    queryKey: ["geocoding", "autocomplete", text],
    queryFn: () =>
      candidateApiClient.get<LocationSuggestion[]>(
        `/geocoding/autocomplete?text=${encodeURIComponent(text)}`
      ),
    enabled: text.trim().length >= 3,
    staleTime: 60_000,
  });
}
