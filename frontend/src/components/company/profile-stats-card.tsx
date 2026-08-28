"use client";

import { Briefcase, TrendingUp, UserCheck, Users } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { useProfileStats } from "@/lib/queries/company";
import type { ProfileStats } from "@/lib/types";

const STATS: { key: keyof ProfileStats; label: string; icon: typeof Briefcase }[] = [
  { key: "active_role_count", label: "Active roles", icon: Briefcase },
  { key: "total_hires", label: "Total hires", icon: UserCheck },
  { key: "team_size", label: "Team size", icon: Users },
  { key: "candidates_in_pipeline", label: "Candidates in pipeline", icon: TrendingUp },
];

// Real numbers only, internal to the company's own team -- never part of the shared public/
// preview shape (see backend ProfileStats' docstring for why hires/pipeline stay internal).
export function ProfileStatsCard() {
  const { data, isLoading } = useProfileStats();

  if (isLoading || !data) return null;

  return (
    <Card>
      <CardContent className="grid grid-cols-2 gap-4 py-5 sm:grid-cols-4">
        {STATS.map(({ key, label, icon: Icon }) => (
          <div key={key} className="flex flex-col gap-1">
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <Icon className="h-3.5 w-3.5" />
              {label}
            </div>
            <span className="text-xl font-semibold text-foreground">{data[key] ?? "—"}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
