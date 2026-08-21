"use client";

import { ShieldAlert } from "lucide-react";

import { CommandCentre } from "@/components/dashboard/command-centre";
import { useAuth } from "@/lib/auth-context";

export default function HomePage() {
  const { hasPermission } = useAuth();
  const canView = hasPermission("projects.view");

  if (!canView) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <ShieldAlert className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">Home is Admin-only</p>
        <p className="max-w-xs text-sm text-muted-foreground">
          Ask an Owner or Admin on your team for access.
        </p>
      </div>
    );
  }

  return <CommandCentre />;
}
