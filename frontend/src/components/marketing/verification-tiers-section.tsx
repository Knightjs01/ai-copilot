import { CheckCircle2, Info } from "lucide-react";

import {
  VERIFICATION_DISCLAIMER,
  VERIFICATION_TIERS,
} from "@/lib/pricing-config";

export function VerificationTiersSection() {
  return (
    <section className="border-t border-border bg-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Your Passport. Your level of verification.
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Verification levels are free for every candidate. They&apos;re a trust signal for
            companies, not a paywall.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {VERIFICATION_TIERS.map((tier) => (
            <div
              key={tier.id}
              className="flex flex-col gap-4 rounded-2xl border border-border bg-white p-6 shadow-sm shadow-slate-900/[0.03]"
            >
              <div>
                <p className="text-sm font-semibold uppercase tracking-wide text-foreground">
                  {tier.id}
                </p>
                <p className="text-xs text-muted-foreground">{tier.name}</p>
              </div>
              <p className="text-sm text-muted-foreground">{tier.description}</p>
              <ul className="flex flex-col gap-2">
                {tier.checksIncluded.map((check) => (
                  <li key={check} className="flex items-start gap-2">
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand" />
                    <span className="text-xs leading-relaxed text-foreground">{check}</span>
                  </li>
                ))}
              </ul>
              <span
                className={`mt-auto inline-flex w-fit items-center rounded-full border px-2.5 py-1 text-[10px] font-semibold tracking-wide ${tier.badgeColorClass}`}
              >
                {tier.badge}
              </span>
            </div>
          ))}
        </div>

        <div className="mx-auto mt-10 max-w-3xl rounded-2xl border border-border bg-white p-6 shadow-sm shadow-slate-900/[0.03]">
          <div className="flex items-start gap-3">
            <Info className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            <div className="flex flex-col gap-2">
              <p className="text-sm font-semibold text-foreground">
                Verification is trust, not rank.
              </p>
              <p className="text-sm leading-relaxed text-muted-foreground">
                A Gold or Platinum candidate does not automatically rank above a Bronze
                candidate. Matching primarily considers skills, experience, role requirements,
                candidate preferences, career fit and availability, then verification status. A
                perfect Bronze candidate can outrank an irrelevant Gold candidate.
              </p>
              <p className="text-sm leading-relaxed text-muted-foreground">
                {VERIFICATION_DISCLAIMER}
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
