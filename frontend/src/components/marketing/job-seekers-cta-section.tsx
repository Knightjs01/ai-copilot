import Link from "next/link";
import { Clock } from "lucide-react";

import { Button } from "@/components/ui/button";

export function JobSeekersCtaSection() {
  return (
    <section className="border-t border-border bg-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-20 lg:py-28">
        <div className="mx-auto flex flex-col items-center gap-5 rounded-3xl border border-border bg-white px-8 py-14 text-center shadow-sm shadow-slate-900/[0.03]">
          <Clock className="h-8 w-8 text-brand" />
          <h2 className="max-w-xl text-2xl font-semibold tracking-tight text-foreground sm:text-3xl">
            The Job Board and Candidate Portal are still in development
          </h2>
          <p className="max-w-lg text-muted-foreground">
            The ATS above — Callsigns, the Identity Vault, Zero-Retention — is real and live
            today. If the company you want to work for hires through Phantom, this is what your
            experience of it will look like once it ships.
          </p>
          <Button asChild variant="secondary" size="lg">
            <Link href="/hiring-teams">See what hiring teams get today</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
