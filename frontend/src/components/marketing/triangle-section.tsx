import { Eye, ShieldCheck, Users } from "lucide-react";

const TRIANGLE = [
  {
    icon: ShieldCheck,
    quote: "Zero-Retention is the reason people trust Phantom.",
    body: "Every project is built to disappear. There's no growing archive of personal data sitting around to leak, get subpoenaed, or be misused, because it doesn't exist once the job is done.",
  },
  {
    icon: Users,
    quote: "Hidden talent is the reason companies buy it.",
    body: "Access to exceptional people who aren't on the open market, because they're not job-searching in public. They're quietly exploring through Phantom.",
  },
  {
    icon: Eye,
    quote: "Private job discovery is the reason candidates join it.",
    body: "Explore your next move without announcing it to your current employer, your network, or anyone but the companies you choose to meet.",
  },
];

export function TriangleSection() {
  return (
    <section id="triangle" className="border-t border-border bg-secondary/20">
      <div className="mx-auto max-w-6xl px-6 py-16 lg:py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
            Why it works
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            The product and the strategy sit on the same three-sided foundation.
          </p>
        </div>

        <div className="mt-14 grid grid-cols-1 gap-6 lg:grid-cols-3">
          {TRIANGLE.map((leg) => (
            <div
              key={leg.quote}
              className="flex flex-col gap-4 rounded-2xl border border-border bg-card p-7 shadow-sm shadow-slate-900/[0.03]"
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand/10 text-brand">
                <leg.icon className="h-5 w-5" />
              </div>
              <p className="text-lg font-semibold leading-snug text-foreground">{leg.quote}</p>
              <p className="text-sm leading-relaxed text-muted-foreground">{leg.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
