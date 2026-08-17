import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

import { PassportIdCardMockup } from "@/components/marketing/mockups/passport-id-card-mockup";
import { Button } from "@/components/ui/button";

const KEY_FEATURES = [
  "Build your professional record once — it travels with you to every role you apply for",
  "Apply under a reusable Callsign, recruiters see your evidence, never your name",
  "Your original CV stays encrypted in your Candidate Vault, never shown to anyone",
  "You review and approve every version before it's ever visible to a recruiter",
  "Your real identity only unseals when you personally approve a Reveal Request",
];

export function PassportHeroSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            Candidate Passport
          </p>
          <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
            One passport. A private identity, revealed only when you choose.
          </h1>
          <ul className="flex flex-col gap-2.5">
            {KEY_FEATURES.map((point) => (
              <li key={point} className="flex items-start gap-2.5">
                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-brand" />
                <span className="text-base text-foreground/90">{point}</span>
              </li>
            ))}
          </ul>
          <div>
            <Button asChild variant="brand" size="lg">
              <Link href="/shadow/signup">Build your Passport</Link>
            </Button>
          </div>
        </div>

        <PassportIdCardMockup />
      </div>
    </section>
  );
}
