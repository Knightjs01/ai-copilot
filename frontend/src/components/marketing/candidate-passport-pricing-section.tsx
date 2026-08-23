import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { PassportIdCardMockup } from "@/components/marketing/mockups/passport-id-card-mockup";

const FEATURES = [
  "Free forever",
  "Create your Passport",
  "Get verified",
  "Browse Shadow",
  "Explore opportunities anonymously",
  "Control your identity",
  "No subscription",
];

export function CandidatePassportPricingSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col gap-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-brand">
              For candidates
            </p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              Your Phantom Passport is free.
            </h2>
            <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
              Create your professional identity once. Discover roles privately. Apply
              anonymously, and stay in control of when your identity is revealed. Phantom&apos;s
              commercial model is built around companies, never candidates.
            </p>
          </div>

          <ul className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
            {FEATURES.map((feature) => (
              <li key={feature} className="flex items-start gap-2">
                <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
                <span className="text-sm text-foreground">{feature}</span>
              </li>
            ))}
          </ul>

          <div className="flex flex-col gap-3 sm:flex-row">
            <Button asChild variant="brand" size="lg">
              <Link href="/shadow/signup">Create Your Passport</Link>
            </Button>
            <Button asChild variant="secondary" size="lg">
              <Link href="/shadow">Explore Shadow</Link>
            </Button>
          </div>
        </div>

        <div className="flex justify-center">
          <PassportIdCardMockup />
        </div>
      </div>
    </section>
  );
}
