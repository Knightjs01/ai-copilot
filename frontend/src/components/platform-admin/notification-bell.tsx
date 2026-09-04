"use client";

import * as React from "react";
import { Bell } from "lucide-react";

import {
  useMarkNotificationsRead,
  useNotifications,
  useUnreadNotificationCount,
} from "@/lib/queries/platform-admin";
import { cn } from "@/lib/utils";

// Mirrors GlobalSearchBox's click-outside + absolute-positioned dropdown shape exactly. The
// unread count polls independently (cheap, dedicated endpoint) so the badge stays live even
// while the panel is closed; opening the panel marks everything read once, not per-item -- see
// the plan this shipped under for why a single per-admin watermark is the honest, simplest
// correct design here.
export function NotificationBell() {
  const [open, setOpen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const { data: unreadData } = useUnreadNotificationCount();
  const { data: notificationsData, isFetching } = useNotifications({ pageSize: 10 });
  const markRead = useMarkNotificationsRead();

  const unreadCount = unreadData?.unread_count ?? 0;

  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleToggle = () => {
    const next = !open;
    setOpen(next);
    if (next && unreadCount > 0) {
      markRead.mutate();
    }
  };

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={handleToggle}
        className="relative flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-card text-muted-foreground hover:text-foreground"
        aria-label="Notifications"
      >
        <Bell className="h-4 w-4" />
        {unreadCount > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-danger px-1 text-[10px] font-semibold text-danger-foreground">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-20 mt-1 w-80 overflow-hidden rounded-xl border border-border bg-card shadow-lg shadow-slate-900/10">
          <p className="border-b border-border px-3.5 py-2.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
            Notifications
          </p>
          {isFetching && (
            <p className="px-3.5 py-3 text-xs text-muted-foreground">Loading…</p>
          )}
          {!isFetching && (notificationsData?.items.length ?? 0) === 0 && (
            <p className="px-3.5 py-3 text-xs text-muted-foreground">Nothing yet.</p>
          )}
          {!isFetching &&
            notificationsData?.items.map((notification) => (
              <div
                key={notification.id}
                className={cn(
                  "flex flex-col gap-0.5 border-b border-border px-3.5 py-2.5 last:border-b-0"
                )}
              >
                <p className="text-sm font-medium text-foreground">{notification.title}</p>
                <p className="text-xs text-muted-foreground">{notification.body}</p>
                <p className="text-[11px] text-muted-foreground">
                  {new Date(notification.created_at).toLocaleString()}
                </p>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
