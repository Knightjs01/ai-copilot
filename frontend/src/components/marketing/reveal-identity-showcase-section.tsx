import Image from "next/image";

import { RevealIdentityMockup } from "@/components/marketing/mockups/reveal-identity-mockup";

export function RevealIdentityShowcaseSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto grid max-w-6xl grid-cols-1 items-center gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="order-2 lg:order-1">
          <RevealIdentityMockup />
        </div>

        <div className="order-1 flex flex-col gap-5 lg:order-2">
          <div className="flex items-center gap-2">
            <Image
              src="/phantom-icon.png"
              alt=""
              width={234}
              height={190}
              className="h-4 w-auto"
            />
            <p className="text-xs font-semibold uppercase tracking-wide text-brand">
              Identity Vault · Live now
            </p>
          </div>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Blind by default. Revealed on your terms.
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Every candidate stays a Callsign until an Owner reveals them, with a reason recorded
            against their name and an entry in the audit trail. No silent lookups, no shared
            spreadsheet of names floating around your team.
          </p>
        </div>
      </div>
    </section>
  );
}
