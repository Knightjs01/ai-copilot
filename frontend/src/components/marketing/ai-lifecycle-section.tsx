import { CheckCircle2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";

export function AiLifecycleSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-12 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            The interview, bookended
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            AI prepares you. AI never runs the call.
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Phantom AI works before the interview and after it. What happens on the call is
            entirely yours.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]">
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Before the call
              </p>
              <Badge variant="success">Strong Fit</Badge>
            </div>
            <p className="text-sm leading-relaxed text-foreground/80">
              Generate a fit assessment straight from the role brief and the candidate&apos;s own
              record: strengths, gaps, and the exact questions worth asking.
            </p>
            <div className="mt-1 rounded-xl border border-border bg-secondary/30 p-3.5">
              <p className="flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
                <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-success" />
                Ready once the role brief and candidate record are both in
              </p>
            </div>
          </div>

          <div className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]">
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                After the call
              </p>
              <Badge variant="info">Handoff ready</Badge>
            </div>
            <p className="text-sm leading-relaxed text-foreground/80">
              Generate handoff recommendations for the hiring manager, drawn from the original
              evidence plus your own interview notes.
            </p>
            <div className="mt-1 rounded-xl border border-border bg-secondary/30 p-3.5">
              <p className="flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
                <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-success" />
                Only unlocks once you&apos;ve written up the interview — Phantom AI works from
                your notes, not instead of them
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
