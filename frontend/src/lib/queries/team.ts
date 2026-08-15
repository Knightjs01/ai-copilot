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

export function useChangeRole(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (role: RoleName) => apiClient.patch<void>(`/users/${userId}/role`, { role }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["team"] });
    },
  });
}

export function useRemoveUser(userId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.delete<void>(`/users/${userId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["team"] });
    },
  });
}
