import type { Metadata } from "next";

import { DiscreetIndustriesSection } from "@/components/marketing/discreet-industries-section";
import { FeatureGridSection } from "@/components/marketing/feature-grid-section";
import { HiringTeamsHeroSection } from "@/components/marketing/hiring-teams-hero-section";
import { HowItWorksSection } from "@/components/marketing/how-it-works-section";
import { PurgeCertificateShowcaseSection } from "@/components/marketing/purge-certificate-showcase-section";
import { RevealIdentityShowcaseSection } from "@/components/marketing/reveal-identity-showcase-section";
import { SecurityCtaSection } from "@/components/marketing/security-cta-section";

export const metadata: Metadata = {
  title: "For Hiring Teams | Phantom Hire",
  description:
    "The ATS built for hiring that can't be seen: hidden talent, AI screening, and zero-retention when the project is done.",
};

export default function HiringTeamsPage() {
  return (
    <>
      <HiringTeamsHeroSection />
      <RevealIdentityShowcaseSection />
      <FeatureGridSection />
      <PurgeCertificateShowcaseSection />
      <DiscreetIndustriesSection />
      <HowItWorksSection />
      <SecurityCtaSection />
    </>
  );
}
