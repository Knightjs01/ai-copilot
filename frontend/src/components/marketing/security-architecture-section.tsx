import { FileClock, Gauge, KeyRound, Lock, ShieldCheck } from "lucide-react";

// Each point is grounded precisely in a real SECURITY.md section — no invented claims,
// no compliance certifications that don't exist.
const PILLARS = [
  {
    icon: ShieldCheck,
    title: "Tenant isolation",
    body: "Three independent layers protect every candidate and project record: no database grant, Row-Level Security, and an application-layer re-check.",
  },
  {
    icon: KeyRound,
    title: "Mandatory MFA & step-up",
    body: "Every account enrolls in MFA. High-risk actions — inviting a teammate, revealing an identity, purging a project — require a fresh password-and-code check first.",
  },
  {
    icon: Lock,
    title: "Encryption at rest",
    body: "Candidate PII, resume files, and MFA secrets are encrypted the moment they're stored, never held in plaintext.",
  },
  {
    icon: FileClock,
    title: "Append-only audit log",
    body: "Every login, reveal, and purge is recorded. The audit table itself can't be edited or deleted, even by a compromised application connection.",
  },
  {
    icon: Gauge,
    title: "Rate limiting",
    body: "Per-IP and per-account limits work together, so credential stuffing spread across many addresses is still caught.",
  },
];

export function SecurityArchitectureSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">Architecture</p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Five real mechanisms, not a badge.
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {PILLARS.map((pillar) => (
            <div
              key={pillar.title}
              className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <pillar.icon className="h-5 w-5" />
              </div>
              <h3 className="text-sm font-semibold text-foreground">{pillar.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{pillar.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
