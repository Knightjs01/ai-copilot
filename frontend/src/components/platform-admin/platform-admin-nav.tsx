"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import { ChangePasswordDialog } from "@/components/platform-admin/change-password-dialog";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import { cn } from "@/lib/utils";
import type { PlatformAdmin } from "@/lib/types";

const NAV_ITEMS: { href: string; label: string; permission?: string }[] = [
  { href: "/platform-admin", label: "Dashboard" },
  { href: "/platform-admin/requests", label: "Requests", permission: "companies.view" },
  { href: "/platform-admin/companies", label: "Companies", permission: "companies.view" },
  { href: "/platform-admin/jobs", label: "Jobs", permission: "jobs.view" },
  { href: "/platform-admin/activity", label: "Activity", permission: "audit.view" },
  { href: "/platform-admin/team", label: "Team", permission: "admins.manage" },
  { href: "/platform-admin/danger-zone", label: "Danger Zone", permission: "danger_zone.purge" },
];

export function PlatformAdminNav({ admin }: { admin: PlatformAdmin }) {
  const pathname = usePathname();
  const { logout, hasPermission } = usePlatformAdminAuth();
  const visibleItems = NAV_ITEMS.filter(
    (item) => !item.permission || hasPermission(item.permission)
  );

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Phantom Admin</h1>
          <p className="text-sm text-muted-foreground">Signed in as {admin.email}</p>
        </div>
        <div className="flex items-center gap-2">
          <ChangePasswordDialog />
          <Button type="button" variant="secondary" size="sm" onClick={logout}>
            Log out
          </Button>
        </div>
      </div>
      <nav className="flex gap-1 border-b border-border">
        {visibleItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "border-b-2 px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "border-primary text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
