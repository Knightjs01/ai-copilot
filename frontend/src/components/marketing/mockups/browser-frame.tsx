import { Lock } from "lucide-react";

import { cn } from "@/lib/utils";

// Palantir-adjacent technical chrome: dot-grid backdrop, monospace system readouts, a live-pulse
// indicator for "Live now" badges specifically (never shown on "Preview" — that badge stays
// static since nothing behind it is actually live).
export function BrowserFrame({
  url,
  badge,
  children,
}: {
  url: string;
  badge?: string;
  children: React.ReactNode;
}) {
  const isLive = badge?.toLowerCase().includes("live");

  return (
    <div className="relative w-full overflow-hidden rounded-2xl border border-border bg-card shadow-xl shadow-slate-900/[0.08]">
      {badge && (
        <span
          className={cn(
            "absolute right-4 top-4 z-10 flex items-center gap-1.5 rounded-full px-3 py-1 font-mono text-[10px] font-semibold uppercase tracking-[0.12em] shadow-sm",
            isLive ? "bg-brand text-brand-foreground" : "bg-secondary text-muted-foreground"
          )}
        >
          {isLive && (
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-brand-foreground/60" />
              <span className="relative inline-flex h-1.5 w-1.5 rounded-full bg-brand-foreground" />
            </span>
          )}
          {badge}
        </span>
      )}

      <div className="flex items-center gap-1.5 border-b border-border bg-secondary/60 px-4 py-2.5">
        <span className="h-2.5 w-2.5 rounded-full bg-danger/40" aria-hidden />
        <span className="h-2.5 w-2.5 rounded-full bg-warning/40" aria-hidden />
        <span className="h-2.5 w-2.5 rounded-full bg-success/40" aria-hidden />
        <div className="mx-auto flex items-center gap-1.5 rounded-full bg-background px-3 py-1 font-mono text-[11px] tracking-tight text-muted-foreground">
          <Lock className="h-3 w-3 shrink-0" />
          {url}
        </div>
      </div>

      <div className="relative overflow-hidden bg-secondary/20">
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.05]"
          style={{
            backgroundImage:
              "radial-gradient(hsl(var(--foreground)) 0.6px, transparent 0.6px)",
            backgroundSize: "14px 14px",
          }}
          aria-hidden
        />
        <div className="relative p-4 sm:p-6">{children}</div>
      </div>
    </div>
  );
}
