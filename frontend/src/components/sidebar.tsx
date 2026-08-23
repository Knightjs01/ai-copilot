"use client";

import * as React from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import {
  Archive,
  BarChart3,
  Briefcase,
  ChevronsLeft,
  ChevronsRight,
  Home,
  Sparkles,
  UserCog,
  Users,
  Video,
} from "lucide-react";

import { CreateMenu } from "@/components/create-menu";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: typeof Home;
  permission?: string;
}

export function Sidebar({ container }: { container?: HTMLElement | null }) {
  const { user, hasPermission } = useAuth();
  const pathname = usePathname();
  const [collapsed, setCollapsed] = React.useState(false);

  if (!user) return null;

  const items: NavItem[] = [
    { label: "Home", href: "/home", icon: Home },
    { label: "Jobs", href: "/projects", icon: Briefcase },
    { label: "Candidates", href: "/pipeline", icon: Users, permission: "candidates.view" },
    { label: "Discover Talent", href: "/phantom-ai", icon: Sparkles },
    { label: "Interviews", href: "/interviews", icon: Video, permission: "interviews.view" },
    { label: "Hiring Team", href: "/hiring-team", icon: UserCog, permission: "projects.view" },
  ];

  // A separate, lower group -- reporting/governance destinations, not day-to-day hiring work.
  // Project Vault is the same real audit/purge-log page previously reachable only from Settings
  // (route and historic_vault.view permission code unchanged -- label-only rename, matching this
  // app's established "rename the word, not the route" convention).
  const dataItems: NavItem[] = [
    { label: "Analytics", href: "/analytics", icon: BarChart3 },
    { label: "Project Vault", href: "/historic-vault", icon: Archive, permission: "historic_vault.view" },
  ];

  const visibleItems = items.filter((item) => !item.permission || hasPermission(item.permission));
  const visibleDataItems = dataItems.filter(
    (item) => !item.permission || hasPermission(item.permission)
  );

  const isActive = (href: string) => pathname === href || pathname?.startsWith(`${href}/`);

  const renderNavItem = (item: NavItem) => {
    const active = isActive(item.href);
    const link = (
      <Link
        key={item.href}
        href={item.href}
        className={cn(
          "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
          collapsed && "justify-center px-0",
          active
            ? "bg-brand/10 text-brand"
            : "text-muted-foreground hover:bg-secondary hover:text-foreground"
        )}
      >
        <item.icon className="h-4 w-4 shrink-0" />
        {!collapsed && item.label}
      </Link>
    );
    if (!collapsed) return link;
    return (
      <Tooltip key={item.href}>
        <TooltipTrigger asChild>{link}</TooltipTrigger>
        <TooltipContent container={container} side="right">
          {item.label}
        </TooltipContent>
      </Tooltip>
    );
  };

  return (
    <TooltipProvider delayDuration={200}>
      <aside
        className={cn(
          "sticky top-0 flex h-screen shrink-0 flex-col border-r border-border bg-card transition-[width] duration-150",
          collapsed ? "w-[68px]" : "w-60"
        )}
      >
        <div
          className={cn(
            "flex h-16 items-center border-b border-border px-4",
            collapsed && "justify-center px-0"
          )}
        >
          <Link href="/home" aria-label="Phantom ATS home" className="flex items-center">
            {collapsed ? (
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand text-sm font-bold text-brand-foreground">
                P
              </span>
            ) : (
              <Image
                src="/phantom-ats-logo.png"
                alt="Phantom ATS"
                width={2027}
                height={487}
                className="h-8 w-auto"
                priority
              />
            )}
          </Link>
        </div>

        <nav className="flex flex-1 flex-col gap-1 overflow-y-auto p-3">
          {visibleItems.map((item) => renderNavItem(item))}

          {visibleDataItems.length > 0 && (
            <>
              {!collapsed && (
                <p className="mt-4 px-3 pb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Data
                </p>
              )}
              {collapsed && <div className="my-2 border-t border-border" />}
              {visibleDataItems.map((item) => renderNavItem(item))}
            </>
          )}
        </nav>

        <div className="flex flex-col gap-2 border-t border-border p-3">
          <CreateMenu collapsed={collapsed} container={container} />

          <button
            type="button"
            onClick={() => setCollapsed((c) => !c)}
            className={cn(
              "flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground",
              collapsed && "justify-center px-0"
            )}
            aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? <ChevronsRight className="h-3.5 w-3.5" /> : <ChevronsLeft className="h-3.5 w-3.5" />}
            {!collapsed && "Collapse"}
          </button>
        </div>
      </aside>
    </TooltipProvider>
  );
}
