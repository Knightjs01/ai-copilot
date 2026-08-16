import type { Metadata } from "next";

import { AtsAlignmentSection } from "@/components/marketing/ats-alignment-section";
import { AtsAnalyticsSection } from "@/components/marketing/ats-analytics-section";
import { AtsFinalCtaSection } from "@/components/marketing/ats-final-cta-section";
import { AtsGovernanceSection } from "@/components/marketing/ats-governance-section";
import { AtsHeroSection } from "@/components/marketing/ats-hero-section";
import { AtsPipelineSection } from "@/components/marketing/ats-pipeline-section";

export const metadata: Metadata = {
  title: "Phantom ATS | Phantom Hire",
  description:
    "Hiring projects, Callsigns instead of names, AI fit ratings, and a live dashboard of exactly what needs your attention next.",
};

export default function AtsPage() {
  return (
    <>
      <AtsHeroSection />
      <AtsPipelineSection />
      <AtsAlignmentSection />
      <AtsAnalyticsSection />
      <AtsGovernanceSection />
      <AtsFinalCtaSection />
    </>
  );
}
