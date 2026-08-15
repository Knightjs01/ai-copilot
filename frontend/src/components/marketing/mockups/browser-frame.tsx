import { Lock } from "lucide-react";

export function BrowserFrame({
  url,
  badge,
  children,
}: {
  url: string;
  badge?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="relative w-full overflow-hidden rounded-2xl border border-border bg-card shadow-xl shadow-slate-900/[0.08]">
      {badge && (
        <span className="absolute right-4 top-4 z-10 rounded-full bg-brand px-3 py-1 text-xs font-semibold text-brand-foreground shadow-sm">
          {badge}
        </span>
      )}

      <div className="flex items-center gap-1.5 border-b border-border bg-secondary/60 px-4 py-2.5">
        <span className="h-2.5 w-2.5 rounded-full bg-danger/40" aria-hidden />
        <span className="h-2.5 w-2.5 rounded-full bg-warning/40" aria-hidden />
        <span className="h-2.5 w-2.5 rounded-full bg-success/40" aria-hidden />
        <div className="mx-auto flex items-center gap-1.5 rounded-full bg-background px-3 py-1 text-xs text-muted-foreground">
          <Lock className="h-3 w-3" />
          {url}
        </div>
      </div>

      <div className="bg-secondary/20 p-4 sm:p-6">{children}</div>
    </div>
  );
}
