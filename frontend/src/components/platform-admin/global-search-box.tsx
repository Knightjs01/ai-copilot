"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Building2, Search, User, Briefcase } from "lucide-react";

import { Input } from "@/components/ui/input";
import { useGlobalSearch } from "@/lib/queries/platform-admin";
import { cn } from "@/lib/utils";
import type { GlobalSearchResultItem, GlobalSearchResultType } from "@/lib/types";

const TYPE_ICON: Record<GlobalSearchResultType, typeof Building2> = {
  company: Building2,
  job: Briefcase,
  candidate: User,
};

const TYPE_LABEL: Record<GlobalSearchResultType, string> = {
  company: "Companies",
  job: "Jobs",
  candidate: "Candidates",
};

const SEARCH_PAGE_BY_TYPE: Record<GlobalSearchResultType, string> = {
  company: "/platform-admin/companies",
  job: "/platform-admin/jobs",
  candidate: "/platform-admin/candidates",
};

// A plain Input + floating grouped-results list, mirroring LocationAutocomplete's exact pattern
// (no cmdk -- this admin surface has no ⌘K command palette to hook into). Each type shows at
// most a handful of results with a "See all" link into that entity's own now-searchable list
// page rather than inventing a merged, paginated cross-type result view.
export function GlobalSearchBox() {
  const router = useRouter();
  const [query, setQuery] = React.useState("");
  const [debouncedQuery, setDebouncedQuery] = React.useState("");
  const [open, setOpen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handle = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(handle);
  }, [query]);

  const { data: results, isFetching } = useGlobalSearch(debouncedQuery);

  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const grouped = React.useMemo(() => {
    const groups = new Map<GlobalSearchResultType, GlobalSearchResultItem[]>();
    for (const item of results ?? []) {
      const existing = groups.get(item.type) ?? [];
      existing.push(item);
      groups.set(item.type, existing);
    }
    return groups;
  }, [results]);

  const showDropdown = open && query.trim().length >= 2;

  return (
    <div ref={containerRef} className="relative w-full sm:w-72">
      <div className="relative">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search companies, jobs, candidates…"
          value={query}
          autoComplete="off"
          className="pl-9"
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setOpen(true)}
        />
      </div>
      {showDropdown && (
        <div className="absolute z-20 mt-1 w-full overflow-hidden rounded-xl border border-border bg-card shadow-lg shadow-slate-900/10">
          {isFetching && (
            <p className="px-3.5 py-3 text-xs text-muted-foreground">Searching…</p>
          )}
          {!isFetching && (results?.length ?? 0) === 0 && (
            <p className="px-3.5 py-3 text-xs text-muted-foreground">
              No results for &quot;{query}&quot;.
            </p>
          )}
          {!isFetching &&
            Array.from(grouped.entries()).map(([type, items]) => {
              const Icon = TYPE_ICON[type];
              return (
                <div key={type} className="border-b border-border last:border-b-0">
                  <p className="px-3.5 pt-2.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    {TYPE_LABEL[type]}
                  </p>
                  {items.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => {
                        setOpen(false);
                        setQuery("");
                        router.push(item.url);
                      }}
                      className={cn(
                        "flex w-full items-center gap-2 px-3.5 py-2 text-left text-sm text-foreground",
                        "hover:bg-secondary"
                      )}
                    >
                      <Icon className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                      <span className="flex min-w-0 flex-1 flex-col">
                        <span className="truncate">{item.title}</span>
                        <span className="truncate text-xs text-muted-foreground">
                          {item.subtitle}
                        </span>
                      </span>
                    </button>
                  ))}
                  <button
                    type="button"
                    onClick={() => {
                      setOpen(false);
                      router.push(`${SEARCH_PAGE_BY_TYPE[type]}?search=${encodeURIComponent(query)}`);
                    }}
                    className="block w-full px-3.5 py-2 text-left text-xs font-medium text-brand hover:underline"
                  >
                    See all {TYPE_LABEL[type].toLowerCase()} results →
                  </button>
                </div>
              );
            })}
        </div>
      )}
    </div>
  );
}
