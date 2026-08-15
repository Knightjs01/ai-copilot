import { Check, X } from "lucide-react";

const ROWS = [
  { label: "CV storage", traditional: false, phantom: false },
  { label: "Anonymous candidate marketplace", traditional: false, phantom: true },
  { label: "Candidate Passport", traditional: false, phantom: true },
  { label: "Candidate-controlled identity reveal", traditional: false, phantom: true },
  { label: "AI interview co-pilot", traditional: false, phantom: true },
  { label: "Talent Memory & future rediscovery", traditional: false, phantom: true },
  { label: "Zero-Retention project purge", traditional: false, phantom: true },
  { label: "Project Vault", traditional: false, phantom: true },
  { label: "Verification levels", traditional: false, phantom: true },
  { label: "AI talent intelligence", traditional: false, phantom: true },
  { label: "Privacy-first architecture", traditional: false, phantom: true },
];

export function AtsComparisonSection() {
  return (
    <section className="border-t border-border">
      <div className="mx-auto max-w-4xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Why Phantom is different
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            A traditional ATS is a system of record. Phantom is a system of intelligence and
            privacy.
          </p>
        </div>

        <div className="mt-10 overflow-hidden rounded-2xl border border-border bg-card shadow-sm shadow-slate-900/[0.03]">
          <div className="grid grid-cols-3 border-b border-border bg-secondary/20 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            <div className="px-4 py-3">Capability</div>
            <div className="px-4 py-3 text-center">Traditional ATS</div>
            <div className="px-4 py-3 text-center text-brand">Phantom Hire</div>
          </div>
          {ROWS.map((row) => (
            <div key={row.label} className="grid grid-cols-3 border-b border-border last:border-b-0">
              <div className="px-4 py-3 text-sm text-foreground">{row.label}</div>
              <div className="flex items-center justify-center px-4 py-3">
                {row.traditional ? (
                  <Check className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <X className="h-4 w-4 text-muted-foreground/40" />
                )}
              </div>
              <div className="flex items-center justify-center bg-brand/5 px-4 py-3">
                {row.phantom ? (
                  <Check className="h-4 w-4 text-brand" />
                ) : (
                  <X className="h-4 w-4 text-muted-foreground/40" />
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
