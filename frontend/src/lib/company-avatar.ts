// Deterministic colored-initial avatar for a company name -- purely presentational styling of
// real data (the company's own name), never a fabricated field. Shared by ShadowJobCard's
// showCompanyAvatar prop and the Home page's "Saved opportunities" list so both pick the same
// color for the same company.
const PALETTE = [
  "bg-brand text-brand-foreground",
  "bg-electric text-white",
  "bg-slate-800 text-white",
  "bg-emerald-600 text-white",
  "bg-amber-600 text-white",
  "bg-rose-600 text-white",
] as const;

export function companyAvatar(name: string): { initial: string; colorClassName: string } {
  const trimmed = name.trim();
  const initial = trimmed ? trimmed[0]!.toUpperCase() : "?";
  let hash = 0;
  for (let i = 0; i < trimmed.length; i++) {
    hash = (hash * 31 + trimmed.charCodeAt(i)) >>> 0;
  }
  return { initial, colorClassName: PALETTE[hash % PALETTE.length]! };
}
