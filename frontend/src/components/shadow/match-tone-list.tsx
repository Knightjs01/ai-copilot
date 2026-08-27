import { AlertTriangle, CheckCircle2 } from "lucide-react";

export function MatchToneList({
  title,
  items,
  tone,
}: {
  title: string;
  items: string[];
  tone: "positive" | "caution";
}) {
  if (items.length === 0) return null;
  const Icon = tone === "positive" ? CheckCircle2 : AlertTriangle;
  return (
    <div>
      <h4 className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h4>
      <ul
        className={
          tone === "positive"
            ? "flex flex-col gap-1.5 rounded-xl border border-success/20 bg-success/5 p-3"
            : "flex flex-col gap-1.5 rounded-xl border border-warning/20 bg-warning/5 p-3"
        }
      >
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-foreground">
            <Icon
              className={
                tone === "positive"
                  ? "mt-0.5 h-3.5 w-3.5 shrink-0 text-success"
                  : "mt-0.5 h-3.5 w-3.5 shrink-0 text-warning"
              }
            />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
