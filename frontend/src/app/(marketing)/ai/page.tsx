import type { Metadata } from "next";

import { AiCapabilitiesSection } from "@/components/marketing/ai-capabilities-section";
import { AiFinalCtaSection } from "@/components/marketing/ai-final-cta-section";
import { AiHeroSection } from "@/components/marketing/ai-hero-section";
import { AiLifecycleSection } from "@/components/marketing/ai-lifecycle-section";
import { AiTrustSection } from "@/components/marketing/ai-trust-section";

export const metadata: Metadata = {
  title: "Phantom AI | Phantom Hire",
  description:
    "Evidence-based fit assessments before every call and honest handoff recommendations after every one — generated on demand, never a live listener.",
};

export default function AiPage() {
  return (
    <>
      <AiHeroSection />
      <AiCapabilitiesSection />
      <AiLifecycleSection />
      <AiTrustSection />
      <AiFinalCtaSection />
    </>
  );
}
