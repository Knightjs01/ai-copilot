"use client";

import { Search } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { EMPLOYMENT_TYPE_LABEL, REMOTE_PREFERENCE_LABEL } from "@/lib/status-display";
import type { EmploymentType, RemotePreference } from "@/lib/types";

const REMOTE_OPTIONS = Object.keys(REMOTE_PREFERENCE_LABEL) as RemotePreference[];
const EMPLOYMENT_OPTIONS = Object.keys(EMPLOYMENT_TYPE_LABEL) as EmploymentType[];

export function ShadowBoardToolbar({
  search,
  onSearchChange,
  remotePreference,
  onRemotePreferenceChange,
  employmentType,
  onEmploymentTypeChange,
  matchCount,
  totalCount,
  container,
}: {
  search: string;
  onSearchChange: (value: string) => void;
  remotePreference: RemotePreference | "all";
  onRemotePreferenceChange: (value: RemotePreference | "all") => void;
  employmentType: EmploymentType | "all";
  onEmploymentTypeChange: (value: EmploymentType | "all") => void;
  matchCount: number;
  totalCount: number;
  container: HTMLElement | null;
}) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
      <div className="relative w-full sm:max-w-xs">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search roles by skill, not by title…"
          className="pl-9"
        />
      </div>

      <Select
        value={remotePreference}
        onValueChange={(value) => onRemotePreferenceChange(value as RemotePreference | "all")}
      >
        <SelectTrigger className="w-full sm:w-40">
          <SelectValue placeholder="Any location" />
        </SelectTrigger>
        <SelectContent container={container}>
          <SelectItem value="all">Any location</SelectItem>
          {REMOTE_OPTIONS.map((option) => (
            <SelectItem key={option} value={option}>
              {REMOTE_PREFERENCE_LABEL[option]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
        value={employmentType}
        onValueChange={(value) => onEmploymentTypeChange(value as EmploymentType | "all")}
      >
        <SelectTrigger className="w-full sm:w-40">
          <SelectValue placeholder="Any type" />
        </SelectTrigger>
        <SelectContent container={container}>
          <SelectItem value="all">Any type</SelectItem>
          {EMPLOYMENT_OPTIONS.map((option) => (
            <SelectItem key={option} value={option}>
              {EMPLOYMENT_TYPE_LABEL[option]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <span className="shrink-0 text-xs text-muted-foreground">
        {matchCount} of {totalCount} roles
      </span>
    </div>
  );
}
