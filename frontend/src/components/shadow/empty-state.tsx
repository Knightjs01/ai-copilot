"use client";

import Link from "next/link";
import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: { label: string; href: string };
  className?: string;
}

// The one standard "nothing exists here yet" treatment across Shadow's candidate pages --
// previously every page hand-rolled its own copy of either this dashed-border box or a plain
// Card with the same icon-and-sentence shape, with no rule for which got which.
export function EmptyState({ icon: Icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-16 text-center",
        className
      )}
    >
      <Icon className="h-8 w-8 text-muted-foreground" />
      <div className="flex flex-col gap-1">
        <p className="text-sm font-medium text-foreground">{title}</p>
        {description && <p className="max-w-xs text-sm text-muted-foreground">{description}</p>}
      </div>
      {action && (
        <Link href={action.href} className="text-sm font-medium text-brand hover:underline">
          {action.label}
        </Link>
      )}
    </div>
  );
}
