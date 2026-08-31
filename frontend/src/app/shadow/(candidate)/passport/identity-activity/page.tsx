"use client";

import { Lock, ShieldCheck } from "lucide-react";

import { EmptyState } from "@/components/shadow/empty-state";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { useMyRevealHistory } from "@/lib/queries/shadow-reveal";
import { SHADOW_FIELD_LABEL } from "@/lib/status-display";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

// The candidate-wide "who has seen my identity" timeline -- every reveal request/response
// across every application, not scoped to one. Real data via GET /shadow-reveal/my-history.
export default function IdentityActivityPage() {
  const { data: history, isLoading } = useMyRevealHistory();

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Identity activity
        </h1>
        <p className="text-sm text-muted-foreground">
          Every time a company has requested to see your real identity, and how you responded.
        </p>
      </div>

      {isLoading && (
        <div className="flex justify-center py-16">
          <Spinner className="h-6 w-6 text-muted-foreground" />
        </div>
      )}

      {!isLoading && history?.length === 0 && (
        <EmptyState
          icon={Lock}
          title="No company has requested your identity yet"
          description="You'll see it here the moment one does."
        />
      )}

      <div className="flex flex-col gap-3">
        {history?.map((item) => (
          <Card key={item.id}>
            <CardContent className="flex flex-col gap-2 py-5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex flex-col gap-0.5">
                  <h2 className="text-sm font-semibold text-foreground">{item.job_title}</h2>
                  <p className="text-xs text-muted-foreground">{item.company_name}</p>
                </div>
                <Badge
                  variant={
                    item.status === "approved"
                      ? "success"
                      : item.status === "declined"
                        ? "outline"
                        : "info"
                  }
                >
                  {item.status === "approved"
                    ? "Approved"
                    : item.status === "declined"
                      ? "Declined"
                      : "Pending"}
                </Badge>
              </div>

              {item.reason && (
                <p className="text-sm text-muted-foreground">&ldquo;{item.reason}&rdquo;</p>
              )}

              <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                <span>Requested {formatDate(item.requested_at)}</span>
                {item.responded_at && <span>· Responded {formatDate(item.responded_at)}</span>}
              </div>

              {item.status === "approved" && (
                <div className="flex flex-wrap items-center gap-1.5 border-t border-border pt-2.5">
                  <ShieldCheck className="h-3.5 w-3.5 shrink-0 text-success" />
                  <span className="text-xs text-muted-foreground">Shared:</span>
                  {item.disclosed_fields ? (
                    item.disclosed_fields.map((field) => (
                      <Badge key={field} variant="outline">
                        {SHADOW_FIELD_LABEL[field]}
                      </Badge>
                    ))
                  ) : (
                    <Badge variant="outline">Everything</Badge>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
