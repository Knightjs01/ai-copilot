"use client";

import * as React from "react";
import { CheckCircle2, CircleDashed } from "lucide-react";
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from "@tanstack/react-table";

import { InviteTeammateDialog } from "@/components/invite-teammate-dialog";
import { RemoveMemberDialog } from "@/components/team/remove-member-dialog";
import { Avatar } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { StatTile } from "@/components/ui/stat-tile";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAuth } from "@/lib/auth-context";
import { useChangeRole, useTeam } from "@/lib/queries/team";
import { ROLE_LABEL, ROLE_VARIANT } from "@/lib/status-display";
import { useThemeScopeContainer } from "@/lib/theme-scope-context";
import { useToast } from "@/lib/toast-context";
import type { RoleName, UserRead } from "@/lib/types";

// Owner deliberately excluded -- the backend has always rejected promoting a user to Owner via
// this endpoint (only Owner-to-Owner handoff exists, and that's not this control's job).
const ROLE_OPTIONS: RoleName[] = ["Recruiter", "Hiring Manager", "Interviewer", "TA Admin"];

function RoleSelect({ userId, role }: { userId: string; role: RoleName }) {
  const changeRole = useChangeRole(userId);
  const container = useThemeScopeContainer();
  const toast = useToast();

  const handleChange = (value: RoleName) => {
    changeRole.mutate(value, {
      onSuccess: () => toast({ title: "Role updated", variant: "success" }),
      onError: () =>
        toast({ title: "Couldn't update role", description: "Try again.", variant: "danger" }),
    });
  };

  return (
    <Select value={role} onValueChange={(value) => handleChange(value as RoleName)}>
      <SelectTrigger className="h-8 w-32 text-xs">
        <SelectValue />
      </SelectTrigger>
      <SelectContent container={container}>
        {ROLE_OPTIONS.map((option) => (
          <SelectItem key={option} value={option}>
            {ROLE_LABEL[option]}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

const columnHelper = createColumnHelper<UserRead>();

export default function TeamPage() {
  const { data: team, isLoading } = useTeam();
  const { user, hasPermission } = useAuth();
  const canChangeRole = hasPermission("users.change_role");
  const canRemove = hasPermission("users.remove");
  const [sorting, setSorting] = React.useState<SortingState>([]);

  const pendingCount = team?.filter((m) => !m.is_email_verified).length ?? 0;

  const columns = React.useMemo(
    () => [
      columnHelper.accessor("full_name", {
        header: "Member",
        cell: (info) => {
          const member = info.row.original;
          return (
            <div className="flex items-center gap-3">
              <Avatar name={member.full_name} />
              <div>
                <p className="text-sm font-medium text-foreground">{member.full_name}</p>
                <p className="text-sm text-muted-foreground">{member.email}</p>
              </div>
            </div>
          );
        },
      }),
      columnHelper.display({
        id: "role",
        header: "Role",
        cell: (info) => {
          const member = info.row.original;
          const isSelf = member.id === user?.id;
          const primaryRole = (member.roles[0] as RoleName) ?? "Recruiter";
          // Owner can never be the target of a role change via this endpoint (self or anyone
          // else's) -- and it's not in ROLE_OPTIONS, so an Owner's own row always renders as a
          // plain badge, not a Select with no matching value.
          return canChangeRole && !isSelf && primaryRole !== "Owner" ? (
            <RoleSelect userId={member.id} role={primaryRole} />
          ) : (
            <div className="flex gap-1.5">
              {member.roles.map((role) => (
                <Badge key={role} variant={ROLE_VARIANT[role as RoleName]}>
                  {ROLE_LABEL[role as RoleName] ?? role}
                </Badge>
              ))}
            </div>
          );
        },
      }),
      columnHelper.accessor("is_email_verified", {
        header: "Status",
        cell: (info) =>
          info.getValue() ? (
            <span className="flex items-center gap-1 text-xs text-muted-foreground" title="Email verified">
              <CheckCircle2 className="h-3.5 w-3.5 text-success" />
              Verified
            </span>
          ) : (
            <span className="flex items-center gap-1 text-xs text-muted-foreground" title="Invite pending">
              <CircleDashed className="h-3.5 w-3.5" />
              Pending
            </span>
          ),
      }),
      columnHelper.display({
        id: "actions",
        header: "",
        cell: (info) => {
          const member = info.row.original;
          const isSelf = member.id === user?.id;
          return canRemove && !isSelf ? (
            <div className="flex justify-end">
              <RemoveMemberDialog userId={member.id} fullName={member.full_name} />
            </div>
          ) : null;
        },
      }),
    ],
    [canChangeRole, canRemove, user?.id]
  );

  const table = useReactTable({
    data: team ?? [],
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-foreground">Team</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Everyone here sees the same hiring projects and candidates.
          </p>
        </div>
        {hasPermission("users.invite") && <InviteTeammateDialog />}
      </div>

      {isLoading ? (
        <div className="flex flex-col gap-8">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
          <Skeleton className="h-48 w-full" />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <StatTile label="Team members" value={team?.length ?? 0} />
            <StatTile label="Pending invites" value={pendingCount} />
          </div>

          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  {table.getHeaderGroups().map((headerGroup) => (
                    <TableRow key={headerGroup.id}>
                      {headerGroup.headers.map((header) => (
                        <TableHead
                          key={header.id}
                          sortable={header.column.getCanSort()}
                          sortDirection={header.column.getIsSorted()}
                          onSort={header.column.getToggleSortingHandler()}
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                        </TableHead>
                      ))}
                    </TableRow>
                  ))}
                </TableHeader>
                <TableBody>
                  {table.getRowModel().rows.map((row) => (
                    <TableRow key={row.id}>
                      {row.getVisibleCells().map((cell) => (
                        <TableCell key={cell.id}>
                          {flexRender(cell.column.columnDef.cell, cell.getContext())}
                        </TableCell>
                      ))}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
