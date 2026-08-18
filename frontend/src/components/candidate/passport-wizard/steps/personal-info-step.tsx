"use client";

import { Lock, Mail } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";

interface PersonalInfoStepProps {
  firstName: string;
  onFirstNameChange: (value: string) => void;
  lastName: string;
  onLastNameChange: (value: string) => void;
  // Read-only — this is the candidate's real login email from candidate_auth signup, not a
  // second editable contact field. One email per candidate, already verified.
  email: string;
  phone: string;
  onPhoneChange: (value: string) => void;
  location: string;
  onLocationChange: (value: string) => void;
}

export function PersonalInfoStep({
  firstName,
  onFirstNameChange,
  lastName,
  onLastNameChange,
  email,
  phone,
  onPhoneChange,
  location,
  onLocationChange,
}: PersonalInfoStepProps) {
  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>Personal identity — private</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex items-start gap-2.5 rounded-xl border border-border bg-background px-4 py-3">
            <Lock className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
            <p className="text-xs text-muted-foreground">
              This is encrypted and kept separate from your professional profile. It&apos;s never
              shown to a company unless you personally approve a Reveal Request.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Field label="First name" htmlFor="firstName">
              <Input
                id="firstName"
                value={firstName}
                onChange={(e) => onFirstNameChange(e.target.value)}
              />
            </Field>
            <Field label="Last name" htmlFor="lastName">
              <Input
                id="lastName"
                value={lastName}
                onChange={(e) => onLastNameChange(e.target.value)}
              />
            </Field>
          </div>
          <Field label="Email address" htmlFor="email">
            <div className="flex items-center gap-2 rounded-xl border border-border bg-secondary px-3 py-2.5 text-sm text-muted-foreground">
              <Mail className="h-4 w-4 shrink-0" />
              {email}
            </div>
          </Field>
          <Field label="Phone" htmlFor="phone">
            <Input id="phone" value={phone} onChange={(e) => onPhoneChange(e.target.value)} />
          </Field>
          <Field label="Location" htmlFor="location">
            <Input
              id="location"
              placeholder="e.g. London, UK"
              value={location}
              onChange={(e) => onLocationChange(e.target.value)}
            />
          </Field>
        </CardContent>
      </Card>
    </div>
  );
}
