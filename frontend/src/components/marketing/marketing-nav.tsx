"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu } from "lucide-react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

import { MobileNav, type MobileNavGroup } from "@/components/marketing/mobile-nav";

interface NavGroup {
  label: string;
  links: { href: string; label: string }[];
}

// Every link below points at a real, shipped page — no placeholders.
const NAV_GROUPS: NavGroup[] = [
  {
    label: "Candidates",
    links: [
      { href: "/shadow-job-board", label: "Shadow Job Board" },
      { href: "/passport", label: "Candidate Passport" },
      { href: "/job-seekers", label: "For Job Seekers" },
    ],
  },
  {
    label: "Hire",
    links: [
      { href: "/ats", label: "Phantom ATS" },
      { href: "/ai", label: "Phantom AI" },
      { href: "/hiring-teams", label: "For Hiring Teams" },
    ],
  },
  {
    label: "Intelligence",
    links: [
      { href: "/talent-memory", label: "Talent Memory" },
      { href: "/intelligence", label: "Phantom Intelligence" },
    ],
  },
  {
    label: "Trust",
    links: [
      { href: "/trust", label: "Security" },
      { href: "/pricing", label: "Pricing" },
      { href: "/about", label: "About" },
    ],
  },
];

function DesktopNavGroup({ group, isActive }: { group: NavGroup; isActive: boolean }) {
  const [open, setOpen] = React.useState(false);

  return (
    <div
      className="relative"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        className={cn(
          "text-sm font-medium transition-colors hover:text-foreground",
          isActive ? "text-foreground" : "text-muted-foreground"
        )}
        aria-expanded={open}
        onFocus={() => setOpen(true)}
      >
        {group.label}
      </button>
      {open && (
        <div className="absolute left-1/2 top-full z-50 -translate-x-1/2 pt-3">
          <div className="flex w-52 flex-col gap-1 rounded-xl border border-border bg-popover p-2 shadow-xl shadow-slate-900/10">
            {group.links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="rounded-lg px-3 py-2 text-sm font-medium text-foreground transition-colors hover:bg-secondary"
                onClick={() => setOpen(false)}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export function MarketingNav() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const mobileGroups: MobileNavGroup[] = NAV_GROUPS;

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link href="/" aria-label="Phantom Hire home">
          <Image
            src="/phantom-hire-logo-compact.png"
            alt="Phantom Hire"
            width={2006}
            height={589}
            className="h-10 w-auto"
            priority
          />
        </Link>

        <nav className="hidden items-center gap-8 md:flex">
          {NAV_GROUPS.map((group) => (
            <DesktopNavGroup
              key={group.label}
              group={group}
              isActive={group.links.some((link) => link.href === pathname)}
            />
          ))}
        </nav>

        <div className="hidden items-center gap-4 md:flex">
          <Link
            href="/login"
            className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            Log in
          </Link>
          <Button asChild variant="secondary" size="sm">
            <Link href="/shadow/signup">Create Passport</Link>
          </Button>
          <Button asChild variant="brand" size="sm">
            <Link href="/signup">Start hiring</Link>
          </Button>
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          aria-label="Open menu"
          onClick={() => setMobileOpen(true)}
        >
          <Menu className="h-5 w-5" />
        </Button>
      </div>

      <MobileNav open={mobileOpen} onOpenChange={setMobileOpen} groups={mobileGroups} />
    </header>
  );
}
