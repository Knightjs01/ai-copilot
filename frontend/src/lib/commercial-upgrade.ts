import type { CommercialPlanCode } from "@/lib/types";

const SALES_EMAIL = "sales@phantomhire.com";

interface NextPlan {
  code: CommercialPlanCode;
  name: string;
  highlight: string;
}

// The natural upgrade path, Core -> Growth -> Scale. Scale has no "next" -- it's already the top
// tier; hitting its limit means asking to raise the configured override, not upgrading plans.
export const NEXT_PLAN: Record<CommercialPlanCode, NextPlan | null> = {
  core: {
    code: "growth",
    name: "Phantom Growth",
    highlight: "enhanced employer branding and hiring analytics",
  },
  growth: {
    code: "scale",
    name: "Phantom Scale",
    highlight: "configurable capacity and advanced AI",
  },
  scale: null,
};

// No self-serve billing or in-app plan change exists for a company -- only a platform admin can
// change a company's plan. mailto is the honest, real action available today; it must never look
// like a self-serve "Upgrade" button that silently changes anything.
export function upgradeMailto(subject: string): string {
  return `mailto:${SALES_EMAIL}?subject=${encodeURIComponent(subject)}`;
}
