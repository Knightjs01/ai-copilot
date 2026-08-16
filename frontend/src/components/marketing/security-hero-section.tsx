import Link from "next/link";

import { TenantIsolationMockup } from "@/components/marketing/mockups/tenant-isolation-mockup";
import { Button } from "@/components/ui/button";

export function SecurityHeroSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-12 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">Security</p>
          <h1 className="text-4xl font-semibold tracking-tight text-foreground sm:text-5xl">
            Built to hold as little as possible.
          </h1>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Tenant isolation enforced in three independent layers, mandatory MFA with a fresh
            re-check before every high-risk action, encryption at rest, and an append-only audit
            trail that can&apos;t be edited even by a compromised application connection.
          </p>
          <div>
            <Button asChild variant="brand" size="lg">
              <Link href="/signup">Start hiring with Phantom</Link>
            </Button>
          </div>
        </div>

        <TenantIsolationMockup />
      </div>
    </section>
  );
}
