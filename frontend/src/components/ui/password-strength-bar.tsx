import { scorePasswordStrength, type PasswordStrength } from "@/lib/password-strength";
import { cn } from "@/lib/utils";

const TIER_ORDER: PasswordStrength[] = ["weak", "medium", "strong"];

const TIER_COLOR: Record<PasswordStrength, string> = {
  weak: "bg-danger",
  medium: "bg-warning",
  strong: "bg-success",
};

const TIER_LABEL: Record<PasswordStrength, string> = {
  weak: "Weak",
  medium: "Medium",
  strong: "Strong",
};

export function PasswordStrengthBar({ password }: { password: string }) {
  if (!password) return null;
  const strength = scorePasswordStrength(password);
  const filledSegments = TIER_ORDER.indexOf(strength) + 1;

  return (
    <div className="flex flex-col gap-1">
      <div className="flex gap-1.5">
        {TIER_ORDER.map((tier, i) => (
          <div
            key={tier}
            className={cn(
              "h-1.5 flex-1 rounded-full transition-colors",
              i < filledSegments ? TIER_COLOR[strength] : "bg-secondary"
            )}
          />
        ))}
      </div>
      <p
        className={cn(
          "text-xs font-medium",
          strength === "weak" && "text-danger",
          strength === "medium" && "text-warning-foreground",
          strength === "strong" && "text-success"
        )}
      >
        {TIER_LABEL[strength]} password
      </p>
    </div>
  );
}
