"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  Bookmark,
  Briefcase,
  CalendarClock,
  Compass,
  Home,
  IdCard,
  LogOut,
  MessageSquare,
  Sparkles,
  X,
  type LucideIcon,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { useCandidateAuth } from "@/lib/candidate-auth-context";
import { useMyMessageThreads } from "@/lib/queries/messages";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

// Same route/icon/order list as the mobile nav bar and command palette this replaces — no new IA
// decision here, just promoted from a bottom bar into a sidebar. Flat, unlike the ATS Sidebar's
// Work/Data split: a candidate has no reporting/governance surface analogous to Analytics/Project
// Vault, so a single group is the right call.
const NAV_ITEMS: NavItem[] = [
  { label: "Home", href: "/shadow/home", icon: Home },
  { label: "Discover", href: "/shadow", icon: Compass },
  { label: "For You", href: "/shadow/for-you", icon: Sparkles },
  { label: "Applications", href: "/shadow/applications", icon: Briefcase },
  { label: "Messages", href: "/shadow/messages", icon: MessageSquare },
  { label: "Interviews", href: "/shadow/interviews", icon: CalendarClock },
  { label: "Passport", href: "/shadow/passport", icon: IdCard },
  { label: "Saved Jobs", href: "/shadow/saved-jobs", icon: Bookmark },
];

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { candidate } = useCandidateAuth();
  const { data: threads } = useMyMessageThreads({ enabled: !!candidate });
  const unreadCount = threads?.reduce((sum, t) => sum + t.unread_count, 0) ?? 0;

  const isActive = (href: string) =>
    href === "/shadow" ? pathname === "/shadow" : pathname === href || pathname?.startsWith(`${href}/`);

  return (
    <nav className="flex flex-col gap-1">
      {NAV_ITEMS.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          onClick={onNavigate}
          className={cn(
            "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
            isActive(item.href)
              ? "bg-brand/10 text-brand"
              : "text-muted-foreground hover:bg-secondary hover:text-foreground"
          )}
        >
          <span className="relative shrink-0">
            <item.icon className="h-4 w-4" />
            {item.href === "/shadow/messages" && unreadCount > 0 && (
              <span className="absolute -right-1.5 -top-1.5 flex h-3.5 min-w-3.5 items-center justify-center rounded-full bg-info px-1 text-[9px] font-semibold text-info-foreground">
                {unreadCount}
              </span>
            )}
          </span>
          {item.label}
        </Link>
      ))}
    </nav>
  );
}

function SidebarLogo() {
  return (
    <Link href="/shadow" aria-label="Shadow home" className="flex items-center">
      <Image
        src="/phantom-shadow-logo-new.png"
        alt="Phantom Shadow"
        width={2172}
        height={724}
        className="h-8 w-auto"
        priority
      />
    </Link>
  );
}

export function ShadowSidebar({
  mobileOpen,
  onMobileOpenChange,
}: {
  mobileOpen: boolean;
  onMobileOpenChange: (open: boolean) => void;
}) {
  const { candidate, logout } = useCandidateAuth();
  const router = useRouter();
  const reduceMotion = useReducedMotion();
  const closeButtonRef = React.useRef<HTMLButtonElement>(null);

  React.useEffect(() => {
    if (!mobileOpen) return;

    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onMobileOpenChange(false);
    };
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = originalOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [mobileOpen, onMobileOpenChange]);

  const handleLogout = async () => {
    await logout();
    router.push("/shadow");
  };

  return (
    <>
      {/* Desktop: persistent sidebar, mirrors components/sidebar.tsx's structure. */}
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-border bg-card md:flex">
        <div className="flex h-16 items-center border-b border-border px-4">
          <SidebarLogo />
        </div>
        <div className="flex-1 overflow-y-auto px-3 py-4">
          <NavLinks />
        </div>
        <div className="flex flex-col gap-2 border-t border-border p-4">
          <p className="truncate text-xs font-medium text-muted-foreground">
            {candidate?.first_name} {candidate?.last_name}
          </p>
          <button
            type="button"
            onClick={handleLogout}
            className="flex items-center gap-2 text-xs font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            <LogOut className="h-3.5 w-3.5" />
            Log out
          </button>
        </div>
      </aside>

      {/* Mobile: full-bleed slide-in drawer, same proven pattern as marketing/mobile-nav.tsx. */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            className="fixed inset-0 z-50 flex flex-col bg-background md:hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: reduceMotion ? 0 : 0.2 }}
            role="dialog"
            aria-modal="true"
            aria-label="Shadow navigation"
          >
            <div className="flex h-16 shrink-0 items-center justify-between border-b border-border px-6">
              <SidebarLogo />
              <Button
                ref={closeButtonRef}
                variant="ghost"
                size="icon"
                aria-label="Close menu"
                onClick={() => onMobileOpenChange(false)}
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-6">
              <NavLinks onNavigate={() => onMobileOpenChange(false)} />
            </div>

            <div className="flex shrink-0 flex-col gap-3 border-t border-border px-6 py-6">
              <p className="text-center text-sm text-muted-foreground">
                {candidate?.first_name} {candidate?.last_name}
              </p>
              <Button
                variant="secondary"
                size="lg"
                onClick={() => {
                  onMobileOpenChange(false);
                  handleLogout();
                }}
              >
                <LogOut className="h-4 w-4" />
                Log out
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
