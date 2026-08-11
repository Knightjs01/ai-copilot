import { BrowserFrame } from "@/components/marketing/mockups/browser-frame";

const STATS = [
  { label: "Live projects", value: "3" },
  { label: "Candidates in process", value: "14" },
  { label: "Pre-screen stage", value: "5" },
  { label: "Hiring manager stage", value: "3" },
];

const COLUMNS = [
  { title: "New", candidates: [{ callsign: "Pulse-78", ref: "PH-2026-0041" }] },
  {
    title: "Screening",
    candidates: [
      { callsign: "Echo-14", ref: "PH-2026-0038", tag: "Advance" },
      { callsign: "Nova-32", ref: "PH-2026-0039" },
    ],
  },
  { title: "Interviewing", candidates: [{ callsign: "Cipher-05", ref: "PH-2026-0035" }] },
  { title: "Offer", candidates: [{ callsign: "Atlas-91", ref: "PH-2026-0021", tag: "Offer sent" }] },
];

export function AtsMockup() {
  return (
    <BrowserFrame url="app.phantomhire.com/projects/senior-backend-engineer" badge="Live now">
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-foreground">Senior Backend Engineer</p>
            <p className="text-xs text-muted-foreground">Engineering</p>
          </div>
          <span className="rounded-full bg-info/10 px-2.5 py-1 text-xs font-medium text-info">Open</span>
        </div>

        <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
          {STATS.map((stat) => (
            <div key={stat.label} className="rounded-xl border border-border bg-white px-3 py-2.5">
              <p className="text-lg font-semibold leading-none text-foreground">{stat.value}</p>
              <p className="mt-1 text-[11px] leading-tight text-muted-foreground">{stat.label}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-2.5 sm:grid-cols-4">
          {COLUMNS.map((column) => (
            <div key={column.title} className="flex flex-col gap-2">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-muted-foreground">
                {column.title}
              </p>
              {column.candidates.map((candidate) => (
                <div
                  key={candidate.callsign}
                  className="rounded-lg border border-border bg-white p-2.5 shadow-sm"
                >
                  <p className="text-xs font-medium text-foreground">{candidate.callsign}</p>
                  <p className="text-[10px] text-muted-foreground">{candidate.ref}</p>
                  {candidate.tag && (
                    <span className="mt-1 inline-block rounded-full bg-brand/10 px-1.5 py-0.5 text-[10px] font-medium text-brand">
                      {candidate.tag}
                    </span>
                  )}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </BrowserFrame>
  );
}
