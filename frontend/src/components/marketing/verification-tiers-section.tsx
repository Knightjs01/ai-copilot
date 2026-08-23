import { Info, TrendingUp } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { VERIFICATION_DISCLAIMER, VERIFICATION_ROADMAP } from "@/lib/pricing-config";
import { VERIFICATION_STATUS_LABEL, VERIFICATION_STATUS_VARIANT } from "@/lib/status-display";
import type { VerificationStatus } from "@/lib/types";

const STATUSES: { status: VerificationStatus; description: string }[] = [
  { status: "unverified", description: "The default for every new Passport." },
  { status: "pending", description: "A verification request has been made." },
  { status: "verified", description: "Confirmed by Phantom." },
];

export function VerificationTiersSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Your Passport. Your level of verification.
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Every Passport carries a real verification status — free for every candidate, and
            never a paywall.
          </p>
        </div>

        <div className="mx-auto mt-12 grid max-w-3xl grid-cols-1 gap-4 sm:grid-cols-3">
          {STATUSES.map(({ status, description }) => (
            <div
              key={status}
              className="flex flex-col gap-2 rounded-2xl border border-border bg-card p-5 text-center shadow-sm shadow-slate-900/[0.03]"
            >
              <Badge variant={VERIFICATION_STATUS_VARIANT[status]} className="mx-auto w-fit">
                {VERIFICATION_STATUS_LABEL[status]}
              </Badge>
              <p className="text-xs leading-relaxed text-muted-foreground">{description}</p>
            </div>
          ))}
        </div>

        <div className="mx-auto mt-14 flex max-w-2xl flex-col gap-5 text-center">
          <div className="flex items-center justify-center gap-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-brand">
              What we&apos;re building toward
            </p>
            <Badge variant="outline">Preview</Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            Not available today — the direction real verification is headed.
          </p>
        </div>

        <div className="mx-auto mt-6 grid max-w-3xl grid-cols-1 gap-3 sm:grid-cols-2">
          {VERIFICATION_ROADMAP.map((item) => (
            <div
              key={item}
              className="flex items-start gap-2.5 rounded-xl border border-dashed border-border bg-secondary/20 p-4"
            >
              <TrendingUp className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
              <p className="text-sm leading-relaxed text-muted-foreground">{item}</p>
            </div>
          ))}
        </div>

        <div className="mx-auto mt-10 max-w-3xl rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]">
          <div className="flex items-start gap-3">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            <p className="text-sm leading-relaxed text-muted-foreground">
              {VERIFICATION_DISCLAIMER}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
