import { DimensionBreakdownList } from "@/components/dimension-breakdown-list";
import { MatchToneList } from "@/components/shadow/match-tone-list";
import type { ShadowJobMatch } from "@/lib/types";

export function MatchDetailPanel({ match }: { match: ShadowJobMatch }) {
  return (
    <div className="flex flex-col gap-4">
      <MatchToneList title="Strengths" items={match.strengths} tone="positive" />
      <MatchToneList title="Gaps" items={match.gaps} tone="caution" />
      <DimensionBreakdownList dimensions={match.dimension_breakdown} />
    </div>
  );
}
