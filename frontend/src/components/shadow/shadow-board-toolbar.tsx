"use client";

import * as React from "react";
import { Bell, Search, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
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
  onAskPhantom,
  isAskPhantomPending,
  canAskPhantom,
  onSaveSearch,
  isSaveSearchPending,
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
  // Ask Phantom (natural-language search) is candidate-only -- callers omit onAskPhantom
  // entirely for logged-out visitors rather than passing a handler that would 401.
  onAskPhantom?: (query: string) => void;
  isAskPhantomPending?: boolean;
  canAskPhantom?: boolean;
  // Save this search as a Job Alert -- same candidate-only omission convention as Ask Phantom.
  // Callers only render this when at least one filter is set (an alert needs real criteria).
  onSaveSearch?: (name: string) => void;
  isSaveSearchPending?: boolean;
}) {
  const [askOpen, setAskOpen] = React.useState(false);
  const [askQuery, setAskQuery] = React.useState("");
  const [saveOpen, setSaveOpen] = React.useState(false);
  const [alertName, setAlertName] = React.useState("");

  const submitAsk = () => {
    const trimmed = askQuery.trim();
    if (trimmed && onAskPhantom) onAskPhantom(trimmed);
  };

  const submitSaveSearch = () => {
    if (!onSaveSearch) return;
    onSaveSearch(alertName.trim());
    setAlertName("");
    setSaveOpen(false);
  };

  return (
    <div className="flex flex-col gap-3">
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

        {canAskPhantom && (
          <Button
            type="button"
            variant="secondary"
            size="sm"
            className="shrink-0"
            onClick={() => setAskOpen((v) => !v)}
          >
            <Sparkles className="h-3.5 w-3.5" />
            Ask Phantom
          </Button>
        )}

        {onSaveSearch && (remotePreference !== "all" || employmentType !== "all") && (
          <Button
            type="button"
            variant="secondary"
            size="sm"
            className="shrink-0"
            onClick={() => setSaveOpen((v) => !v)}
          >
            <Bell className="h-3.5 w-3.5" />
            Save this search
          </Button>
        )}

        <span className="shrink-0 text-xs text-muted-foreground sm:ml-auto">
          {matchCount} of {totalCount} roles
        </span>
      </div>

      {onSaveSearch && saveOpen && (
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <Input
            value={alertName}
            onChange={(e) => setAlertName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submitSaveSearch();
            }}
            placeholder="Name this alert (optional)"
            className="sm:max-w-sm"
            autoFocus
          />
          <Button
            type="button"
            size="sm"
            variant="brand"
            onClick={submitSaveSearch}
            disabled={isSaveSearchPending}
          >
            {isSaveSearchPending ? "Saving…" : "Save alert"}
          </Button>
        </div>
      )}

      {canAskPhantom && askOpen && (
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <Input
            value={askQuery}
            onChange={(e) => setAskQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") submitAsk();
            }}
            placeholder="Try: remote senior roles"
            className="sm:max-w-sm"
            autoFocus
          />
          <Button
            type="button"
            size="sm"
            variant="brand"
            onClick={submitAsk}
            disabled={!askQuery.trim() || isAskPhantomPending}
          >
            {isAskPhantomPending ? "Thinking…" : "Search"}
          </Button>
        </div>
      )}
    </div>
  );
}
