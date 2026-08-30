import type { Metadata } from "next";

import { TalentPartnersFeaturesSection } from "@/components/marketing/talent-partners-features-section";
import { TalentPartnersFinalCtaSection } from "@/components/marketing/talent-partners-final-cta-section";
import { TalentPartnersHeroSection } from "@/components/marketing/talent-partners-hero-section";

export const metadata: Metadata = {
  title: "Phantom Talent Partners | Phantom Hire",
  description:
    "Access verified recruitment experts who manage your search using Phantom's network, technology and insights — the expert layer of the Phantom ecosystem.",
};

export default function TalentPartnersPage() {
  return (
    <>
      <TalentPartnersHeroSection />
      <TalentPartnersFeaturesSection />
      <TalentPartnersFinalCtaSection />
    </>
  );
}
