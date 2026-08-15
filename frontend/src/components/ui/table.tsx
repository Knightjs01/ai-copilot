import * as React from "react";
import { ChevronDown, ChevronsUpDown, ChevronUp } from "lucide-react";

import { cn } from "@/lib/utils";

function Table({ className, ...props }: React.HTMLAttributes<HTMLTableElement>) {
  return (
    <div className="overflow-x-auto">
      <table className={cn("w-full text-sm", className)} {...props} />
    </div>
  );
}

function TableHeader({ className, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) {
  return <thead className={cn(className)} {...props} />;
}

function TableBody({ className, ...props }: React.HTMLAttributes<HTMLTableSectionElement>) {
  return <tbody className={cn(className)} {...props} />;
}

function TableRow({ className, ...props }: React.HTMLAttributes<HTMLTableRowElement>) {
  return <tr className={cn("border-b border-border last:border-0", className)} {...props} />;
}

type SortDirection = "asc" | "desc" | false;

function TableHead({
  className,
  sortable,
  sortDirection,
  onSort,
  children,
  ...props
}: React.ThHTMLAttributes<HTMLTableCellElement> & {
  sortable?: boolean;
  sortDirection?: SortDirection;
  onSort?: (event: unknown) => void;
}) {
  if (!sortable) {
    return (
      <th
        className={cn(
          "px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground",
          className
        )}
        {...props}
      >
        {children}
      </th>
    );
  }

  const Icon = sortDirection === "asc" ? ChevronUp : sortDirection === "desc" ? ChevronDown : ChevronsUpDown;

  return (
    <th
      className={cn(
        "px-4 py-3 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground",
        className
      )}
      {...props}
    >
      <button
        type="button"
        onClick={onSort}
        className="flex items-center gap-1 transition-colors hover:text-foreground"
      >
        {children}
        <Icon className={cn("h-3 w-3", sortDirection ? "text-foreground" : "text-muted-foreground/50")} />
      </button>
    </th>
  );
}

function TableCell({ className, ...props }: React.TdHTMLAttributes<HTMLTableCellElement>) {
  return <td className={cn("px-4 py-3", className)} {...props} />;
}

export { Table, TableHeader, TableBody, TableRow, TableHead, TableCell };
