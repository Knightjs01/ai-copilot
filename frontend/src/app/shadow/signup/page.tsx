import type { Metadata } from "next";

import { ShadowSignupForm } from "./shadow-signup-form";

export const metadata: Metadata = {
  title: "Create Passport | Phantom Hire",
};

export default function ShadowSignupPage() {
  return <ShadowSignupForm />;
}
