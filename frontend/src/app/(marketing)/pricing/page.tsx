import type { Metadata } from "next";

import { CandidatePassportPricingSection } from "@/components/marketing/candidate-passport-pricing-section";
import { CompanyPlansSection } from "@/components/marketing/company-plans-section";
import { PlanComparisonTableSection } from "@/components/marketing/plan-comparison-table-section";
import { PricingFaqSection } from "@/components/marketing/pricing-faq-section";
import { PricingFinalCtaSection } from "@/components/marketing/pricing-final-cta-section";
import { PricingHeroSection } from "@/components/marketing/pricing-hero-section";
import { PricingHowItWorksSection } from "@/components/marketing/pricing-how-it-works-section";
import { WhyPhantomDifferentSection } from "@/components/marketing/why-phantom-different-section";
import { getCommercialPlans } from "@/lib/pricing-config";

export const metadata: Metadata = {
  title: "Pricing | Phantom Hire",
  description:
    "Candidates are free. Companies pay for the hiring infrastructure, talent discovery and intelligence that make Phantom different.",
};

export default async function PricingPage() {
  const plans = await getCommercialPlans();

  return (
    <>
      <PricingHeroSection />
      <CompanyPlansSection plans={plans} />
      <WhyPhantomDifferentSection />
      <PricingHowItWorksSection />
      <CandidatePassportPricingSection />
      <PlanComparisonTableSection plans={plans} />
      <PricingFaqSection />
      <PricingFinalCtaSection />
    </>
  );
}
