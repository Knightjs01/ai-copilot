import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { IdentityFlowMockup } from "@/components/marketing/mockups/identity-flow-mockup";

const FEATURES = [
  "Phantom Passport",
  "Professional profile",
  "CV / career history",
  "Skills & experience",
  "AI job matching",
  "Shadow anonymous job board",
  "Anonymous applications",
  "Project-specific Callsign",
  "Candidate-controlled identity reveal",
  "Job recommendations",
  "Talent discovery",
  "Privacy controls",
  "Talent visibility controls",
  "Candidate Privacy Centre",
];

export function CandidatePassportPricingSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-start gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col gap-6">
          <div>
            <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              Your Phantom Passport is free.
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
              Create your professional identity once. Discover roles privately. Apply
              anonymously. Stay in control of when your identity is revealed.
            </p>
          </div>

          <div className="flex items-end gap-2">
            <span className="text-5xl font-semibold tracking-tight text-foreground">£0</span>
            <span className="pb-1.5 text-sm font-medium text-muted-foreground">Forever</span>
          </div>

          <div>
            <Button asChild variant="brand" size="lg">
              <Link href="/shadow/signup">Create My Passport</Link>
            </Button>
          </div>

          <ul className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
            {FEATURES.map((feature) => (
              <li key={feature} className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
                <span className="text-sm text-foreground">{feature}</span>
              </li>
            ))}
          </ul>

          <p className="text-sm font-medium text-muted-foreground">
            Your Passport belongs to you.
          </p>
        </div>

        <IdentityFlowMockup />
      </div>
    </section>
  );
}
