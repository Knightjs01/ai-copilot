"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "@/lib/api-client";
import type { RoleName, UserRead } from "@/lib/types";

export function useTeam() {
  return useQuery({
    queryKey: ["team"],
    queryFn: () => apiClient.get<UserRead[]>("/users"),
  });
}

interface InviteUserInput {
  email: string;
  full_name: string;
  role: RoleName;
}

export function useInviteUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ input, stepUpToken }: { input: InviteUserInput; stepUpToken: string }) =>
      apiClient.post<UserRead>("/users/invite", input, stepUpToken),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["team"] });
    },
  });
}
