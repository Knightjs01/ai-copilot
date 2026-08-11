import { CandidateAuthProvider } from "@/lib/candidate-auth-context";

export default function ShadowLayout({ children }: { children: React.ReactNode }) {
  return <CandidateAuthProvider>{children}</CandidateAuthProvider>;
}
