import { Badge } from "@/components/ui/badge";
import { CANDIDATE_STATUS_COLUMNS, CANDIDATE_STATUS_LABEL } from "@/lib/status-display";

const FIT_TIERS = [
  {
    rating: "Strong Fit",
    variant: "success" as const,
    description: "Meets every must-have requirement, evidenced in their own record.",
  },
  {
    rating: "Good Fit",
    variant: "info" as const,
    description: "Meets most requirements, with a small evidence gap worth probing.",
  },
  {
    rating: "Possible Fit",
    variant: "warning" as const,
    description: "Some real overlap, but several requirements are unconfirmed.",
  },
  {
    rating: "Weak Fit",
    variant: "danger" as const,
    description: "Limited evidence of the role's core requirements.",
  },
];

export function AtsPipelineSection() {
  return (
    <section className="border-t border-border bg-secondary/20">
      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-12 px-6 py-16 lg:grid-cols-2 lg:py-20">
        <div className="flex flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">Pipeline</p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground">
            One pipeline, every stage.
          </h2>
          <p className="text-sm leading-relaxed text-muted-foreground">
            Every candidate moves through the same seven-stage pipeline, whether they applied
            through Shadow or were added directly. Nothing to configure.
          </p>
          <div className="flex flex-wrap items-center gap-2">
            {CANDIDATE_STATUS_COLUMNS.map((status) => (
              <span
                key={status}
                className="rounded-full border border-border bg-card px-3.5 py-1.5 text-xs font-medium text-foreground"
              >
                {CANDIDATE_STATUS_LABEL[status]}
              </span>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-brand">AI fit rating</p>
          <h2 className="text-3xl font-semibold tracking-tight text-foreground">
            A real rating, not a black-box score.
          </h2>
          <div className="flex flex-col gap-2.5">
            {FIT_TIERS.map((tier) => (
              <div
                key={tier.rating}
                className="flex items-start gap-3 rounded-xl border border-border bg-card p-3.5"
              >
                <Badge variant={tier.variant} className="mt-0.5 shrink-0">
                  {tier.rating}
                </Badge>
                <p className="text-sm text-muted-foreground">{tier.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
