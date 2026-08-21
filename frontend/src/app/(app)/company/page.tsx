"use client";

import { ShieldAlert } from "lucide-react";

import { CompanyProfileWizard } from "@/components/company/company-profile-wizard";
import { useAuth } from "@/lib/auth-context";

export default function CompanyProfilePage() {
  const { hasPermission } = useAuth();
  const canManage = hasPermission("company.manage_settings");

  if (!canManage) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border py-24 text-center">
        <ShieldAlert className="h-8 w-8 text-muted-foreground" />
        <p className="text-sm font-medium text-foreground">
          Company Profile isn&apos;t available on your role
        </p>
        <p className="max-w-xs text-sm text-muted-foreground">
          Ask an Owner or TA Admin on your team for access.
        </p>
      </div>
    );
  }

  return <CompanyProfileWizard />;
}
