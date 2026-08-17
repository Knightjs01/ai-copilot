import { ProductIconBadge } from "@/components/marketing/icons/product-icon-badge";

export function ShadowMaskIcon() {
  return (
    <ProductIconBadge>
      <svg width="34" height="34" viewBox="0 0 34 34" fill="none" aria-hidden>
        <ellipse cx="10" cy="17" rx="8.5" ry="6.5" fill="white" transform="rotate(-8 10 17)" />
        <ellipse cx="24" cy="17" rx="8.5" ry="6.5" fill="white" transform="rotate(8 24 17)" />
        <rect x="14" y="14.5" width="6" height="3" rx="1.5" fill="white" />
        <ellipse
          cx="10"
          cy="17"
          rx="2.6"
          ry="2.2"
          fill="hsl(253 45% 30%)"
          transform="rotate(-8 10 17)"
        />
        <ellipse
          cx="24"
          cy="17"
          rx="2.6"
          ry="2.2"
          fill="hsl(253 45% 30%)"
          transform="rotate(8 24 17)"
        />
      </svg>
    </ProductIconBadge>
  );
}
