import type { Metadata } from "next";

import { AtsComparisonSection } from "@/components/marketing/ats-comparison-section";
import { CommercialFlywheelSection } from "@/components/marketing/commercial-flywheel-section";
import { PhantomIntelligenceSection } from "@/components/marketing/phantom-intelligence-section";
import { PlanComparisonTableSection } from "@/components/marketing/plan-comparison-table-section";
import { PricingFaqSection } from "@/components/marketing/pricing-faq-section";
import { PricingFinalCtaSection } from "@/components/marketing/pricing-final-cta-section";
import { PricingHeroSection } from "@/components/marketing/pricing-hero-section";
import { PricingToggleProvider } from "@/components/marketing/pricing-toggle-provider";
import { PricingTrustSection } from "@/components/marketing/pricing-trust-section";
import { TalentMemorySection } from "@/components/marketing/talent-memory-section";

export const metadata: Metadata = {
  title: "Pricing | Phantom Hire",
  description:
    "Candidates are free. Companies pay for the hiring infrastructure, AI, talent intelligence, verification and security that make Phantom different.",
};

export default function PricingPage() {
  return (
    <>
      <PricingHeroSection />
      <PricingToggleProvider />
      <TalentMemorySection />
      <PhantomIntelligenceSection />
      <AtsComparisonSection />
      <CommercialFlywheelSection />
      <PlanComparisonTableSection />
      <PricingFaqSection />
      <PricingTrustSection />
      <PricingFinalCtaSection />
    </>
  );
}
