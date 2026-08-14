"use client";

import * as React from "react";

import { AiCreditsSection } from "@/components/marketing/ai-credits-section";
import { CandidatePassportPricingSection } from "@/components/marketing/candidate-passport-pricing-section";
import { CompanyPlansSection } from "@/components/marketing/company-plans-section";
import { MarketplaceFeeSection } from "@/components/marketing/marketplace-fee-section";
import { VerificationTiersSection } from "@/components/marketing/verification-tiers-section";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import type { BillingPeriod } from "@/lib/pricing-config";

type Audience = "candidate" | "company";

export function PricingToggleProvider() {
  const [audience, setAudience] = React.useState<Audience>("company");
  const [billingPeriod, setBillingPeriod] = React.useState<BillingPeriod>("annual");

  return (
    <>
      <section className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-3 px-6 py-10 text-center">
          <p className="text-sm font-medium text-muted-foreground">I&apos;m a...</p>
          <PillToggleGroup
            options={[
              { value: "candidate", label: "Candidate" },
              { value: "company", label: "Company / Recruiter" },
            ]}
            value={audience}
            onChange={setAudience}
          />
        </div>
      </section>

      {audience === "candidate" ? (
        <>
          <CandidatePassportPricingSection />
          <VerificationTiersSection />
        </>
      ) : (
        <>
          <CompanyPlansSection
            billingPeriod={billingPeriod}
            onBillingPeriodChange={setBillingPeriod}
          />
          <AiCreditsSection />
          <MarketplaceFeeSection />
        </>
      )}
    </>
  );
}
