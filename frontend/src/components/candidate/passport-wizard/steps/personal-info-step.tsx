"use client";

import { Lock } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Field } from "@/components/ui/field";
import { Input } from "@/components/ui/input";

interface PersonalInfoStepProps {
  firstName: string;
  onFirstNameChange: (value: string) => void;
  lastName: string;
  onLastNameChange: (value: string) => void;
  phone: string;
  onPhoneChange: (value: string) => void;
  address: string;
  onAddressChange: (value: string) => void;
}

export function PersonalInfoStep({
  firstName,
  onFirstNameChange,
  lastName,
  onLastNameChange,
  phone,
  onPhoneChange,
  address,
  onAddressChange,
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
          <Field label="Phone" htmlFor="phone">
            <Input id="phone" value={phone} onChange={(e) => onPhoneChange(e.target.value)} />
          </Field>
          <Field label="Address" htmlFor="address">
            <Input id="address" value={address} onChange={(e) => onAddressChange(e.target.value)} />
          </Field>
        </CardContent>
      </Card>
    </div>
  );
}
