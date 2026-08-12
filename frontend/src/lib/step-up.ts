import { apiClient } from "@/lib/api-client";
import type { StepUpResponse } from "@/lib/types";

/** Re-verifies password (and MFA code, if enrolled) and returns a short-lived token to pass as
 * the X-Step-Up-Token header on a high-risk action — see StepUpDialog, which is the usual way
 * to call this from a component. */
export async function requestStepUpToken(password: string, mfaCode?: string): Promise<string> {
  const res = await apiClient.post<StepUpResponse>("/auth/step-up", {
    password,
    mfa_code: mfaCode || undefined,
  });
  return res.step_up_token;
}
