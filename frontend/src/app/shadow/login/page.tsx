import type { Metadata } from "next";

import { ShadowLoginForm } from "./shadow-login-form";

export const metadata: Metadata = {
  title: "Candidate Login | Phantom Hire",
};

export default function ShadowLoginPage() {
  return <ShadowLoginForm />;
}
