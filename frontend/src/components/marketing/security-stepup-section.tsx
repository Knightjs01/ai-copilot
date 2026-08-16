import { Fingerprint, ShieldAlert } from "lucide-react";

// The real list of actions gated by step-up re-auth today (SECURITY.md §4).
const STEP_UP_ACTIONS = [
  "Inviting a teammate",
  "Revealing a candidate's identity",
  "Purging a project",
  "Reading a revealed identity",
];

export function SecurityStepupSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col gap-12 px-6 py-16 lg:flex-row lg:items-start lg:py-20">
        <div className="flex flex-1 flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            Step-up, in practice
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Zero-Trust access, made concrete.
          </h2>
          <p className="text-lg leading-relaxed text-muted-foreground">
            Being signed in isn&apos;t enough for the actions that matter most. Before any of the
            below, Phantom asks for a fresh password and MFA code — no exceptions, regardless of
            how recently you logged in.
          </p>
          <ul className="flex flex-col gap-2.5">
            {STEP_UP_ACTIONS.map((action) => (
              <li key={action} className="flex items-start gap-2.5 text-sm">
                <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
                <span className="text-foreground/80">{action}</span>
              </li>
            ))}
          </ul>
        </div>

        <div className="flex flex-1 flex-col gap-4">
          <div className="flex items-start gap-3 rounded-2xl border border-border bg-card p-5 shadow-sm shadow-slate-900/[0.03]">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
              <span className="text-sm font-semibold">1</span>
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground">Fresh check requested</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Password plus MFA code, even if you signed in minutes ago.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3 rounded-2xl border border-brand/20 bg-brand/5 p-5">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
              <Fingerprint className="h-4 w-4" />
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground">Action proceeds</p>
              <p className="mt-1 text-sm text-muted-foreground">
                The check is short-lived and single-purpose — it can&apos;t be reused for anything
                else.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
