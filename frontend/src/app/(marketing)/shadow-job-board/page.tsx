import type { Metadata } from "next";

import { ShadowBenefitsSection } from "@/components/marketing/shadow-benefits-section";
import { ShadowFeaturesSection } from "@/components/marketing/shadow-features-section";
import { ShadowFinalCtaSection } from "@/components/marketing/shadow-final-cta-section";
import { ShadowHeroSection } from "@/components/marketing/shadow-hero-section";
import { ShadowHowItWorksSection } from "@/components/marketing/shadow-howitworks-section";
import { ShadowRevealSection } from "@/components/marketing/shadow-reveal-section";

export const metadata: Metadata = {
  title: "Shadow - Anonymous Talent Network | Phantom Hire",
  description:
    "The job market you can enter without being seen. Search real roles by skill, apply with your Phantom Passport, and control every reveal yourself.",
};

export default function ShadowJobBoardPage() {
  return (
    <>
      <ShadowHeroSection />
      <ShadowFeaturesSection />
      <ShadowHowItWorksSection />
      <ShadowRevealSection />
      <ShadowBenefitsSection />
      <ShadowFinalCtaSection />
    </>
  );
}
