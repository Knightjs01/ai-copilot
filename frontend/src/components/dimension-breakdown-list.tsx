import { Badge } from "@/components/ui/badge";
import { DIMENSION_RATING_VARIANT } from "@/lib/status-display";
import type { DimensionRating } from "@/lib/types";

// Shared between the recruiter-facing applicant match tab (components/shadow-jobs/candidate-workspace)
// and the candidate-facing Shadow match views (components/shadow) -- both consume the same
// DimensionRating[] shape from passport_matching, just from opposite sides of the same match.
// Tri-state (Strong/Moderate/Weak), never a percentage -- there is no numeric per-dimension score
// anywhere in the schema, so a progress bar would misrepresent this data.
export function DimensionBreakdownList({ dimensions }: { dimensions: DimensionRating[] }) {
  if (dimensions.length === 0) return null;
  return (
    <div className="flex flex-col divide-y divide-border">
      {dimensions.map((dim) => (
        <div key={dim.dimension} className="flex flex-col gap-1 py-3 first:pt-0 last:pb-0">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm font-medium text-foreground">{dim.dimension}</p>
            <Badge variant={DIMENSION_RATING_VARIANT[dim.rating]}>{dim.rating}</Badge>
          </div>
          <p className="text-sm text-muted-foreground">{dim.evidence}</p>
        </div>
      ))}
    </div>
  );
}
