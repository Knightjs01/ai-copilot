import Image from "next/image";
import { Eye, Lock, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { FIT_RATING_VARIANT } from "@/lib/status-display";

// The homepage hero's primary visual. A layered two-card composite -- more visual depth than a
// single flat card, without becoming a full "app shell" screenshot (that's AtsAppShellMockup's
// job, further down the page). Every field is real: Callsign, the 4-tier FitRating (never a
// fabricated percentage, same rule as every other mockup on the site), and the single-state
// gold Verified badge. Distinct from PassportIdCardMockup (its own dedicated section right below
// this one) and from every other mockup already used elsewhere on the homepage.

const DISSOLVE_DOTS = [
  { top: "4%", left: "88%", size: 5, opacity: 0.7 },
  { top: "18%", left: "95%", size: 4, opacity: 0.5 },
  { top: "36%", left: "91%", size: 4, opacity: 0.6 },
  { top: "62%", left: "94%", size: 3, opacity: 0.4 },
  { top: "80%", left: "89%", size: 3, opacity: 0.3 },
];

export function HeroShowcaseMockup() {
  return (
    <div className="relative mx-auto w-full max-w-sm pr-6 pt-6">
      <div
        className="absolute -inset-2 rounded-[28px] bg-gradient-to-br from-brand/25 via-electric/15 to-brand/25 blur-2xl"
        aria-hidden
      />

      <div className="absolute -top-2 right-0 z-0 w-40 -rotate-6 rounded-2xl border border-border bg-card p-4 shadow-lg">
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand/10 text-brand">
          <Lock className="h-3.5 w-3.5" />
        </div>
        <p className="mt-2 text-[11px] font-semibold text-foreground">Identity Vault</p>
        <p className="text-[10px] leading-relaxed text-muted-foreground">
          Sealed until a candidate approves reveal.
        </p>
      </div>

      <div className="relative z-10 flex flex-col gap-5 rounded-3xl border border-brand/20 bg-card p-6 shadow-xl">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-[11px] font-medium text-success">
            <span className="h-1.5 w-1.5 rounded-full bg-success" aria-hidden />
            Live pipeline
          </span>
          <Badge variant="info">Interviewing</Badge>
        </div>

        <div className="flex items-center gap-4">
          <div className="relative flex h-14 w-14 shrink-0 items-center justify-center rounded-full border-2 border-brand/40">
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
            <Image src="/phantom-icon.png" alt="" width={234} height={190} className="h-8 w-auto" />
          </div>
          <div className="flex flex-col gap-1">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              Callsign
            </p>
            <p className="text-lg font-bold tracking-tight text-foreground">Pulse-78</p>
            <Badge variant="gold" className="w-fit">
              Verified
            </Badge>
          </div>
        </div>

        <div className="flex flex-col gap-2 rounded-2xl border border-border bg-secondary/30 p-3.5">
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-[11px] font-semibold text-foreground">
              <Sparkles className="h-3.5 w-3.5 text-brand" />
              AI fit assessment
            </span>
            <Badge variant={FIT_RATING_VARIANT["Strong Fit"]}>Strong Fit</Badge>
          </div>
          <p className="text-[11px] leading-relaxed text-muted-foreground">
            Evidence-based, from the role brief and the candidate&apos;s own record. Never a
            black-box score.
          </p>
        </div>

        <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
          <Eye className="h-3.5 w-3.5" />
          Identity reveal requires the candidate&apos;s approval
        </div>
      </div>
    </div>
  );
}
