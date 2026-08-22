"use client";

import Link from "next/link";
import { ArrowRight, FileText, Search, Sparkles, UsersRound } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";

interface AiFeature {
  title: string;
  description: string;
  href: string;
  icon: typeof Sparkles;
  permission?: string;
}

const GROUPS: { heading: string; items: AiFeature[] }[] = [
  {
    heading: "Matches",
    items: [
      {
        title: "Phantom Smart Talent",
        description: "AI-ranked candidates from the discoverable Shadow pool, matched to a role.",
        href: "/search-candidates",
        icon: Search,
        permission: "shadow_candidates.search",
      },
      {
        title: "Talent Pool matches",
        description: "Find matches for a role among candidates who've granted future-role access.",
        href: "/talent-pool",
        icon: UsersRound,
        permission: "talent_pool.view",
      },
    ],
  },
  {
    heading: "Insights",
    items: [
      {
        title: "Hiring Blueprint & Interview Kit",
        description:
          "Generated per job from the role brief — required qualifications, evaluation criteria, and a grounded interview kit. Open a job's Blueprint tab.",
        href: "/projects",
        icon: FileText,
      },
    ],
  },
];

export default function PhantomAiHubPage() {
  const { hasPermission } = useAuth();
  const visibleGroups = GROUPS.map((group) => ({
    ...group,
    items: group.items.filter((item) => !item.permission || hasPermission(item.permission)),
  })).filter((group) => group.items.length > 0);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-semibold tracking-tight text-foreground">
          <Sparkles className="h-5 w-5 text-brand" />
          Discover Talent
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          A directory of the real AI-generation features already built into Phantom — every card
          here links to something that actually runs, nothing invented.
        </p>
      </div>

      {visibleGroups.map((group) => (
        <div key={group.heading}>
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            {group.heading}
          </h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {group.items.map((item) => (
              <Link key={item.href + item.title} href={item.href}>
                <Card className="h-full transition-colors hover:border-brand">
                  <CardHeader className="flex-row items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <item.icon className="h-4 w-4 text-brand" />
                      {item.title}
                    </CardTitle>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{item.description}</p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
