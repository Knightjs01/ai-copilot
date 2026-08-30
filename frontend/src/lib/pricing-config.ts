// Single source of truth for everything the /pricing page renders. Static content (taglines,
// feature copy, comparison rows, CTAs) lives here directly. Prices and active-role limits are
// NOT hardcoded here -- they're fetched from the real `commercial_plans` table (see
// getCommercialPlans below) so a future price/limit change never needs a second place updated.
// FALLBACK_PLAN_NUMBERS exists only for when that fetch fails; keep it in sync with the real
// current values in commercial_plans (seeded in 0062_commercial_plans.py, last updated by
// 0066_commercial_plan_price_update.py) if those ever diverge.

export type BillingPeriod = "monthly" | "annual";

export type CompanyPlanId = "core" | "growth" | "scale";

export interface CompanyPlan {
  id: CompanyPlanId;
  name: string;
  tagline: string;
  /** In whole pounds (converted from the backend's pence). null only ever happens if the public
   *  endpoint is unreachable AND this plan is missing from FALLBACK_PLAN_NUMBERS -- shouldn't
   *  happen in practice, but price=null renders "Custom" rather than crashing. */
  price: { monthly: number | null; annual: number | null };
  /** From the backend. null = no fixed cap configured (Scale's default -- capacity is
   *  negotiated per company via an admin override, see commercial/service.py). */
  activeRoleLimit: number | null;
  /** Scale's price is a floor, not a fixed fee -- shown as "From £899/month". */
  priceIsFrom?: boolean;
  mostPopular?: boolean;
  /** The highlights shown on the plan card itself (an "active roles" bullet is injected at
   *  render time from the real limit -- see withActiveRoleBullet). See getFeatureComparisonRows
   *  for the full, categorised feature list shown further down the page. */
  features: string[];
  cta: { label: string; href: string };
}

/** Computed, never hardcoded, so the "Save ~X%" badge always matches the real numbers above. */
export function annualSavingsPercent(plan: CompanyPlan): number | null {
  if (plan.price.monthly === null || plan.price.annual === null) return null;
  return Math.round((1 - plan.price.annual / (plan.price.monthly * 12)) * 100);
}

/** Human phrasing for a plan's active-role capacity, derived entirely from real numbers so it
 *  can never drift from what's actually enforced. Core = "Up to N"; Growth = the range starting
 *  right after Core's limit; Scale = "N+" starting right after Growth's limit (or "Configurable"
 *  if Scale itself has no override-driven limit to show here, which is the common case). */
export function activeRoleRangeLabel(planId: CompanyPlanId, plans: CompanyPlan[]): string {
  const core = plans.find((p) => p.id === "core");
  const growth = plans.find((p) => p.id === "growth");
  const plan = plans.find((p) => p.id === planId);
  if (!plan) return "";

  if (planId === "core") {
    return plan.activeRoleLimit !== null ? `Up to ${plan.activeRoleLimit}` : "Unlimited";
  }
  if (planId === "growth") {
    const lower = core?.activeRoleLimit !== null && core?.activeRoleLimit !== undefined
      ? core.activeRoleLimit + 1
      : 1;
    return plan.activeRoleLimit !== null ? `${lower}–${plan.activeRoleLimit}` : `${lower}+`;
  }
  // scale
  const lower = growth?.activeRoleLimit !== null && growth?.activeRoleLimit !== undefined
    ? growth.activeRoleLimit + 1
    : 1;
  return plan.activeRoleLimit !== null ? `${lower}–${plan.activeRoleLimit}` : `${lower}+`;
}

type PlanContent = Omit<CompanyPlan, "price" | "activeRoleLimit">;

const PLAN_CONTENT: PlanContent[] = [
  {
    id: "core",
    name: "Phantom Core",
    tagline: "For lean talent teams.",
    features: [
      "Full ATS — jobs, pipeline & interviews",
      "Shadow job advertising & company profile",
      "Anonymous candidate applications",
      "Candidate Passport matching",
      "AI-powered hiring included",
      "Candidate messaging & collaboration",
      "Verified employer status",
    ],
    cta: { label: "Start with Phantom", href: "/signup" },
  },
  {
    id: "growth",
    name: "Phantom Growth",
    tagline: "For growing talent teams.",
    mostPopular: true,
    features: [
      "Everything in Core, plus:",
      "Enhanced employer branding — banner, culture, benefits",
      "Advanced talent discovery & candidate search",
      "Hiring funnel & conversion analytics",
      "More AI usage & candidate discovery capacity",
      "More talent users",
      "Hiring velocity reporting",
    ],
    cta: { label: "Choose Growth", href: "/signup" },
  },
  {
    id: "scale",
    name: "Phantom Scale",
    tagline: "For established talent teams.",
    priceIsFrom: true,
    features: [
      "Everything in Growth, plus:",
      "Multiple hiring teams & advanced permissions",
      "Advanced AI & candidate discovery",
      "Phantom Stories & team profiles",
      "Featured opportunities placement",
      "Enterprise security & audit controls",
      "Priority support",
    ],
    cta: { label: "Talk to Phantom", href: "mailto:sales@phantomhire.com?subject=Phantom%20Scale" },
  },
];

const FALLBACK_PLAN_NUMBERS: Record<
  CompanyPlanId,
  { monthly: number | null; annual: number | null; activeRoleLimit: number | null }
> = {
  core: { monthly: 349, annual: 3490, activeRoleLimit: 5 },
  growth: { monthly: 599, annual: 5990, activeRoleLimit: 10 },
  scale: { monthly: 899, annual: 8990, activeRoleLimit: null },
};

interface PublicCommercialPlan {
  code: string;
  name: string;
  monthly_price_pence: number;
  annual_price_pence: number;
  active_role_limit: number | null;
}

function withActiveRoleBullet(plan: CompanyPlan, allPlans: CompanyPlan[]): CompanyPlan {
  const bullet = `${activeRoleRangeLabel(plan.id, allPlans)} active roles`;
  const insertIndex = plan.features[0]?.startsWith("Everything in") ? 1 : 0;
  const features = [...plan.features];
  features.splice(insertIndex, 0, bullet);
  return { ...plan, features };
}

/** Server-side only (calls fetch directly, no client API-client wrapper -- marketing pages have
 *  no candidate/company session to attach). Falls back to FALLBACK_PLAN_NUMBERS on any failure
 *  so /pricing never renders blank or throws just because the API is briefly unreachable. */
export async function getCommercialPlans(): Promise<CompanyPlan[]> {
  let fetched: PublicCommercialPlan[] | null = null;
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
    const res = await fetch(`${apiUrl}/api/v1/commercial/plans`, {
      next: { revalidate: 300 },
    });
    if (res.ok) {
      fetched = (await res.json()) as PublicCommercialPlan[];
    }
  } catch {
    // Network/parse failure — fall through to the hardcoded fallback below.
  }

  const merged = PLAN_CONTENT.map((content): CompanyPlan => {
    const remote = fetched?.find((p) => p.code === content.id);
    const numbers = remote
      ? {
          monthly: remote.monthly_price_pence / 100,
          annual: remote.annual_price_pence / 100,
          activeRoleLimit: remote.active_role_limit,
        }
      : FALLBACK_PLAN_NUMBERS[content.id];
    return {
      ...content,
      price: { monthly: numbers.monthly, annual: numbers.annual },
      activeRoleLimit: numbers.activeRoleLimit,
    };
  });

  return merged.map((plan) => withActiveRoleBullet(plan, merged));
}

export type FeatureCategory =
  | "Hiring"
  | "Talent Discovery"
  | "AI"
  | "Employer Brand"
  | "Insights"
  | "Control";

export interface FeatureRow {
  category: FeatureCategory;
  label: string;
  values: Record<CompanyPlanId, boolean | string>;
}

// "Talent rediscovery" is deliberately never a plain checkmark -- Talent Memory has zero real
// backend today (confirmed exhaustively this session). Shown as "Preview" in every column that
// includes it, never sold as a live, paid-for feature. See PricingTrustSection/
// TalentMemorySection for the same rule applied elsewhere.
export function getFeatureComparisonRows(plans: CompanyPlan[]): FeatureRow[] {
  const activeRoles: Record<CompanyPlanId, string> = {
    core: activeRoleRangeLabel("core", plans),
    growth: activeRoleRangeLabel("growth", plans),
    scale: activeRoleRangeLabel("scale", plans),
  };

  return [
    // Hiring
    { category: "Hiring", label: "ATS", values: { core: true, growth: true, scale: true } },
    { category: "Hiring", label: "Active roles", values: activeRoles },
    {
      category: "Hiring",
      label: "Candidate pipeline & kanban",
      values: { core: true, growth: true, scale: true },
    },
    {
      category: "Hiring",
      label: "Interview scorecards",
      values: { core: true, growth: true, scale: true },
    },
    {
      category: "Hiring",
      label: "Hiring collaboration",
      values: { core: true, growth: true, scale: true },
    },
    // Talent Discovery
    {
      category: "Talent Discovery",
      label: "Shadow",
      values: { core: true, growth: true, scale: true },
    },
    {
      category: "Talent Discovery",
      label: "Anonymous candidate applications",
      values: { core: true, growth: true, scale: true },
    },
    {
      category: "Talent Discovery",
      label: "Candidate Passport",
      values: { core: true, growth: true, scale: true },
    },
    {
      category: "Talent Discovery",
      label: "Candidate search",
      values: { core: "Basic", growth: "Advanced", scale: "Advanced" },
    },
    {
      category: "Talent Discovery",
      label: "Talent rediscovery (Preview)",
      values: { core: false, growth: "Preview", scale: "Preview" },
    },
    // AI
    {
      category: "AI",
      label: "AI-powered hiring tools",
      values: { core: true, growth: true, scale: true },
    },
    {
      category: "AI",
      label: "Candidate & job intelligence",
      values: { core: true, growth: true, scale: true },
    },
    {
      category: "AI",
      label: "Advanced AI matching",
      values: { core: false, growth: false, scale: true },
    },
    // Employer Brand
    {
      category: "Employer Brand",
      label: "Company profile & logo",
      values: { core: true, growth: true, scale: true },
    },
    {
      category: "Employer Brand",
      label: "Banner, culture & benefits",
      values: { core: false, growth: true, scale: true },
    },
    {
      category: "Employer Brand",
      label: "Media & video",
      values: { core: false, growth: true, scale: true },
    },
    {
      category: "Employer Brand",
      label: "Phantom Stories & team profiles",
      values: { core: false, growth: false, scale: true },
    },
    {
      category: "Employer Brand",
      label: "Featured opportunities",
      values: { core: false, growth: false, scale: true },
    },
    // Insights
    {
      category: "Insights",
      label: "Core reporting",
      values: { core: true, growth: true, scale: true },
    },
    {
      category: "Insights",
      label: "Hiring funnel & conversion analytics",
      values: { core: false, growth: true, scale: true },
    },
    {
      category: "Insights",
      label: "Advanced analytics",
      values: { core: false, growth: false, scale: true },
    },
    // Control
    {
      category: "Control",
      label: "Team collaboration",
      values: { core: true, growth: true, scale: true },
    },
    {
      category: "Control",
      label: "Advanced permissions & multiple hiring teams",
      values: { core: false, growth: false, scale: true },
    },
    {
      category: "Control",
      label: "Enterprise security & audit controls",
      values: { core: false, growth: false, scale: true },
    },
    {
      category: "Control",
      label: "Custom integrations & usage policies",
      values: { core: false, growth: false, scale: true },
    },
    {
      category: "Control",
      label: "Priority support",
      values: { core: false, growth: false, scale: true },
    },
  ];
}
