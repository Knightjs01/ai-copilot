import Image from "next/image";
import Link from "next/link";

// Mirrors marketing-nav.tsx's audience-first grouping (Candidates / Companies / Company), so the
// footer sitemap and the header nav never disagree about how the site is organised. Every link
// points at a real, shipped page -- no Privacy/Terms links, since those pages don't exist yet and
// a footer link to a non-existent page (or invented legal text) would be worse than no link.
const FOOTER_GROUPS: { label: string; links: { href: string; label: string }[] }[] = [
  {
    label: "Candidates",
    links: [
      { href: "/shadow-job-board", label: "Shadow Job Board" },
      { href: "/passport", label: "Candidate Passport" },
      { href: "/job-seekers", label: "For Job Seekers" },
    ],
  },
  {
    label: "Companies",
    links: [
      { href: "/ats", label: "Phantom ATS" },
      { href: "/ai", label: "Phantom AI" },
      { href: "/talent-memory", label: "Talent Memory" },
      { href: "/intelligence", label: "Phantom Intelligence" },
      { href: "/hiring-teams", label: "For Hiring Teams" },
    ],
  },
  {
    label: "Company",
    links: [
      { href: "/pricing", label: "Pricing" },
      { href: "/trust", label: "Security" },
      { href: "/about", label: "About" },
    ],
  },
];

export function MarketingFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="grid grid-cols-2 gap-10 sm:grid-cols-4">
          <div className="col-span-2 flex flex-col gap-3 sm:col-span-1">
            <Image
              src="/phantom-hire-logo-new.png"
              alt="Phantom Hire"
              width={2172}
              height={724}
              className="h-7 w-auto"
            />
            <p className="text-xs leading-relaxed text-muted-foreground">
              The world&apos;s first Zero-Retention Hiring Platform.
            </p>
          </div>

          {FOOTER_GROUPS.map((group) => (
            <div key={group.label} className="flex flex-col gap-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                {group.label}
              </p>
              <div className="flex flex-col gap-2">
                {group.links.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="text-sm text-muted-foreground transition-colors hover:text-foreground"
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-10 flex flex-col items-center gap-4 border-t border-border pt-6 sm:flex-row sm:justify-between">
          <span className="text-xs text-muted-foreground">© {year} Phantom Hire</span>
          <div className="flex items-center gap-6 text-sm text-muted-foreground">
            <Link href="/login" className="transition-colors hover:text-foreground">
              Log in
            </Link>
            <Link href="/signup" className="transition-colors hover:text-foreground">
              Get started
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
