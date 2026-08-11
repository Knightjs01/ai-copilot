import Image from "next/image";
import Link from "next/link";

export function MarketingFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-border">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-4 px-6 py-10 sm:flex-row sm:justify-between">
        <div className="flex items-center gap-3">
          <Image
            src="/phantom-wordmark.png"
            alt="Phantom Hire"
            width={829}
            height={193}
            className="h-6 w-auto"
          />
          <span className="text-xs text-muted-foreground">
            The world&apos;s first Zero-Retention Hiring Platform.
          </span>
        </div>

        <div className="flex items-center gap-6 text-sm text-muted-foreground">
          <Link href="/login" className="transition-colors hover:text-foreground">
            Log in
          </Link>
          <Link href="/signup" className="transition-colors hover:text-foreground">
            Get started
          </Link>
          <span>© {year} Phantom Hire</span>
        </div>
      </div>
    </footer>
  );
}
