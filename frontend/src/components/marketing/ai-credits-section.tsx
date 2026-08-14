import { Sparkles } from "lucide-react";

import { AI_CREDIT_PACKS, COMPANY_PLANS } from "@/lib/pricing-config";

export function AiCreditsSection() {
  return (
    <section className="border-t border-border bg-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <div className="mx-auto inline-flex items-center gap-2 rounded-full border border-border bg-white px-3.5 py-1.5">
            <Sparkles className="h-3.5 w-3.5 text-brand" />
            <span className="text-xs font-medium text-muted-foreground">
              AI that scales with your hiring
            </span>
          </div>
          <p className="mt-5 text-lg leading-relaxed text-muted-foreground">
            Candidate volume shouldn&apos;t be the bottleneck. Intelligence is where Phantom&apos;s
            infrastructure does the heavy lifting, so AI compute is what&apos;s metered, not how
            many CVs, applications or candidates move through your pipeline.
          </p>
        </div>

        <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {COMPANY_PLANS.map((plan) => (
            <div
              key={plan.id}
              className="flex flex-col gap-2 rounded-2xl border border-border bg-white p-5 shadow-sm shadow-slate-900/[0.03]"
            >
              <p className="text-sm font-semibold text-foreground">{plan.name}</p>
              <p className="text-xs leading-relaxed text-muted-foreground">
                {plan.aiAllowance.label}
              </p>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-center gap-6">
          <p className="text-sm font-medium text-foreground">Need more?</p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {AI_CREDIT_PACKS.map((pack) => (
              <div
                key={pack.id}
                className="flex flex-col items-center gap-1 rounded-2xl border border-border bg-white px-8 py-6 text-center shadow-sm shadow-slate-900/[0.03]"
              >
                <span className="text-2xl font-semibold tracking-tight text-foreground">
                  £{pack.price}
                </span>
                <span className="text-xs text-muted-foreground">
                  {pack.credits.toLocaleString("en-GB")} AI credits
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
