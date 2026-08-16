import type { Metadata } from "next";

import { IntelligenceCapabilitiesSection } from "@/components/marketing/intelligence-capabilities-section";
import { IntelligenceFinalCtaSection } from "@/components/marketing/intelligence-final-cta-section";
import { IntelligenceHeroSection } from "@/components/marketing/intelligence-hero-section";
import { IntelligenceRoadmapSection } from "@/components/marketing/intelligence-roadmap-section";

export const metadata: Metadata = {
  title: "Phantom Intelligence | Phantom Hire",
  description:
    "Real breakdowns of your own pipeline — fit rating, status, source, and hiring manager alignment — generated from your project data, not market-wide claims.",
};

export default function IntelligencePage() {
  return (
    <>
      <IntelligenceHeroSection />
      <IntelligenceCapabilitiesSection />
      <IntelligenceRoadmapSection />
      <IntelligenceFinalCtaSection />
    </>
  );
}
