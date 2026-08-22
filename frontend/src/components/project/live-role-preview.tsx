"use client";

import { ExternalLink, Eye } from "lucide-react";

import { Button } from "@/components/ui/button";

// The most honest "preview" is the real public page itself, opened directly in its own tab --
// not a second, hand-built rendering, and not a cramped iframe fighting Shadow's own dark theme
// and page-level scroll inside a small light-themed ATS dialog. This guarantees byte-for-byte
// parity with what a candidate actually sees (their real viewport, their real layout), with none
// of the embedding compromises.
export function LiveRoleLink({
  jobId,
  label = "View live role",
  variant = "secondary",
  size = "sm",
}: {
  jobId: string;
  label?: string;
  variant?: "secondary" | "brand" | "primary" | "ghost";
  size?: "sm" | "md" | "lg";
}) {
  return (
    <Button type="button" variant={variant} size={size} asChild>
      <a href={`/shadow/jobs/${jobId}`} target="_blank" rel="noopener noreferrer">
        <Eye className="h-3.5 w-3.5" />
        {label}
        <ExternalLink className="h-3 w-3" />
      </a>
    </Button>
  );
}
