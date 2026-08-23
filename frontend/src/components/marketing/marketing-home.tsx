import { AtsShowcaseSection } from "@/components/marketing/ats-showcase-section";
import { HeroSection } from "@/components/marketing/hero-section";
import { HomeFinalCtaSection } from "@/components/marketing/home-final-cta-section";
import { JobBoardShowcaseSection } from "@/components/marketing/job-board-showcase-section";
import { PassportShowcaseSection } from "@/components/marketing/passport-showcase-section";
import { PhantomAiBeatSection } from "@/components/marketing/phantom-ai-beat-section";
import { RevealBeatSection } from "@/components/marketing/reveal-beat-section";
import { SecurityBeatSection } from "@/components/marketing/security-beat-section";
import { TalentMemoryBeatSection } from "@/components/marketing/talent-memory-beat-section";

// Nav/footer/theme now come from (marketing)/layout.tsx — this renders section content only.
//
// A Passport-led narrative: the hero's primary visual IS the Candidate Passport (not the Ghost,
// which is now a discreet watermark inside HeroSection), then the story follows the Passport
// through the product -- explained, then used to discover opportunities (Shadow), calculate
// match (Intelligence), work inside a hiring pipeline (ATS), and finally the controlled
// anonymous-to-identified transition (Reveal) -- before trust-building beats (Security, Talent
// Memory, the latter explicitly framed as a preview, not live product) and a final CTA that
// forks by audience into /hiring-teams and /job-seekers.
export function MarketingHome() {
  return (
    <>
      <HeroSection />
      <PassportShowcaseSection />
      <JobBoardShowcaseSection />
      <PhantomAiBeatSection />
      <AtsShowcaseSection />
      <RevealBeatSection />
      <SecurityBeatSection />
      <TalentMemoryBeatSection />
      <HomeFinalCtaSection />
    </>
  );
}
