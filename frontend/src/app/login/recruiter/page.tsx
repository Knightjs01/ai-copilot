import type { Metadata } from "next";

import { RecruiterLoginForm } from "./recruiter-login-form";

export const metadata: Metadata = {
  title: "Recruiter Login | Phantom Hire",
};

export default function RecruiterLoginPage() {
  return <RecruiterLoginForm />;
}
