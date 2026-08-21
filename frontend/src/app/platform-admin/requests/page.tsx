"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Inbox } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { Spinner } from "@/components/ui/spinner";
import { StatTile } from "@/components/ui/stat-tile";
import { Textarea } from "@/components/ui/textarea";
import { PlatformAdminNav } from "@/components/platform-admin/platform-admin-nav";
import {
  useAccessRequests,
  useApproveAccessRequest,
  useDashboardStats,
  useRejectAccessRequest,
  useRequestMoreInfo,
} from "@/lib/queries/platform-admin";
import { usePlatformAdminAuth } from "@/lib/platform-admin-auth-context";
import type { CompanyAccessRequest } from "@/lib/types";

const STATUS_OPTIONS: { value: "pending" | "all"; label: string }[] = [
  { value: "pending", label: "Pending" },
  { value: "all", label: "All requests" },
];

function RequestCard({ request }: { request: CompanyAccessRequest }) {
  const approve = useApproveAccessRequest();
  const reject = useRejectAccessRequest();
  const requestInfo = useRequestMoreInfo();
  const [mode, setMode] = React.useState<"idle" | "rejecting" | "requesting-info">("idle");
  const [note, setNote] = React.useState("");

  const isPending = approve.isPending || reject.isPending || requestInfo.isPending;
  const isReviewed = request.status !== "pending";

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 py-5">
        <div className="flex flex-col gap-0.5">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-semibold text-foreground">{request.company_name}</h3>
            {isReviewed && (
              <span
                className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                  request.status === "approved"
                    ? "bg-success/10 text-success"
                    : "bg-danger/10 text-danger"
                }`}
              >
                {request.status}
              </span>
            )}
          </div>
          <p className="text-sm text-muted-foreground">
            {request.full_name}
            {request.job_title ? ` · ${request.job_title}` : ""}
          </p>
          <p className="text-sm text-muted-foreground">{request.work_email}</p>
          <p className="text-xs text-muted-foreground">
            Requested {new Date(request.created_at).toLocaleString()}
          </p>
        </div>

        {mode !== "idle" && (
          <Textarea
            placeholder={mode === "rejecting" ? "Reason (optional)" : "What's missing?"}
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={2}
          />
        )}

        {(approve.isError || reject.isError || requestInfo.isError) && (
          <p className="text-sm font-medium text-danger">Couldn&apos;t save. Try again.</p>
        )}
        {requestInfo.isSuccess && mode === "idle" && (
          <p className="text-sm font-medium text-success">Info request sent.</p>
        )}

        {!isReviewed && (
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="brand"
              size="sm"
              onClick={() => approve.mutate(request.id)}
              disabled={isPending}
            >
              {approve.isPending ? "Approving…" : "Approve"}
            </Button>
            {mode === "rejecting" ? (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => reject.mutate({ requestId: request.id, reason: note || undefined })}
                disabled={isPending}
              >
                {reject.isPending ? "Rejecting…" : "Confirm reject"}
              </Button>
            ) : (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setMode("rejecting")}
                disabled={isPending}
              >
                Reject
              </Button>
            )}
            {mode === "requesting-info" ? (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => {
                  if (!note.trim()) return;
                  requestInfo.mutate(
                    { requestId: request.id, message: note },
                    { onSuccess: () => setMode("idle") }
                  );
                }}
                disabled={isPending || !note.trim()}
              >
                {requestInfo.isPending ? "Sending…" : "Send request"}
              </Button>
            ) : (
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={() => setMode("requesting-info")}
                disabled={isPending}
              >
                Request info
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function PlatformAdminRequestsPage() {
  const router = useRouter();
  const { admin, isLoading: authLoading } = usePlatformAdminAuth();
  const [statusFilter, setStatusFilter] = React.useState<"pending" | "all">("pending");
  const { data: requests, isLoading } = useAccessRequests(statusFilter);
  const { data: stats } = useDashboardStats();

  React.useEffect(() => {
    if (!authLoading && !admin) router.push("/platform-admin/login");
  }, [authLoading, admin, router]);

  if (authLoading || !admin) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner className="h-6 w-6 text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-3xl flex-col gap-6 px-6 py-10">
      <PlatformAdminNav admin={admin} />

      {stats && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
          <StatTile label="Pending" value={stats.pending_requests} />
          <StatTile label="Approved" value={stats.approved_requests} />
          <StatTile label="Rejected" value={stats.rejected_requests} />
          <StatTile label="Active companies" value={stats.active_companies} />
          <StatTile label="Suspended" value={stats.suspended_companies} />
        </div>
      )}

      <PillToggleGroup options={STATUS_OPTIONS} value={statusFilter} onChange={setStatusFilter} />

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && requests?.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
            <Inbox className="h-5 w-5 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              {statusFilter === "pending" ? "No pending requests." : "No requests yet."}
            </p>
          </CardContent>
        </Card>
      )}

      {!isLoading && requests && requests.length > 0 && (
        <div className="flex flex-col gap-3">
          {requests.map((request) => (
            <RequestCard key={request.id} request={request} />
          ))}
        </div>
      )}
    </div>
  );
}
