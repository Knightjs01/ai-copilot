import { Badge } from "@/components/ui/badge";
import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";

// Real stage columns (a subset of CANDIDATE_STATUS_COLUMNS) with real FitRating badges — a
// genuinely different visual rhythm from the compact single-column hero dashboard mockup.
// Illustrative sample data, same convention as every other mockup on this site.
const COLUMNS = [
  {
    stage: "New",
    cards: [{ callsign: "Vertex-19", ref: "PH-2026-0044", fit: null }],
  },
  {
    stage: "Screening",
    cards: [
      { callsign: "Echo-14", ref: "PH-2026-0038", fit: "Good Fit", variant: "info" as const },
      { callsign: "Nova-32", ref: "PH-2026-0039", fit: "Possible Fit", variant: "warning" as const },
    ],
  },
  {
    stage: "Interviewing",
    cards: [{ callsign: "Cipher-05", ref: "PH-2026-0035", fit: "Strong Fit", variant: "success" as const }],
  },
  {
    stage: "Offer",
    cards: [{ callsign: "Atlas-91", ref: "PH-2026-0021", fit: "Strong Fit", variant: "success" as const }],
  },
];

export function AtsKanbanMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/projects/vp-engineering/candidates" badge="Live now">
      <div className="grid grid-cols-4 gap-2.5">
        {COLUMNS.map((column) => (
          <div key={column.stage} className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground">
                {column.stage}
              </p>
              <span className="font-mono text-[10px] tabular-nums text-muted-foreground/60">
                {column.cards.length}
              </span>
            </div>
            <div className="flex flex-col gap-2">
              {column.cards.map((card) => (
                <div
                  key={card.callsign}
                  className="flex flex-col gap-1.5 rounded-xl border border-border bg-card p-2.5"
                >
                  <p className="truncate font-mono text-xs font-medium text-foreground">{card.callsign}</p>
                  <p className="truncate font-mono text-[9px] text-muted-foreground/70">{card.ref}</p>
                  {card.fit && (
                    <Badge variant={card.variant} className="w-fit text-[10px]">
                      {card.fit}
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </BrowserFrame>
  );
}
