import Image from "next/image";
import { Check } from "lucide-react";

import { VERIFICATION_STATUS_LABEL } from "@/lib/status-display";

// A standalone "ID card" visual — deliberately NOT wrapped in BrowserFrame, a different visual
// language from every other (browser-screenshot-style) mockup on the site, reserved for this one
// flagship focal moment. Gold is used here purely as a decorative accent (hex badge, checklist
// icons, QR-style texture) — it never labels a tier. Shows the real single-state verification
// field (VERIFICATION_STATUS_LABEL.verified), not an invented Bronze/Silver/Gold/Platinum tier —
// no such tier exists in the real VerificationStatus enum (only unverified/pending/verified). The
// 3-item checklist uses real Passport mechanics (approved version, encrypted personal info,
// identity sealed until reveal), not a fabricated Identity/Employment/Credentials breakdown — no
// such category set exists in the real data model. The QR-style grid is decorative card texture,
// not a real scan feature. Illustrative sample data (Pulse-78), same convention as every other
// Passport mockup on the site.
const SKILLS = ["Senior Backend", "Distributed Systems", "Payments", "Team Leadership"];

const VERIFICATION_CHECKS = [
  "Profile reviewed & approved",
  "Personal info encrypted",
  "Identity sealed until reveal",
];

const QR_ROWS = ["1110101", "1010111", "1110010", "0001101", "1011100", "0100111", "1101010"];

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

      <div className="relative flex w-32 shrink-0 flex-col items-center gap-3.5 bg-[#100b1f] px-3 py-6">
        <div
          className="absolute left-1/2 top-7 h-20 w-20 -translate-x-1/2 rounded-full bg-[#d4af6a]/25 blur-2xl"
          aria-hidden
        />

        <div className="relative z-10 h-16 w-16 shrink-0">
          <div
            className="absolute inset-0 bg-gradient-to-b from-[#f5da9c] via-[#d4af6a] to-[#a8822f]"
            style={{ clipPath: "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)" }}
            aria-hidden
          />
          <div
            className="absolute inset-[3px] bg-[#100b1f]"
            style={{ clipPath: "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)" }}
            aria-hidden
          />
          <div className="absolute inset-0 flex items-center justify-center">
            <Image src="/phantom-icon.png" alt="" width={234} height={190} className="h-8 w-auto" />
          </div>
        </div>

        <div className="relative z-10 flex flex-col items-center gap-0.5">
          <p className="text-center text-[9px] font-semibold uppercase tracking-[0.2em] text-[#d4af6a]/70">
            Verification
          </p>
          <p className="text-center text-base font-bold uppercase tracking-wide text-[#e8c988]">
            {VERIFICATION_STATUS_LABEL.verified}
          </p>
        </div>

        <div className="relative z-10 flex w-full flex-col gap-2 border-t border-[#d4af6a]/20 pt-3">
          {VERIFICATION_CHECKS.map((check) => (
            <div key={check} className="flex items-start gap-1.5">
              <div className="mt-0.5 flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full bg-[#d4af6a]">
                <Check className="h-2 w-2 text-[#100b1f]" strokeWidth={4} />
              </div>
              <p className="text-[9px] leading-tight text-white/75">{check}</p>
            </div>
          ))}
        </div>

        <div className="relative z-10 mt-auto flex flex-col items-center gap-1.5">
          <div className="grid grid-cols-7 gap-[1.5px] rounded-sm bg-white p-1.5">
            {QR_ROWS.flatMap((row, r) =>
              row.split("").map((cell, c) => (
                <span
                  key={`${r}-${c}`}
                  className={cell === "1" ? "h-[2.5px] w-[2.5px] bg-[#100b1f]" : "h-[2.5px] w-[2.5px]"}
                />
              ))
            )}
          </div>
          <p className="text-center text-[8px] font-semibold uppercase tracking-[0.15em] text-[#d4af6a]/60">
            Private by design
          </p>
        </div>
      </div>
    </div>
  );
}
