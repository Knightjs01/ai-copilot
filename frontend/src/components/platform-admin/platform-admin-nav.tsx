"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import { cn } from "@/lib/utils";
import type { PlatformAdmin } from "@/lib/types";

const NAV_ITEMS = [
  { href: "/platform-admin/requests", label: "Requests" },
  { href: "/platform-admin/companies", label: "Companies" },
  { href: "/platform-admin/activity", label: "Activity" },
];

export function PlatformAdminNav({ admin }: { admin: PlatformAdmin }) {
  const pathname = usePathname();
  const { logout } = usePlatformAdminAuth();

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Phantom Admin</h1>
          <p className="text-sm text-muted-foreground">Signed in as {admin.email}</p>
        </div>
        <Button type="button" variant="secondary" size="sm" onClick={logout}>
          Log out
        </Button>
      </div>
      <nav className="flex gap-1 border-b border-border">
        {NAV_ITEMS.map((item) => {
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
