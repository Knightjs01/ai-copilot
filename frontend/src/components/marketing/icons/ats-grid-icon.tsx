import { ProductIconBadge } from "@/components/marketing/icons/product-icon-badge";

export function AtsGridIcon() {
  return (
    <ProductIconBadge>
      <svg width="30" height="30" viewBox="0 0 30 30" fill="none" aria-hidden>
        <rect x="4" y="4" width="9" height="9" rx="2" fill="white" />
        <rect x="17" y="4" width="9" height="9" rx="2" fill="white" fillOpacity="0.55" />
        <rect x="4" y="17" width="9" height="9" rx="2" fill="white" fillOpacity="0.55" />
        <rect x="17" y="17" width="9" height="9" rx="2" fill="white" />
      </svg>
    </ProductIconBadge>
  );
}
