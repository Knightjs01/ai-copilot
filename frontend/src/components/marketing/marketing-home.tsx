import { AtsShowcaseSection } from "@/components/marketing/ats-showcase-section";
import { HeroSection } from "@/components/marketing/hero-section";
import { HomeFinalCtaSection } from "@/components/marketing/home-final-cta-section";
import { JobBoardShowcaseSection } from "@/components/marketing/job-board-showcase-section";
import { PassportShowcaseSection } from "@/components/marketing/passport-showcase-section";
import { PhantomAiBeatSection } from "@/components/marketing/phantom-ai-beat-section";
import { SecurityBeatSection } from "@/components/marketing/security-beat-section";
import { TalentMemoryBeatSection } from "@/components/marketing/talent-memory-beat-section";

// Nav/footer/theme now come from (marketing)/layout.tsx — this renders section content only.
//
// An 8-beat narrative (Opening -> Shadow -> Passport -> ATS -> AI -> Talent Memory -> Security
// -> Final CTA), each with its own visual treatment, rather than a flat list of generic sections.
// Real product demonstrations (Shadow's job board, Passport's Candidate Vault, the ATS pipeline,
// a real prescreen-assessment output) are used where the feature actually exists; Talent Memory
// is explicitly framed as a preview, not live product.
export function MarketingHome() {
  return (
    <>
      <HeroSection />
      <JobBoardShowcaseSection />
      <PassportShowcaseSection />
      <AtsShowcaseSection />
      <PhantomAiBeatSection />
      <TalentMemoryBeatSection />
      <SecurityBeatSection />
      <HomeFinalCtaSection />
    </>
  );
}
