"use client";

import { useMutation } from "@tanstack/react-query";

import { candidateApiClient } from "@/lib/candidate-api-client";
import type { CopilotChatRequest, CopilotChatResponse } from "@/lib/types";

export function useSendCopilotMessage() {
  return useMutation({
    mutationFn: (input: CopilotChatRequest) =>
      candidateApiClient.post<CopilotChatResponse>("/copilot/chat", input),
  });
}
