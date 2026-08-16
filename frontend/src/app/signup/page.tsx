import type { Metadata } from "next";

import { SignupForm } from "./signup-form";

export const metadata: Metadata = {
  title: "Sign up | Phantom Hire",
};

export default function SignupPage() {
  return <SignupForm />;
}
