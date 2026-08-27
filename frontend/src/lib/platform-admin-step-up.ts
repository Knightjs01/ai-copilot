import { platformAdminApiClient } from "@/lib/platform-admin-api-client";
import type { StepUpResponse } from "@/lib/types";

/** Re-verifies password + MFA code and returns a short-lived token to pass as the
 * X-Step-Up-Token header on a Danger Zone action — see PlatformAdminStepUpDialog, the usual way
 * to call this from a component. Mirrors lib/step-up.ts's requestStepUpToken exactly. */
export async function requestPlatformAdminStepUpToken(
  password: string,
  mfaCode?: string
): Promise<string> {
  const res = await platformAdminApiClient.post<StepUpResponse>("/platform-admin/step-up", {
    password,
    mfa_code: mfaCode || undefined,
  });
  return res.step_up_token;
}
