// Single source of truth for everything the /pricing page renders. Change a price or a feature
// here, not in the components that render it.

export type BillingPeriod = "monthly" | "annual";

export type CompanyPlanId = "core" | "network" | "intelligence" | "enterprise";

export interface CompanyPlan {
  id: CompanyPlanId;
  name: string;
  tagline: string;
  /** null = "Custom" pricing (Enterprise). `annual` is the real flat yearly price shown when the
   *  Annual toggle is selected (e.g. "£10,000/year") -- not a monthly-equivalent restatement. */
  price: { monthly: number | null; annual: number | null };
  mostPopular?: boolean;
  /** The 7-8 highlights shown on the plan card itself. See FEATURE_COMPARISON_ROWS for the full,
   *  categorised feature list shown further down the page. */
  features: string[];
  cta: { label: string; href: string };
}

/** Computed, never hardcoded, so the "Save ~X%" badge always matches the real numbers above. */
export function annualSavingsPercent(plan: CompanyPlan): number | null {
  if (plan.price.monthly === null || plan.price.annual === null) return null;
  return Math.round((1 - plan.price.annual / (plan.price.monthly * 12)) * 100);
}

export const COMPANY_PLANS: CompanyPlan[] = [
  {
    id: "core",
    name: "Phantom Core",
    tagline: "Everything you need to run your hiring process.",
    price: { monthly: 499, annual: 5000 },
    features: [
      "Full Phantom ATS",
      "Hiring projects & candidate pipeline",
      "Candidate profiles",
      "Candidate Passport integration",
      "Interview management",
      "Candidate messaging",
      "Team collaboration",
      "Basic candidate matching",
    ],
    cta: { label: "Start with Phantom", href: "/signup" },
  },
  {
    id: "network",
    name: "Phantom Network",
    tagline: "Find and hire from Phantom's private talent network.",
    price: { monthly: 999, annual: 10000 },
    mostPopular: true,
    features: [
      "Everything in Core",
      "Shadow Job Board",
      "Verified talent network",
      "Anonymous candidate discovery",
      "Advanced candidate matching",
      "Phantom Passport intelligence",
      "Identity reveal workflow",
      "Talent recommendations",
    ],
    cta: { label: "Start Hiring", href: "/signup" },
  },
  {
    id: "intelligence",
    name: "Phantom Intelligence",
    tagline: "Turn your hiring data into hiring intelligence.",
    price: { monthly: 1999, annual: 20000 },
    features: [
      "Everything in Network",
      "Advanced AI matching",
      "AI candidate ranking",
      "Match explanations",
      "Role & candidate intelligence",
      "Advanced hiring analytics",
      "Hiring recommendations",
      "Priority support",
    ],
    cta: {
      label: "Talk to Phantom",
      href: "mailto:sales@phantomhire.com?subject=Phantom%20Intelligence",
    },
  },
  {
    id: "enterprise",
    name: "Phantom Enterprise",
    tagline: "Phantom infrastructure for complex organisations.",
    price: { monthly: null, annual: null },
    features: [
      "Everything in Intelligence",
      "Multiple teams & business units",
      "Advanced permissions",
      "SSO",
      "Enterprise security",
      "API access",
      "Custom workflows",
      "Dedicated support",
    ],
    cta: {
      label: "Contact Phantom",
      href: "mailto:sales@phantomhire.com?subject=Phantom%20Enterprise",
    },
  },
];

export type FeatureCategory = "Hiring" | "Candidate" | "Shadow" | "Intelligence" | "Enterprise";

export interface FeatureRow {
  category: FeatureCategory;
  label: string;
  values: Record<CompanyPlanId, boolean | string>;
}

// "Talent rediscovery"/"Talent insights" rows are deliberately never a plain checkmark, even on
// plans where the brief's own copy lists them as included -- Talent Memory and the wider "Phantom
// Intelligence" market/scarcity/salary-benchmark analytics both have zero real backend today
// (confirmed exhaustively this session). Shown as "Preview" in every column that includes them,
// never sold as a live, paid-for feature. See PricingTrustSection/TalentMemorySection for the
// same rule applied elsewhere.
export const FEATURE_COMPARISON_ROWS: FeatureRow[] = [
  // Hiring
  { category: "Hiring", label: "ATS", values: { core: true, network: true, intelligence: true, enterprise: true } },
  { category: "Hiring", label: "Jobs", values: { core: true, network: true, intelligence: true, enterprise: true } },
  { category: "Hiring", label: "Hiring projects", values: { core: true, network: true, intelligence: true, enterprise: true } },
  { category: "Hiring", label: "Candidate pipeline", values: { core: true, network: true, intelligence: true, enterprise: true } },
  { category: "Hiring", label: "Interviews", values: { core: true, network: true, intelligence: true, enterprise: true } },
  { category: "Hiring", label: "Messaging", values: { core: true, network: true, intelligence: true, enterprise: true } },
  { category: "Hiring", label: "Team collaboration", values: { core: true, network: true, intelligence: true, enterprise: true } },
  // Candidate
  { category: "Candidate", label: "Candidate Passport", values: { core: true, network: true, intelligence: true, enterprise: true } },
  { category: "Candidate", label: "Candidate search", values: { core: true, network: true, intelligence: true, enterprise: true } },
  { category: "Candidate", label: "Candidate matching", values: { core: "Basic", network: "Advanced", intelligence: "Advanced", enterprise: "Advanced" } },
  { category: "Candidate", label: "Talent pools", values: { core: false, network: true, intelligence: true, enterprise: true } },
  { category: "Candidate", label: "Talent rediscovery (Preview)", values: { core: false, network: "Preview", intelligence: "Preview", enterprise: "Preview" } },
  // Shadow
  { category: "Shadow", label: "Shadow Job Board", values: { core: false, network: true, intelligence: true, enterprise: true } },
  { category: "Shadow", label: "Anonymous discovery", values: { core: false, network: true, intelligence: true, enterprise: true } },
  { category: "Shadow", label: "Verified talent network", values: { core: false, network: true, intelligence: true, enterprise: true } },
  { category: "Shadow", label: "Candidate recommendations", values: { core: false, network: true, intelligence: true, enterprise: true } },
  { category: "Shadow", label: "Identity reveal", values: { core: false, network: true, intelligence: true, enterprise: true } },
  // Intelligence
  { category: "Intelligence", label: "AI matching", values: { core: false, network: "Basic", intelligence: true, enterprise: true } },
  { category: "Intelligence", label: "Candidate intelligence", values: { core: false, network: false, intelligence: true, enterprise: true } },
  { category: "Intelligence", label: "Role intelligence", values: { core: false, network: false, intelligence: true, enterprise: true } },
  { category: "Intelligence", label: "Match explanations", values: { core: false, network: false, intelligence: true, enterprise: true } },
  { category: "Intelligence", label: "Hiring analytics", values: { core: "Basic", network: "Basic", intelligence: "Advanced", enterprise: "Advanced" } },
  { category: "Intelligence", label: "Talent insights (Preview)", values: { core: false, network: false, intelligence: "Preview", enterprise: "Preview" } },
  { category: "Intelligence", label: "Advanced reporting", values: { core: false, network: false, intelligence: true, enterprise: true } },
  // Enterprise
  { category: "Enterprise", label: "SSO", values: { core: false, network: false, intelligence: false, enterprise: true } },
  { category: "Enterprise", label: "API access", values: { core: false, network: false, intelligence: false, enterprise: true } },
  { category: "Enterprise", label: "Integrations", values: { core: false, network: false, intelligence: false, enterprise: true } },
  { category: "Enterprise", label: "Advanced permissions", values: { core: false, network: false, intelligence: false, enterprise: true } },
  { category: "Enterprise", label: "Custom workflows", values: { core: false, network: false, intelligence: false, enterprise: true } },
  { category: "Enterprise", label: "Dedicated support", values: { core: false, network: false, intelligence: "Priority", enterprise: "Dedicated" } },
];
