"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bookmark,
  Briefcase,
  CalendarClock,
  Compass,
  Home,
  IdCard,
  MessageSquare,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

import { useCandidateAuth } from "@/lib/candidate-auth-context";
import { useMyMessageThreads } from "@/lib/queries/messages";
import { cn } from "@/lib/utils";

interface MobileNavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

const ITEMS: MobileNavItem[] = [
  { label: "Home", href: "/shadow/home", icon: Home },
  { label: "Discover", href: "/shadow", icon: Compass },
  { label: "For You", href: "/shadow/for-you", icon: Sparkles },
  { label: "Applications", href: "/shadow/applications", icon: Briefcase },
  { label: "Messages", href: "/shadow/messages", icon: MessageSquare },
  { label: "Interviews", href: "/shadow/interviews", icon: CalendarClock },
  { label: "Passport", href: "/shadow/passport", icon: IdCard },
  { label: "Saved", href: "/shadow/saved-jobs", icon: Bookmark },
];

// Replaces the top nav's horizontal links below md -- the top bar itself stays (logo + avatar),
// see shadow-top-nav.tsx. Only rendered for authed candidates (same gate the top nav's own link
// list already uses), so a logged-out visitor on the public board never sees candidate-only
// destinations.
export function ShadowMobileNav() {
  const pathname = usePathname();
  const { candidate } = useCandidateAuth();
  const { data: threads } = useMyMessageThreads({ enabled: !!candidate });
  const unreadCount = threads?.reduce((sum, t) => sum + t.unread_count, 0) ?? 0;

  if (!candidate) return null;

  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-40 flex items-stretch justify-around border-t border-border bg-white/95 backdrop-blur md:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      aria-label="Shadow navigation"
    >
      {ITEMS.map((item) => {
        const isActive =
          item.href === "/shadow" ? pathname === "/shadow" : pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            className={cn(
              "relative flex flex-1 flex-col items-center gap-1 py-2.5 text-[11px] font-medium transition-colors",
              isActive ? "text-brand" : "text-muted-foreground hover:text-foreground"
            )}
          >
            <span className="relative">
              <item.icon className="h-5 w-5" />
              {item.href === "/shadow/messages" && unreadCount > 0 && (
                <span className="absolute -right-1.5 -top-1.5 flex h-3.5 min-w-3.5 items-center justify-center rounded-full bg-info px-1 text-[9px] font-semibold text-info-foreground">
                  {unreadCount}
                </span>
              )}
            </span>
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
