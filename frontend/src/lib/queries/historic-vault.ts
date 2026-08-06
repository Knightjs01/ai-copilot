"use client";

import { useQuery } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { HistoricVaultOverview } from "@/lib/types";

export function useHistoricVaultOverview() {
  return useQuery({
    queryKey: ["historic-vault"],
    queryFn: () => apiClient.get<HistoricVaultOverview>("/historic-vault"),
  });
}
