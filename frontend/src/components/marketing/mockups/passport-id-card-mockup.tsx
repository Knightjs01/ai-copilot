import Image from "next/image";
import { BadgeCheck, Lock } from "lucide-react";

import { VERIFICATION_STATUS_LABEL } from "@/lib/status-display";

// A standalone "ID card" visual — deliberately NOT wrapped in BrowserFrame, a different visual
// language from every other (browser-screenshot-style) mockup on the site, reserved for this one
// flagship focal moment. Shows the real single-state verification field (VERIFICATION_STATUS_LABEL
// .verified) as one badge, not an invented Bronze/Silver/Gold/Platinum tier or a fabricated
// Identity/Employment/Credentials checklist — neither exists in the real VerificationStatus enum
// (only unverified/pending/verified). Real completion_percentage + Approved/Version copy replaces
// an invented "Passport ID" number. Illustrative sample data (Pulse-78), same convention as every
// other Passport mockup on the site.
const SKILLS = ["Senior Backend", "Distributed Systems", "Payments", "Team Leadership"];

const DISSOLVE_DOTS = [
  { top: "6%", left: "86%", size: 6, opacity: 0.7 },
  { top: "18%", left: "95%", size: 4, opacity: 0.5 },
  { top: "34%", left: "90%", size: 5, opacity: 0.6 },
  { top: "52%", left: "97%", size: 3, opacity: 0.4 },
  { top: "68%", left: "92%", size: 4, opacity: 0.5 },
  { top: "84%", left: "87%", size: 3, opacity: 0.3 },
];

export function PassportIdCardMockup() {
  return (
    <div className="relative mx-auto flex w-full max-w-sm overflow-hidden rounded-3xl border border-border bg-card shadow-2xl shadow-slate-900/20">
      <div className="flex flex-1 flex-col gap-5 p-6">
        <div className="flex flex-col gap-0.5">
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
            Phantom
          </p>
          <p className="text-lg font-bold tracking-tight text-brand">Passport</p>
        </div>

        <div className="relative mx-auto flex h-24 w-24 items-center justify-center rounded-full border-2 border-brand/40">
          {DISSOLVE_DOTS.map((dot, i) => (
            <span
              key={i}
              className="absolute rounded-full bg-brand"
              style={{
                top: dot.top,
                left: dot.left,
                width: dot.size,
                height: dot.size,
                opacity: dot.opacity,
              }}
              aria-hidden
            />
          ))}
          <Image
            src="/phantom-icon.png"
            alt=""
            width={234}
            height={190}
            className="h-14 w-auto"
          />
        </div>

        <div className="flex flex-col items-center gap-1 text-center">
          <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            Callsign
          </p>
          <p className="text-2xl font-bold tracking-tight text-foreground">Pulse-78</p>
        </div>

        <div className="flex flex-wrap justify-center gap-1.5">
          {SKILLS.map((skill) => (
            <span
              key={skill}
              className="rounded-full border border-border bg-secondary/40 px-2.5 py-1 text-[10px] text-foreground/80"
            >
              {skill}
            </span>
          ))}
        </div>

        <div className="mt-auto flex items-center justify-between rounded-xl border border-border bg-secondary/30 px-3 py-2.5">
          <span className="text-[11px] text-muted-foreground">92% complete</span>
          <span className="text-[11px] font-semibold text-brand">Approved · v3</span>
        </div>
      </div>

      <div className="relative flex w-28 shrink-0 flex-col items-center gap-4 bg-brand px-3 py-6">
        <div
          className="absolute left-1/2 top-9 h-16 w-16 -translate-x-1/2 rounded-full bg-electric/50 blur-2xl"
          aria-hidden
        />
        <div className="relative z-10 flex h-9 w-9 items-center justify-center rounded-full bg-brand-foreground/15">
          <BadgeCheck className="h-5 w-5 text-brand-foreground" />
        </div>
        <p className="relative z-10 text-center text-[9px] font-semibold uppercase tracking-[0.15em] text-brand-foreground/70">
          Verification
        </p>
        <p className="relative z-10 text-center text-sm font-bold uppercase tracking-wide text-brand-foreground">
          {VERIFICATION_STATUS_LABEL.verified}
        </p>
        <div className="relative z-10 mt-2 flex flex-col items-center gap-1.5 text-center">
          <Lock className="h-3.5 w-3.5 text-brand-foreground/70" />
          <p className="text-[9px] leading-snug text-brand-foreground/70">
            Identity sealed until you approve a reveal
          </p>
        </div>
        <div className="relative z-10 mt-auto flex flex-col items-center gap-1">
          <p className="text-[9px] font-semibold uppercase tracking-wide text-brand-foreground">
            Phantom Hire
          </p>
          <p className="text-[8px] text-brand-foreground/60">Private by design</p>
        </div>
      </div>
    </div>
  );
}
