"use client";

import Link from "next/link";
import { ArrowRight, Building2, ShieldCheck, Users } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";

export default function SettingsHubPage() {
  const { hasPermission } = useAuth();
  const canManageCompany = hasPermission("company.manage_settings");

  // Project Vault moved to the sidebar's own "Data" group -- no longer listed here, to avoid
  // showing the same destination in two places (see sidebar.tsx).
  const items = [
    { title: "Team", description: "Manage teammates, roles, and invitations.", href: "/team", icon: Users, visible: true },
    {
      title: "Company Profile",
      description: "Company info, branding, and public profile settings.",
      href: "/company",
      icon: Building2,
      visible: canManageCompany,
    },
    {
      title: "Security",
      description: "MFA, sessions, and account security settings.",
      href: "/security",
      icon: ShieldCheck,
      visible: true,
    },
  ].filter((item) => item.visible);

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">Administration, separate from day-to-day hiring.</p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {items.map((item) => (
          <Link key={item.href} href={item.href}>
            <Card className="h-full transition-colors hover:border-brand">
              <CardHeader className="flex-row items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <item.icon className="h-4 w-4 text-brand" />
                  {item.title}
                </CardTitle>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{item.description}</p>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
