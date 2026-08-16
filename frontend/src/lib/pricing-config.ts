// Single source of truth for everything the /pricing page renders. Company plans and candidate
// verification tiers are deliberately separate shapes — verification is a trust signal, never a
// paid upsell or a ranking boost (see VERIFICATION_DISCLAIMER).

export type BillingPeriod = "monthly" | "annual";

export type CompanyPlanId = "free" | "pro" | "scale" | "enterprise";

export interface AiAllowance {
  label: string;
  monthlyCredits: number | "unlimited";
}

export interface CompanyPlan {
  id: CompanyPlanId;
  name: string;
  tagline: string;
  idealFor: string;
  /** null = "Custom" pricing (Enterprise). annualMonthlyEquivalent is the discounted rate shown
   *  by default ("Save 20%"); monthly is the higher pay-as-you-go rate shown when the Monthly
   *  toggle is selected. */
  price: { monthly: number | null; annualMonthlyEquivalent: number | null };
  mostPopular?: boolean;
  seats: string;
  roles: string;
  aiAllowance: AiAllowance;
  talentMemory: "not_included" | "included" | "included_extended";
  analyticsLevel: "basic" | "advanced" | "phantom_intelligence";
  features: string[];
  cta: { label: string; href: string };
}

export const COMPANY_PLANS: CompanyPlan[] = [
  {
    id: "free",
    name: "Individual",
    tagline: "For teams exploring Phantom",
    idealFor: "Teams running their first anonymous hire",
    price: { monthly: 0, annualMonthlyEquivalent: 0 },
    seats: "2 recruiter seats",
    roles: "1 active role",
    aiAllowance: { label: "Limited AI usage", monthlyCredits: 25 },
    talentMemory: "not_included",
    analyticsLevel: "basic",
    features: [
      "1 active role",
      "2 recruiter seats",
      "Shadow job posting",
      "Anonymous candidates",
      "Candidate Passport matching",
      "Basic ATS",
      "Limited AI screening",
      "Basic pipeline",
      "Basic analytics",
    ],
    cta: { label: "Start Free", href: "/signup" },
  },
  {
    id: "pro",
    name: "Scale Up",
    tagline: "Full hiring infrastructure for modern TA teams",
    idealFor: "Growing TA teams running multiple live roles",
    price: { monthly: 624, annualMonthlyEquivalent: 499 },
    mostPopular: true,
    seats: "5 recruiter seats",
    roles: "Up to 10 active roles",
    aiAllowance: { label: "500 AI candidate analyses / month", monthlyCredits: 500 },
    talentMemory: "included",
    analyticsLevel: "advanced",
    features: [
      "Up to 10 active roles",
      "5 recruiter seats",
      "Unlimited candidate applications",
      "Full Phantom ATS",
      "Shadow marketplace",
      "AI screening & evidence-based fit assessment",
      "Interview transcription & summaries",
      "Talent Memory & candidate rediscovery (Preview)",
      "Reveal Requests",
      "Project Vault & Zero-Retention Purge",
      "Standard ATS integrations",
    ],
    cta: { label: "Start Scale Up", href: "/signup" },
  },
  {
    id: "scale",
    name: "High Growth",
    tagline: "For scaling TA teams and talent organisations",
    idealFor: "Organisations hiring at volume across multiple teams",
    price: { monthly: 1874, annualMonthlyEquivalent: 1499 },
    seats: "25 recruiter seats",
    roles: "Unlimited active roles",
    aiAllowance: { label: "Expanded AI capacity", monthlyCredits: 2000 },
    talentMemory: "included_extended",
    analyticsLevel: "phantom_intelligence",
    features: [
      "Unlimited active roles",
      "25 recruiter seats",
      "Advanced AI screening & evidence-based fit intelligence",
      "AI Talent Rediscovery (Preview)",
      "Advanced analytics & hiring intelligence",
      "Advanced retention controls",
      "Custom workflows",
      "API access",
      "Advanced integrations & security",
      "Priority support",
    ],
    cta: {
      label: "Talk to Phantom",
      href: "mailto:sales@phantomhire.com?subject=Phantom%20High%20Growth",
    },
  },
  {
    id: "enterprise",
    name: "Enterprise",
    tagline: "For organisations where security, scale and control come first",
    idealFor: "Enterprises needing SSO, SCIM, custom retention and dedicated support",
    price: { monthly: null, annualMonthlyEquivalent: null },
    seats: "Custom",
    roles: "Unlimited / negotiated usage",
    aiAllowance: { label: "Custom AI capacity", monthlyCredits: "unlimited" },
    talentMemory: "included_extended",
    analyticsLevel: "phantom_intelligence",
    features: [
      "Enterprise-scale hiring",
      "SSO & SCIM",
      "Advanced RBAC & audit controls",
      "Custom data retention policies",
      "Data residency options where supported",
      "Dedicated implementation & enterprise support",
      "SLA options",
      "Security review & procurement support",
    ],
    cta: {
      label: "Talk to Enterprise",
      href: "mailto:sales@phantomhire.com?subject=Phantom%20Enterprise",
    },
  },
];

export interface AiCreditPack {
  id: "small" | "medium" | "large";
  credits: number;
  price: number;
}

export const AI_CREDIT_PACKS: AiCreditPack[] = [
  { id: "small", credits: 250, price: 49 },
  { id: "medium", credits: 600, price: 99 },
  { id: "large", credits: 1500, price: 199 },
];

export const MARKETPLACE_FEE = {
  percentOfFirstYearSalary: 7.5,
  upfrontCost: 0,
  description: "Pay nothing upfront. 7.5% of first-year base salary, invoiced only once you hire.",
};

export type VerificationTierId = "bronze" | "silver" | "gold" | "platinum";

export interface VerificationTier {
  id: VerificationTierId;
  name: string;
  badge: string;
  description: string;
  checksIncluded: string[];
  badgeColorClass: string;
}

export const VERIFICATION_TIERS: VerificationTier[] = [
  {
    id: "bronze",
    name: "Profile",
    badge: "BRONZE — PROFILE CREATED",
    description: "Self-declared professional information.",
    checksIncluded: [
      "Career history",
      "Skills",
      "Experience",
      "Achievements",
      "Preferences",
      "Job matching",
      "Anonymous applications",
    ],
    badgeColorClass: "border-orange-200 bg-orange-50 text-orange-700",
  },
  {
    id: "silver",
    name: "Verified",
    badge: "SILVER — PROFESSIONALLY VERIFIED",
    description: "Professionally verified.",
    checksIncluded: [
      "Identity verification",
      "Employment history",
      "Qualifications",
      "Professional profile verification",
      "Email verification",
    ],
    badgeColorClass: "border-slate-300 bg-slate-100 text-slate-700",
  },
  {
    id: "gold",
    name: "Enhanced Verified",
    badge: "GOLD — ENHANCED VERIFIED",
    description: "Enhanced verification.",
    checksIncluded: [
      "Identity",
      "Employment history",
      "Qualifications",
      "Right to work",
      "Enhanced background checks where appropriate",
      "KYC",
      "Professional references",
    ],
    badgeColorClass: "border-yellow-300 bg-yellow-50 text-yellow-700",
  },
  {
    id: "platinum",
    name: "Security Verified",
    badge: "PLATINUM — SECURITY VERIFIED",
    description: "High-assurance professional verification.",
    checksIncluded: [
      "Enhanced identity",
      "Enhanced employment verification",
      "Security clearance status where legitimately verifiable",
      "Regulated-industry verification",
      "Advanced professional credentials",
      "High-assurance checks",
    ],
    badgeColorClass: "border-brand/30 bg-brand/10 text-brand",
  },
];

export const VERIFICATION_DISCLAIMER =
  "Verification confirms the checks listed above were completed — it is not a ranking boost, a compliance certification, or a security clearance guarantee. Specific verification availability depends on the implementation, jurisdiction and verification provider.";

export type FeatureCategory =
  | "Platform"
  | "Candidate Management"
  | "AI"
  | "Security"
  | "Analytics"
  | "Integrations";

export interface FeatureRow {
  category: FeatureCategory;
  label: string;
  values: Record<CompanyPlanId, boolean | string>;
  /** Only the Talent Memory row is wired to the single illustrative upgrade modal. */
  proOnly?: boolean;
}

export const FEATURE_COMPARISON_ROWS: FeatureRow[] = [
  {
    category: "Platform",
    label: "Shadow anonymous job board",
    values: { free: true, pro: true, scale: true, enterprise: true },
  },
  {
    category: "Platform",
    label: "Phantom Passport matching",
    values: { free: true, pro: true, scale: true, enterprise: true },
  },
  {
    category: "Platform",
    label: "Phantom ATS",
    values: { free: "Basic", pro: true, scale: true, enterprise: true },
  },
  {
    category: "Platform",
    label: "Phantom AI co-pilot",
    values: { free: false, pro: true, scale: true, enterprise: true },
  },
  {
    category: "Candidate Management",
    label: "Anonymous applications",
    values: { free: true, pro: true, scale: true, enterprise: true },
  },
  {
    category: "Candidate Management",
    label: "Candidate Callsigns",
    values: { free: true, pro: true, scale: true, enterprise: true },
  },
  {
    category: "Candidate Management",
    label: "Reveal Requests",
    values: { free: true, pro: true, scale: true, enterprise: true },
  },
  {
    category: "Candidate Management",
    label: "AI candidate matching",
    values: { free: "Basic", pro: true, scale: true, enterprise: true },
  },
  {
    category: "Candidate Management",
    label: "Talent Memory (Preview)",
    values: { free: false, pro: true, scale: true, enterprise: true },
    proOnly: true,
  },
  {
    category: "AI",
    label: "AI screening",
    values: { free: "Limited", pro: true, scale: true, enterprise: true },
  },
  {
    category: "AI",
    label: "Evidence-based fit assessment",
    values: { free: false, pro: true, scale: true, enterprise: true },
  },
  {
    category: "AI",
    label: "Interview transcription & summaries",
    values: { free: false, pro: true, scale: true, enterprise: true },
  },
  {
    category: "AI",
    label: "AI Talent Rediscovery (Preview)",
    values: { free: false, pro: false, scale: true, enterprise: true },
  },
  {
    category: "Security",
    label: "Project Vault",
    values: { free: true, pro: true, scale: true, enterprise: true },
  },
  {
    category: "Security",
    label: "Zero-Retention Project Purge",
    values: { free: true, pro: true, scale: true, enterprise: true },
  },
  {
    category: "Security",
    label: "Advanced retention controls",
    values: { free: false, pro: false, scale: true, enterprise: true },
  },
  {
    category: "Security",
    label: "Roles & permissions (RBAC)",
    values: { free: "Basic", pro: true, scale: true, enterprise: "Advanced" },
  },
  {
    category: "Security",
    label: "SSO",
    values: { free: false, pro: false, scale: false, enterprise: true },
  },
  {
    category: "Security",
    label: "SCIM",
    values: { free: false, pro: false, scale: false, enterprise: true },
  },
  {
    category: "Security",
    label: "Audit controls",
    values: { free: "Basic", pro: "Standard", scale: "Advanced", enterprise: "Custom" },
  },
  {
    category: "Analytics",
    label: "Basic analytics",
    values: { free: true, pro: true, scale: true, enterprise: true },
  },
  {
    category: "Analytics",
    label: "Advanced analytics",
    values: { free: false, pro: true, scale: true, enterprise: true },
  },
  {
    category: "Analytics",
    label: "Phantom Intelligence",
    values: { free: false, pro: false, scale: true, enterprise: true },
  },
  {
    category: "Integrations",
    label: "ATS & calendar integrations",
    values: { free: false, pro: true, scale: true, enterprise: true },
  },
  {
    category: "Integrations",
    label: "API access",
    values: { free: false, pro: false, scale: true, enterprise: true },
  },
];
