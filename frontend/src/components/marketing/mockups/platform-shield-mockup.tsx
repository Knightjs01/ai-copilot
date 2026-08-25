import Image from "next/image";
import type { CSSProperties } from "react";
import { Briefcase, EyeOff, ShieldCheck, Sparkles, type LucideIcon } from "lucide-react";

// The homepage hero's primary visual: the Ghost mark at the centre, secured by a shield badge,
// with the three real product surfaces -- Shadow, Phantom ATS, Phantom AI -- radiating outward.
// Deliberately not a card mimicking the Candidate Passport (that has its own dedicated section
// right below the hero) -- this is the platform-level story instead: one Ghost, one security
// foundation, three products built on it. Every label names a real, shipped product surface; no
// fabricated data anywhere.

const PRODUCTS: { label: string; icon: LucideIcon; style: CSSProperties }[] = [
  { label: "Shadow", icon: EyeOff, style: { top: "10%", left: "50%" } },
  { label: "Phantom ATS", icon: Briefcase, style: { top: "82%", left: "14%" } },
  { label: "Phantom AI", icon: Sparkles, style: { top: "82%", left: "86%" } },
];

const LABEL_STYLE: Record<string, CSSProperties> = {
  Shadow: { top: "-2%", left: "50%" },
  "Phantom ATS": { top: "96%", left: "14%" },
  "Phantom AI": { top: "96%", left: "86%" },
};

export function PlatformShieldMockup() {
  return (
    <div className="relative mx-auto w-full max-w-sm">
      <div
        className="absolute -inset-2 rounded-[28px] bg-gradient-to-br from-brand/25 via-electric/15 to-brand/25 blur-2xl"
        aria-hidden
      />

      <div className="relative flex flex-col gap-5 rounded-3xl border border-border bg-card p-6 shadow-xl">
        <div className="flex items-center justify-center gap-2">
          <ShieldCheck className="h-3.5 w-3.5 text-brand" />
          <p className="text-[11px] font-semibold uppercase tracking-[0.15em] text-brand">
            One platform · Zero-Trust security
          </p>
        </div>

        <div className="relative aspect-square w-full">
          <svg viewBox="0 0 100 100" className="absolute inset-0 h-full w-full text-brand/25" aria-hidden>
            {PRODUCTS.map((product) => (
              <line
                key={product.label}
                x1={50}
                y1={50}
                x2={parseFloat(String(product.style.left))}
                y2={parseFloat(String(product.style.top))}
                stroke="currentColor"
                strokeWidth={0.6}
              />
            ))}
          </svg>

          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
            <div
              className="absolute -inset-3 rounded-full bg-brand/15 blur-lg"
              aria-hidden
            />
            <div className="relative flex h-20 w-20 items-center justify-center rounded-full border-2 border-brand bg-card shadow-lg">
              <Image src="/phantom-icon.png" alt="" width={234} height={190} className="h-9 w-auto" />
            </div>
            <div className="absolute -bottom-1 -right-1 flex h-7 w-7 items-center justify-center rounded-full border-2 border-card bg-brand text-brand-foreground">
              <ShieldCheck className="h-3.5 w-3.5" />
            </div>
          </div>

          {PRODUCTS.map((product) => (
            <div
              key={product.label}
              className="absolute flex h-11 w-11 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-electric/30 bg-card text-electric shadow-sm"
              style={product.style}
            >
              <product.icon className="h-4 w-4" />
            </div>
          ))}

          {PRODUCTS.map((product) => (
            <p
              key={product.label}
              className="absolute -translate-x-1/2 whitespace-nowrap text-[10px] font-semibold uppercase tracking-wide text-muted-foreground"
              style={LABEL_STYLE[product.label]}
            >
              {product.label}
            </p>
          ))}
        </div>

        <p className="text-center text-sm leading-relaxed text-muted-foreground">
          Shadow, Phantom ATS and Phantom AI, one Ghost, secured by Zero-Trust from the ground up.
        </p>
      </div>
    </div>
  );
}
