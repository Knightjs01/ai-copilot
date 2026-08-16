import type { Metadata } from "next";

import { SecurityArchitectureSection } from "@/components/marketing/security-architecture-section";
import { SecurityCtaSection } from "@/components/marketing/security-cta-section";
import { SecurityHeroSection } from "@/components/marketing/security-hero-section";
import { SecurityStepupSection } from "@/components/marketing/security-stepup-section";

export const metadata: Metadata = {
  title: "Security | Phantom Hire",
  description:
    "Three-layer tenant isolation, mandatory MFA with step-up re-auth on high-risk actions, encryption at rest, and an append-only audit log — the real architecture behind Phantom Hire.",
};

export default function SecurityPage() {
  return (
    <>
      <SecurityHeroSection />
      <SecurityArchitectureSection />
      <SecurityStepupSection />
      <SecurityCtaSection />
    </>
  );
}
