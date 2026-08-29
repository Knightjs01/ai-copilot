import Image from "next/image";
import Link from "next/link";
import { CheckCircle2 } from "lucide-react";

import { PassportIdCardMockup } from "@/components/marketing/mockups/passport-id-card-mockup";
import { Button } from "@/components/ui/button";

const KEY_POINTS = [
  "Build once, apply everywhere under an anonymous Callsign",
  "Original CV stays encrypted in your Candidate Vault, never shown to recruiters",
  "Companies only see what you've reviewed and approved",
  "Your identity stays sealed until you approve a Reveal Request",
];

export function PassportShowcaseSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col gap-5">
          <div className="inline-flex w-fit items-center gap-2 rounded-full border border-brand/20 bg-gradient-to-r from-brand/10 to-electric/10 px-3.5 py-1.5">
            <Image
              src="/shadow-icon.png"
              alt=""
              width={557}
              height={550}
              className="h-3.5 w-auto"
            />
            <p className="text-xs font-semibold uppercase tracking-wide text-brand">
              The Phantom Candidate Passport · Live now
            </p>
          </div>
          <div>
            <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              One anonymous passport
              <br />
              <span className="text-brand">apply everywhere</span>
            </h2>
            <div className="mt-5 h-1 w-16 rounded-full bg-gradient-to-r from-brand to-electric" />
          </div>
          <ul className="flex flex-col gap-2.5">
            {KEY_POINTS.map((point) => (
              <li key={point} className="flex items-start gap-2.5">
                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-brand" />
                <span className="text-base text-foreground/90">{point}</span>
              </li>
            ))}
          </ul>
          <div>
            <Button
              asChild
              variant="brand"
              size="lg"
              className="bg-gradient-to-br from-brand to-electric shadow-lg shadow-brand/30"
            >
              <Link href="/shadow/signup">Build your Passport</Link>
            </Button>
          </div>
        </div>

        <PassportIdCardMockup />
      </div>
    </section>
  );
}
