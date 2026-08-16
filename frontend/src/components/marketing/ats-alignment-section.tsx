import { CheckCircle2, Circle, Flame } from "lucide-react";

const REQUIREMENTS = [
  { text: "5+ years leading distributed systems teams", met: true },
  { text: "Direct ownership of a production payments platform", met: true },
  { text: "Experience scaling an engineering org past 30 people", met: true },
  { text: "Public speaking or conference track record", met: false },
];

export function AtsAlignmentSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-12 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            Hiring manager alignment
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Hiring managers submit their priorities once. Not another meeting.
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            A hiring manager lists what actually matters for the role. Phantom AI compares every
            candidate&apos;s own record against that list, so recruiters see exactly what&apos;s
            evidenced and what still needs probing, without a status meeting.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              VP Engineering · top priorities
            </p>
            <ul className="mt-3 flex flex-col gap-2.5">
              {REQUIREMENTS.map((req) => (
                <li key={req.text} className="flex items-start gap-2.5 text-sm">
                  {req.met ? (
                    <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                  ) : (
                    <Circle className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                  )}
                  <span className={req.met ? "text-foreground" : "text-muted-foreground"}>
                    {req.text}
                  </span>
                </li>
              ))}
            </ul>
            <div className="mt-4 rounded-xl border border-brand/20 bg-brand/5 p-3">
              <p className="text-xs text-foreground">
                Cipher-05 meets 3 of 4 priorities, evidenced directly in their record.
              </p>
            </div>
          </div>

          <div className="rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
              <Flame className="h-4 w-4" />
            </div>
            <p className="mt-3 text-sm font-semibold text-foreground">Project Vault</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Every requirement, note, and AI insight for this project lives in its own Project
              Vault, purged when the search closes. Nothing lingers past the hire.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
