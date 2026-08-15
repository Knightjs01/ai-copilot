"use client";

import { format, formatDistanceToNow } from "date-fns";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";

export function RelativeTime({ date, className }: { date: string; className?: string }) {
  const container = useThemeScopeContainer();
  const parsed = new Date(date);

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className={className}>{formatDistanceToNow(parsed, { addSuffix: true })}</span>
      </TooltipTrigger>
      <TooltipContent container={container}>{format(parsed, "d MMM yyyy, HH:mm")}</TooltipContent>
    </Tooltip>
  );
}
