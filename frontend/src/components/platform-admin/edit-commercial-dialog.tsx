"use client";

import * as React from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { PillToggleGroup } from "@/components/ui/pill-toggle";
import { useUpdateCompanyCommercial } from "@/lib/queries/commercial";
import type { AdminCompanySummary, CommercialPlanCode } from "@/lib/types";

const PLAN_OPTIONS: { value: CommercialPlanCode; label: string }[] = [
  { value: "core", label: "Core" },
  { value: "growth", label: "Growth" },
  { value: "scale", label: "Scale" },
];

export function EditCommercialDialog({ company }: { company: AdminCompanySummary }) {
  const [open, setOpen] = React.useState(false);
  const [plan, setPlan] = React.useState<CommercialPlanCode>(
    company.commercial_plan_code ?? "core"
  );
  const [override, setOverride] = React.useState(
    company.active_role_limit_override !== null ? String(company.active_role_limit_override) : ""
  );
  const [reason, setReason] = React.useState("");
  const update = useUpdateCompanyCommercial();

  const onOpenChange = (next: boolean) => {
    setOpen(next);
    if (!next) {
      setPlan(company.commercial_plan_code ?? "core");
      setOverride(
        company.active_role_limit_override !== null
          ? String(company.active_role_limit_override)
          : ""
      );
      setReason("");
      update.reset();
    }
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    update.mutate(
      {
        companyId: company.id,
        planCode: plan,
        activeRoleLimitOverride: override.trim() === "" ? null : Number(override),
        reason: reason.trim() === "" ? undefined : reason,
      },
      { onSuccess: () => onOpenChange(false) }
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button type="button" variant="secondary" size="sm">
          Plan
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Commercial plan — {company.name}</DialogTitle>
        </DialogHeader>
        <form className="flex flex-col gap-4" onSubmit={onSubmit}>
          <Field label="Plan">
            <PillToggleGroup options={PLAN_OPTIONS} value={plan} onChange={setPlan} />
          </Field>
          <Field label="Active-role limit override" htmlFor="active-role-override">
            <Input
              id="active-role-override"
              type="number"
              min={0}
              value={override}
              onChange={(e) => setOverride(e.target.value)}
              placeholder="Plan default"
            />
            <p className="text-xs text-muted-foreground">
              Leave blank to use the plan&apos;s own default. Set a number to override it (e.g. a
              negotiated Scale limit).
            </p>
          </Field>
          <Field label="Reason (optional)" htmlFor="commercial-reason">
            <Input
              id="commercial-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Negotiated Scale contract, 25 roles"
            />
          </Field>
          {update.isError && (
            <p className="text-sm font-medium text-danger">Couldn&apos;t save. Try again.</p>
          )}
          <DialogFooter>
            <Button
              type="button"
              variant="secondary"
              onClick={() => onOpenChange(false)}
              disabled={update.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={update.isPending}>
              {update.isPending ? "Saving…" : "Save"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
