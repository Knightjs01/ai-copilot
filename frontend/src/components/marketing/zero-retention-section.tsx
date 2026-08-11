import { Fingerprint, Flame, ScrollText, ShieldCheck, Sparkles, Vault } from "lucide-react";

const PILLARS = [
  {
    icon: Fingerprint,
    title: "Callsigns, not names",
    body: 'Every candidate gets an anonymous Callsign (like "Pulse-78") and a permanent Candidate ID. Recruiters work the entire pipeline without ever seeing a real name.',
  },
  {
    icon: Vault,
    title: "The Identity Vault",
    body: "Real names, emails, phone numbers and CVs are encrypted and locked away from the day-to-day workspace, revealed only by an Owner, with a reason, on the record.",
  },
  {
    icon: Sparkles,
    title: "Automatic redaction",
    body: "Every CV that touches Phantom's AI is stripped of personal details first. The model reasons about a candidate's skills, never their identity.",
  },
  {
    icon: Flame,
    title: "The Burn",
    body: "One click permanently destroys every trace of a hiring project: resumes, sanitized CVs, AI notes, identities. Not archived. Not soft-deleted. Gone on purpose.",
  },
  {
    icon: ShieldCheck,
    title: "The Purge Certificate",
    body: "Every burn produces a certificate confirming exactly what was destroyed and when: a receipt for the erasure, without a single re-identifiable detail in it.",
  },
  {
    icon: ScrollText,
    title: "The Historic Vault",
    body: "Only the critical, non-identifying facts survive the burn: project title, candidate count, purge certificate, audit trail. Enough to prove it happened. Never enough to re-identify anyone.",
  },
];

export function ZeroRetentionSection() {
  return (
    <section id="zero-retention" className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            What is Zero-Retention Hiring?
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Every other hiring platform asks you to trust it with your candidates&apos; personal
            data forever. Phantom Hire doesn&apos;t. Retention isn&apos;t a setting you turn off.
            It was never built in.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {PILLARS.map((pillar) => (
            <div
              key={pillar.title}
              className="flex flex-col gap-3 rounded-2xl border border-border bg-white p-6 shadow-sm shadow-slate-900/[0.03]"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 text-brand">
                <pillar.icon className="h-5 w-5" />
              </div>
              <h3 className="text-base font-semibold text-foreground">{pillar.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{pillar.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
