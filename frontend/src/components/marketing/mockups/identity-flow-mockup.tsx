import { Building2, ChevronDown, EyeOff, ShieldCheck, UserRound } from "lucide-react";

const STEPS = [
  { icon: UserRound, title: "Phantom Passport", body: "Professional identity" },
  { icon: EyeOff, title: "Shadow", body: "Anonymous Callsign" },
  { icon: Building2, title: "Company", body: "Protected profile" },
  { icon: ShieldCheck, title: "Reveal Request", body: "Candidate decides" },
];

export function IdentityFlowMockup() {
  return (
    <div className="flex flex-col items-center gap-1 rounded-2xl border border-border bg-white p-6 shadow-sm shadow-slate-900/[0.03]">
      {STEPS.map((step, i) => (
        <div key={step.title} className="flex w-full flex-col items-center gap-1">
          <div className="flex w-full items-center gap-3 rounded-xl border border-border bg-secondary/40 px-4 py-3">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand/10 text-brand">
              <step.icon className="h-4 w-4" />
            </div>
            <div className="flex flex-col">
              <p className="text-sm font-semibold text-foreground">{step.title}</p>
              <p className="text-xs text-muted-foreground">{step.body}</p>
            </div>
          </div>
          {i < STEPS.length - 1 && (
            <ChevronDown className="h-4 w-4 shrink-0 text-muted-foreground/40" aria-hidden />
          )}
        </div>
      ))}
    </div>
  );
}
