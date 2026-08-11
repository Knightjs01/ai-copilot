"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { PhantomWordmark } from "@/components/phantom-wordmark";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const AUDIENCE_LINKS = [
  { href: "/job-seekers", label: "Job Seekers" },
  { href: "/hiring-teams", label: "Hiring Teams" },
];

const INFO_LINKS = [
  { href: "/#phantom", label: "Meet Phantom" },
  { href: "/#security", label: "Security" },
];

export function MarketingNav() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-white/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link href="/" aria-label="Phantom Hire home">
          <PhantomWordmark />
        </Link>

        <nav className="hidden items-center gap-6 md:flex">
          {AUDIENCE_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "text-sm font-medium transition-colors hover:text-foreground",
                pathname === link.href ? "text-foreground" : "text-muted-foreground"
              )}
            >
              {link.label}
            </Link>
          ))}
          {INFO_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="flex items-center gap-2">
          <Button asChild variant="ghost" size="sm">
            <Link href="/login">Log in</Link>
          </Button>
          <Button asChild variant="brand" size="sm">
            <Link href="/signup">Start hiring with Phantom</Link>
          </Button>
        </div>
      </div>
    </header>
  );
}
