export type PasswordStrength = "weak" | "medium" | "strong";

// A small, dependency-free heuristic -- not a zxcvbn-style dictionary/entropy analyzer, just
// enough to stop "password1" from passing as strong. length>=8 is already the real server-side
// floor (see candidate_auth.schemas.CandidateSignupRequest); this only decides medium vs strong.
export function scorePasswordStrength(password: string): PasswordStrength {
  if (password.length < 8) return "weak";

  const classes = [
    /[a-z]/.test(password),
    /[A-Z]/.test(password),
    /[0-9]/.test(password),
    /[^a-zA-Z0-9]/.test(password),
  ].filter(Boolean).length;

  if (password.length >= 12 && classes >= 3) return "strong";
  if (password.length >= 8 && classes >= 2) return "medium";
  return "weak";
}
