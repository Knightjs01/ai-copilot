"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  Bell,
  Bookmark,
  Briefcase,
  Building2,
  CalendarClock,
  Compass,
  Home,
  IdCard,
  LogOut,
  MessageCircle,
  MessageSquare,
  Sparkles,
  X,
  type LucideIcon,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { useCandidateAuth } from "@/lib/candidate-auth-context";
import { useMyMessageThreads } from "@/lib/queries/messages";
import { useMyPassport, useUpdatePassportVisibility } from "@/lib/queries/phantom-passport";
import { useMyIntroductionRequests } from "@/lib/queries/shadow-introductions";
import { cn } from "@/lib/utils";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

// Companies (a browse surface) sits with Discover/For You; Introductions (inbound communication)
// sits right before Messages, since both carry an unread-style badge (see NavLinks below).
// Originally this list only had the routes promoted from the old mobile nav bar/command palette;
// Introductions and Companies were moved in from Private Tools since they're everyday surfaces a
// candidate needs quick access to, not passport-adjacent settings.
const MAIN_NAV_ITEMS: NavItem[] = [
  { label: "Home", href: "/shadow/home", icon: Home },
  { label: "Discover Roles", href: "/shadow", icon: Compass },
  { label: "For You", href: "/shadow/for-you", icon: Sparkles },
  { label: "Companies", href: "/shadow/companies", icon: Building2 },
  { label: "Applications", href: "/shadow/applications", icon: Briefcase },
  { label: "Introductions", href: "/shadow/introductions", icon: MessageCircle },
  { label: "Messages", href: "/shadow/messages", icon: MessageSquare },
  { label: "Interviews", href: "/shadow/interviews", icon: CalendarClock },
];

// "Private Tools" — Passport and its directly related surfaces only. Alerts is a real,
// already-built feature (job_alerts) that previously only lived inside Saved Jobs with no nav
// entry of its own — this links straight to that same page's #alerts section rather than
// duplicating a second page for it. Deliberately no "People" item here or anywhere else in this
// sidebar: Shadow has no concept of a browsable, named candidate directory, and building one
// would contradict the whole anonymity model (candidates are only ever a callsign until a Reveal
// Request is approved).
const PRIVATE_TOOL_ITEMS: NavItem[] = [
  { label: "My Passport", href: "/shadow/passport", icon: IdCard },
  { label: "Saved Jobs", href: "/shadow/saved-jobs", icon: Bookmark },
  { label: "Alerts", href: "/shadow/saved-jobs#alerts", icon: Bell },
];

function NavItemLink({
  item,
  isActive,
  badge,
  onNavigate,
}: {
  item: NavItem;
  isActive: boolean;
  badge?: number;
  onNavigate?: () => void;
}) {
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      className={cn(
        "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
        isActive
          ? "bg-brand/10 text-brand"
          : "text-muted-foreground hover:bg-secondary hover:text-foreground"
      )}
    >
      <span className="relative shrink-0">
        <item.icon className="h-4 w-4" />
        {!!badge && badge > 0 && (
          <span className="absolute -right-1.5 -top-1.5 flex h-3.5 min-w-3.5 items-center justify-center rounded-full bg-info px-1 text-[9px] font-semibold text-info-foreground">
            {badge}
          </span>
        )}
      </span>
      {item.label}
    </Link>
  );
}

// Quick shortcut on top of the real, 3-state PassportVisibility field (private/match_only/
// discoverable) — match_only and discoverable read identically today (see status-display.ts), so
// collapsing to a binary switch here is an honest simplification, not a loss of real
// functionality. The full 3-way picker still lives in the wizard's Preferences step for anyone
// who wants match_only specifically.
function AnonymousModeToggle() {
  const { data: passport } = useMyPassport();
  const updateVisibility = useUpdatePassportVisibility();
  if (!passport) return null;

  const isAnonymous = passport.visibility === "private";

  return (
    <div className="flex items-center justify-between gap-3 rounded-lg px-3 py-2">
      <span className="text-sm font-medium text-muted-foreground">Anonymous Mode</span>
      <Switch
        checked={isAnonymous}
        aria-label="Anonymous Mode"
        disabled={updateVisibility.isPending}
        onCheckedChange={(checked) =>
          updateVisibility.mutate(checked ? "private" : "discoverable")
        }
      />
    </div>
  );
}

function NavLinks({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const { candidate } = useCandidateAuth();
  const { data: threads } = useMyMessageThreads({ enabled: !!candidate });
  const unreadCount = threads?.reduce((sum, t) => sum + t.unread_count, 0) ?? 0;
  const { data: introRequests } = useMyIntroductionRequests();
  const pendingIntroCount = introRequests?.filter((r) => r.status === "pending").length ?? 0;

  const isActive = (href: string) => {
    const path = href.split("#")[0]!;
    return path === "/shadow" ? pathname === "/shadow" : pathname === path || pathname?.startsWith(`${path}/`);
  };

  return (
    <div className="flex flex-col gap-5">
      <nav className="flex flex-col gap-1">
        {MAIN_NAV_ITEMS.map((item) => (
          <NavItemLink
            key={item.href}
            item={item}
            isActive={isActive(item.href)}
            badge={
              item.href === "/shadow/messages"
                ? unreadCount
                : item.href === "/shadow/introductions"
                  ? pendingIntroCount
                  : undefined
            }
            onNavigate={onNavigate}
          />
        ))}
      </nav>

      <div className="flex flex-col gap-1">
        <p className="px-3 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground/70">
          Private Tools
        </p>
        {PRIVATE_TOOL_ITEMS.map((item) => (
          <NavItemLink
            key={item.href}
            item={item}
            isActive={isActive(item.href)}
            onNavigate={onNavigate}
          />
        ))}
        <AnonymousModeToggle />
      </div>
    </div>
  );
}

// Static reassurance panel, matching the real, already-established anonymity copy used elsewhere
// in Shadow (e.g. the Discover board's own header blurb) — no new claims invented for this.
function YoureInControlPanel() {
  return (
    <div className="mx-3 flex flex-col items-center gap-3 rounded-2xl border border-border bg-secondary/30 p-4 text-center">
      <Image src="/phantom-icon.png" alt="" width={36} height={29} className="opacity-70" />
      <div className="flex flex-col gap-1">
        <p className="text-sm font-semibold text-foreground">You&apos;re in control</p>
        <p className="text-xs text-muted-foreground">
          Your identity is protected. Reveal it when you choose.
        </p>
      </div>
      <Link
        href="/passport"
        className="text-xs font-medium text-brand underline-offset-2 hover:underline"
      >
        How it works
      </Link>
    </div>
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
        className="h-11 w-auto"
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
        <div className="flex flex-1 flex-col gap-6 overflow-y-auto px-3 py-4">
          <NavLinks />
          <YoureInControlPanel />
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

            <div className="flex flex-1 flex-col gap-6 overflow-y-auto px-4 py-6">
              <NavLinks onNavigate={() => onMobileOpenChange(false)} />
              <YoureInControlPanel />
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
