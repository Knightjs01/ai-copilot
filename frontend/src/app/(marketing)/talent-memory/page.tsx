import type { Metadata } from "next";

import { TalentMemoryFinalCtaSection } from "@/components/marketing/talent-memory-final-cta-section";
import { TalentMemoryHeroSection } from "@/components/marketing/talent-memory-hero-section";
import { TalentMemoryRoadmapSection } from "@/components/marketing/talent-memory-roadmap-section";

export const metadata: Metadata = {
  title: "Talent Memory | Phantom Hire",
  description:
    "A preview of what we're building next: a permitted, consent-respecting memory of skills and match profile that survives a project purge — no identity, no CV, no notes carried forward.",
};

export default function TalentMemoryPage() {
  return (
    <>
      <TalentMemoryHeroSection />
      <TalentMemoryRoadmapSection />
      <TalentMemoryFinalCtaSection />
    </>
  );
}
