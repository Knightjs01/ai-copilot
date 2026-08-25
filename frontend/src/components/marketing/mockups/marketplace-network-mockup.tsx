import type { CSSProperties } from "react";
import { Briefcase, EyeOff, Sparkles, type LucideIcon } from "lucide-react";

// A network/marketplace diagram, not an identity card -- deliberately a different visual
// language from PassportIdCardMockup, HeroShowcaseMockup and every other "card" mockup on the
// site, since the Passport already gets its own dedicated section immediately below the hero.
// Purely conceptual: anonymous candidates on one side, companies on the other, Phantom AI
// matching between them. No names, no fabricated numbers, nothing that could be mistaken for a
// real screenshot -- just the shape of the marketplace itself.

const CANDIDATE_NODES = [
  { top: "16%", left: "10%" },
  { top: "50%", left: "6%" },
  { top: "84%", left: "10%" },
];

const COMPANY_NODES = [
  { top: "28%", left: "92%" },
  { top: "72%", left: "92%" },
];

function Node({
  style,
  icon: Icon,
  tone,
}: {
  style: CSSProperties;
  icon: LucideIcon;
  tone: "brand" | "electric";
}) {
  return (
    <div
      className={
        tone === "brand"
          ? "absolute flex h-11 w-11 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-brand/30 bg-card text-brand shadow-sm"
          : "absolute flex h-11 w-11 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border border-electric/30 bg-card text-electric shadow-sm"
      }
      style={style}
    >
      <Icon className="h-4 w-4" />
    </div>
  );
}

export function MarketplaceNetworkMockup() {
  return (
    <div className="relative mx-auto w-full max-w-sm">
      <div
        className="absolute -inset-2 rounded-[28px] bg-gradient-to-br from-brand/20 via-electric/10 to-brand/20 blur-2xl"
        aria-hidden
      />

      <div className="relative rounded-3xl border border-border bg-card p-6 shadow-xl">
        <div className="relative aspect-square w-full">
          <svg
            viewBox="0 0 100 100"
            className="absolute inset-0 h-full w-full text-brand/25"
            aria-hidden
          >
            {CANDIDATE_NODES.map((node, i) => (
              <line
                key={`c-${i}`}
                x1={parseFloat(node.left)}
                y1={parseFloat(node.top)}
                x2={50}
                y2={50}
                stroke="currentColor"
                strokeWidth={0.6}
              />
            ))}
            {COMPANY_NODES.map((node, i) => (
              <line
                key={`e-${i}`}
                x1={50}
                y1={50}
                x2={parseFloat(node.left)}
                y2={parseFloat(node.top)}
                stroke="currentColor"
                strokeWidth={0.6}
              />
            ))}
          </svg>

          <div className="absolute left-1/2 top-1/2 flex h-16 w-16 -translate-x-1/2 -translate-y-1/2 flex-col items-center justify-center rounded-full bg-brand text-brand-foreground shadow-lg shadow-brand/30">
            <Sparkles className="h-6 w-6" />
          </div>

          {CANDIDATE_NODES.map((node, i) => (
            <Node key={i} style={node} icon={EyeOff} tone="brand" />
          ))}
          {COMPANY_NODES.map((node, i) => (
            <Node key={i} style={node} icon={Briefcase} tone="electric" />
          ))}

          <p className="absolute left-[10%] top-[4%] -translate-x-1/2 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            Candidates
          </p>
          <p className="absolute left-[92%] top-[14%] -translate-x-1/2 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">
            Companies
          </p>
          <p className="absolute left-1/2 top-[68%] -translate-x-1/2 text-center text-[10px] font-semibold uppercase tracking-wide text-brand">
            Phantom AI
          </p>
        </div>

        <p className="mt-4 text-center text-sm leading-relaxed text-muted-foreground">
          Anonymous talent, matched privately by AI, revealed only on the candidate&apos;s terms.
        </p>
      </div>
    </div>
  );
}
