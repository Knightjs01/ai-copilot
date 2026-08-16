import { EyeOff, Lock, UserCheck, Vault } from "lucide-react";

const PRIVACY_POINTS = [
  {
    icon: Vault,
    title: "Candidate Vault",
    body: "The original CV file you uploaded stays encrypted. Recruiters never see it — only the version you reviewed and approved.",
  },
  {
    icon: Lock,
    title: "Personal info, encrypted",
    body: "Your legal name, phone, and address are encrypted the moment they're collected, and never joined into anything a recruiter can query.",
  },
  {
    icon: EyeOff,
    title: "Callsign, not your name",
    body: "When you apply through Shadow, companies see a Callsign. Your name and photo stay hidden until you decide otherwise.",
  },
];

const REVEAL_REASONS = [
  "Hiring Manager Interview",
  "Offer Preparation",
  "Background Checks",
  "Client Submission",
  "Hiring Manager Review",
];

export function PassportPrivacySection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-16 lg:py-20">
        <div className="flex max-w-2xl flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">
            What stays private
          </p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            You approve every reveal, individually.
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          {PRIVACY_POINTS.map((point) => (
            <div
              key={point.title}
              className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <point.icon className="h-5 w-5" />
              </div>
              <h3 className="text-sm font-semibold text-foreground">{point.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{point.body}</p>
            </div>
          ))}
        </div>

        <div className="rounded-2xl border border-border bg-card p-6 shadow-sm shadow-slate-900/[0.03]">
          <div className="flex items-center gap-2.5">
            <UserCheck className="h-4 w-4 shrink-0 text-brand" />
            <p className="text-sm font-semibold text-foreground">Reveal Requests</p>
          </div>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            When a company wants to see your real identity, they submit a Reveal Request with a
            stated reason. You approve or decline it — nothing is automatic.
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {REVEAL_REASONS.map((reason) => (
              <span
                key={reason}
                className="rounded-full border border-border bg-secondary/40 px-3 py-1 text-xs text-foreground/80"
              >
                {reason}
              </span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
