import { Badge } from "@/components/ui/badge";
import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";

// Real stage columns (a subset of CANDIDATE_STATUS_COLUMNS) with real FitRating badges — a
// genuinely different visual rhythm from the compact single-column hero dashboard mockup.
// Illustrative sample data, same convention as every other mockup on this site.
const COLUMNS = [
  {
    stage: "Screening",
    cards: [
      { callsign: "Echo-14", fit: "Good Fit", variant: "info" as const },
      { callsign: "Nova-32", fit: "Possible Fit", variant: "warning" as const },
    ],
  },
  {
    stage: "Interviewing",
    cards: [{ callsign: "Cipher-05", fit: "Strong Fit", variant: "success" as const }],
  },
  {
    stage: "Offer",
    cards: [{ callsign: "Atlas-91", fit: "Strong Fit", variant: "success" as const }],
  },
];

export function AtsKanbanMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/projects/vp-engineering/candidates" badge="Live now">
      <div className="grid grid-cols-3 gap-3">
        {COLUMNS.map((column) => (
          <div key={column.stage} className="flex flex-col gap-2">
            <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
              {column.stage}
            </p>
            <div className="flex flex-col gap-2">
              {column.cards.map((card) => (
                <div
                  key={card.callsign}
                  className="flex flex-col gap-2 rounded-xl border border-border bg-card p-2.5"
                >
                  <p className="truncate text-xs font-medium text-foreground">{card.callsign}</p>
                  <Badge variant={card.variant} className="w-fit text-[10px]">
                    {card.fit}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </BrowserFrame>
  );
}
