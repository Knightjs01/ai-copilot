import { DiscreetIndustriesSection } from "@/components/marketing/discreet-industries-section";
import { FeatureGridSection } from "@/components/marketing/feature-grid-section";
import { HeroSection } from "@/components/marketing/hero-section";
import { HowItWorksSection } from "@/components/marketing/how-it-works-section";
import { MarketingFooter } from "@/components/marketing/marketing-footer";
import { MarketingNav } from "@/components/marketing/marketing-nav";
import { PhantomStorySection } from "@/components/marketing/phantom-story-section";
import { SecurityCtaSection } from "@/components/marketing/security-cta-section";
import { ThreeInOneSection } from "@/components/marketing/three-in-one-section";
import { ZeroRetentionSection } from "@/components/marketing/zero-retention-section";

export function MarketingHome() {
  return (
    <div className="flex min-h-screen flex-col bg-white">
      <MarketingNav />
      <main className="flex-1">
        <HeroSection />
        <ThreeInOneSection />
        <DiscreetIndustriesSection />
        <PhantomStorySection />
        <ZeroRetentionSection />
        <HowItWorksSection />
        <FeatureGridSection />
        <SecurityCtaSection />
      </main>
      <MarketingFooter />
    </div>
  );
}
