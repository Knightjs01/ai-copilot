import type { Metadata } from "next";

import { PassportBenefitsSection } from "@/components/marketing/passport-benefits-section";
import { PassportFeaturesSection } from "@/components/marketing/passport-features-section";
import { PassportFinalCtaSection } from "@/components/marketing/passport-final-cta-section";
import { PassportHeroSection } from "@/components/marketing/passport-hero-section";
import { PassportHowItWorksSection } from "@/components/marketing/passport-howitworks-section";
import { PassportPrivacySection } from "@/components/marketing/passport-privacy-section";

export const metadata: Metadata = {
  title: "Candidate Passport | Phantom Hire",
  description:
    "Build your professional record once, apply everywhere under a Callsign, and approve every reveal individually. Free forever, private by default.",
};

export default function PassportPage() {
  return (
    <>
      <PassportHeroSection />
      <PassportFeaturesSection />
      <PassportHowItWorksSection />
      <PassportPrivacySection />
      <PassportBenefitsSection />
      <PassportFinalCtaSection />
    </>
  );
}
