import Image from "next/image";
import Link from "next/link";

import { Button } from "@/components/ui/button";

const NAV_LINKS = [
  { href: "#phantom", label: "Meet Phantom" },
  { href: "#zero-retention", label: "Zero-Retention" },
  { href: "#how-it-works", label: "How it works" },
  { href: "#security", label: "Security" },
];

export function MarketingNav() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-white/80 backdrop-blur">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link href="/" aria-label="Phantom Hire home">
          <Image
            src="/phantom-wordmark.png"
            alt="Phantom Hire"
            width={830}
            height={219}
            className="h-8 w-auto"
            priority
          />
        </Link>

        <nav className="hidden items-center gap-6 md:flex">
          {NAV_LINKS.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm text-muted-foreground transition-colors hover:text-foreground"
            >
              {link.label}
            </a>
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
