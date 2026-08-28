import type { Metadata } from "next";

import { ShadowVerifyEmailContent } from "./shadow-verify-email-content";

export const metadata: Metadata = {
  title: "Verify Your Email | Phantom Hire",
};

export default function ShadowVerifyEmailPage() {
  return <ShadowVerifyEmailContent />;
}
