import { TrendingUp } from "lucide-react";

const INSIGHTS = [
  "Your salary band is 8% below the median for comparable candidates.",
  "You are competing with 37 companies for this skillset.",
  "Only 214 verified candidates appear to meet all 7 requirements.",
  "73% of applicants lack the required payments experience.",
  "Your biggest pipeline drop-off occurs between recruiter screen and hiring manager.",
  "12 candidates from previous hiring projects are strong matches.",
];

const ANALYTICS_TIERS = [
  {
    tier: "Basic analytics",
    items: ["Pipeline", "Time to hire", "Applications", "Source", "Interview stages"],
  },
  {
    tier: "Advanced analytics",
    items: [
      "Cost per hire",
      "Time in stage",
      "Recruiter performance",
      "Hiring manager performance",
      "Candidate conversion",
      "Source quality",
      "Offer acceptance",
      "Candidate drop-off",
    ],
  },
  {
    tier: "Phantom Intelligence",
    items: [
      "Talent market supply",
      "Skill scarcity",
      "Competitive hiring",
      "Salary intelligence",
      "Talent pool quality",
      "Historical talent rediscovery",
      "AI hiring recommendations",
      "Quality-of-hire insights",
    ],
  },
];

export function PhantomIntelligenceSection() {
  return (
    <section className="border-t border-border bg-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Your ATS tells you what happened. Phantom tells you what to do next.
          </h2>
        </div>

        <div className="mx-auto mt-10 grid max-w-3xl grid-cols-1 gap-3 sm:grid-cols-2">
          {INSIGHTS.map((insight) => (
            <div
              key={insight}
              className="flex items-start gap-2.5 rounded-xl border border-border bg-white p-4 shadow-sm shadow-slate-900/[0.03]"
            >
              <TrendingUp className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
              <p className="text-sm leading-relaxed text-foreground">{insight}</p>
            </div>
          ))}
        </div>

        <div className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-3">
          {ANALYTICS_TIERS.map((tier) => (
            <div
              key={tier.tier}
              className="flex flex-col gap-3 rounded-2xl border border-border bg-white p-6 shadow-sm shadow-slate-900/[0.03]"
            >
              <h3 className="text-sm font-semibold text-foreground">{tier.tier}</h3>
              <ul className="flex flex-col gap-1.5">
                {tier.items.map((item) => (
                  <li key={item} className="text-xs text-muted-foreground">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
