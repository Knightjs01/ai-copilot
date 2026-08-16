import Image from "next/image";
import { Check, Copy } from "lucide-react";

// A standalone "ID card" visual — deliberately NOT wrapped in BrowserFrame, a different visual
// language from every other (browser-screenshot-style) mockup on the site, reserved for this one
// flagship focal moment. Light theme with a gold outline glow. Per explicit direction, this card
// features a Gold-tier "Authentication Level" badge, an Identity/Employment/Credentials/Right to
// Work checklist, and a Passport ID + QR block — content that goes beyond the real product's
// current single-state VerificationStatus field (unverified/pending/verified only). Illustrative
// sample data (Pulse-78, kept consistent with every other Passport mockup on the site), same
// convention as every mockup on this page.

const SKILLS = ["Senior Leadership", "Product", "FinTech", "Payments"];

const CHECKS = ["Identity", "Employment", "Credentials", "Right to Work"];

const DISSOLVE_DOTS = [
  { top: "4%", left: "88%", size: 6, opacity: 0.7 },
  { top: "16%", left: "96%", size: 4, opacity: 0.5 },
  { top: "32%", left: "92%", size: 5, opacity: 0.6 },
  { top: "50%", left: "98%", size: 3, opacity: 0.4 },
  { top: "66%", left: "93%", size: 4, opacity: 0.5 },
  { top: "82%", left: "89%", size: 3, opacity: 0.3 },
];

const QR_ROWS = ["1110101", "1010111", "1110010", "0001101", "1011100", "0100111", "1101010"];

function GoldHexBadge({ size }: { size: number }) {
  return (
    <div className="relative shrink-0" style={{ height: size, width: size }}>
      <div
        className="absolute inset-0 bg-gradient-to-b from-[#f5da9c] via-[#d4af6a] to-[#a8822f]"
        style={{ clipPath: "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)" }}
        aria-hidden
      />
      <div
        className="absolute inset-[3px] bg-card"
        style={{ clipPath: "polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)" }}
        aria-hidden
      />
      <div className="absolute inset-0 flex items-center justify-center">
        <Image
          src="/phantom-icon.png"
          alt=""
          width={234}
          height={190}
          style={{ height: size * 0.52, width: "auto" }}
        />
      </div>
    </div>
  );
}

export function PassportIdCardMockup() {
  return (
    <div className="relative mx-auto w-full max-w-xs">
      <div
        className="absolute -inset-2 rounded-[28px] bg-gradient-to-br from-[#d4af6a]/40 via-brand/10 to-[#d4af6a]/40 blur-xl"
        aria-hidden
      />

      <div className="relative flex flex-col gap-5 rounded-3xl border-2 border-[#d4af6a] bg-card p-6 shadow-xl">
        <div className="flex items-start justify-between">
          <div className="flex flex-col gap-0.5">
            <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-[#8a6a1f]">
              Phantom
            </p>
            <p className="text-lg font-bold tracking-tight text-[#8a6a1f]">Passport</p>
          </div>
          <GoldHexBadge size={44} />
        </div>

        <div className="flex items-center gap-4">
          <div className="relative flex h-16 w-16 shrink-0 items-center justify-center rounded-full border-2 border-brand/40">
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
            <Image src="/phantom-icon.png" alt="" width={234} height={190} className="h-9 w-auto" />
          </div>
          <div className="flex flex-col gap-1">
            <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
              Callsign
            </p>
            <p className="text-xl font-bold tracking-tight text-foreground">Pulse-78</p>
            <span className="flex items-center gap-1.5 text-[11px] font-medium text-success">
              <span className="h-1.5 w-1.5 rounded-full bg-success" aria-hidden />
              Active
            </span>
          </div>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {SKILLS.map((skill) => (
            <span
              key={skill}
              className="rounded-full border border-border bg-secondary/40 px-2.5 py-1 text-[10px] text-foreground/80"
            >
              {skill}
            </span>
          ))}
        </div>

        <div className="flex flex-col gap-3 border-t border-border pt-4">
          <p className="text-[9px] font-semibold uppercase tracking-[0.15em] text-muted-foreground">
            Authentication Level
          </p>
          <div className="flex items-center gap-3">
            <GoldHexBadge size={52} />
            <div className="flex flex-col gap-0.5">
              <p className="text-xl font-extrabold uppercase tracking-wide text-[#8a6a1f]">Gold</p>
              <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-[#8a6a1f]/80">
                Verified
              </p>
            </div>
            <p className="text-[10px] leading-snug text-muted-foreground">
              You have completed advanced verification. Your profile is trusted and highly
              credible.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-x-2 border-t border-border pt-4">
          {CHECKS.map((check) => (
            <div key={check} className="flex flex-col items-center gap-1.5 text-center">
              <div className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#d4af6a]">
                <Check className="h-3 w-3 text-[#100b1f]" strokeWidth={4} />
              </div>
              <p className="text-[9px] leading-tight text-foreground/80">
                {check}
                <br />
                <span className="font-semibold text-foreground">Verified</span>
              </p>
            </div>
          ))}
        </div>

        <div className="flex items-center gap-3 rounded-2xl border border-border bg-secondary/30 p-3">
          <div className="grid grid-cols-7 gap-[1.5px] rounded-sm bg-white p-1.5" aria-hidden>
            {QR_ROWS.flatMap((row, r) =>
              row.split("").map((cell, c) => (
                <span
                  key={`${r}-${c}`}
                  className={cell === "1" ? "h-[2.5px] w-[2.5px] bg-[#100b1f]" : "h-[2.5px] w-[2.5px]"}
                />
              ))
            )}
          </div>
          <div className="flex flex-1 flex-col gap-0.5">
            <p className="text-[9px] font-semibold uppercase tracking-wide text-brand">
              Passport ID
            </p>
            <p className="text-sm font-bold tracking-tight text-foreground">PH-482-7X9K</p>
            <p className="text-[9px] text-muted-foreground">Scan to share Phantom Passport</p>
          </div>
          <button
            type="button"
            tabIndex={-1}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-border bg-card"
            aria-hidden
          >
            <Copy className="h-3.5 w-3.5 text-muted-foreground" />
          </button>
        </div>
      </div>
    </div>
  );
}
