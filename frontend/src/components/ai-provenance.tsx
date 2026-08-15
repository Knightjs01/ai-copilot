import { formatDistanceToNow } from "date-fns";

export function AiProvenance({
  modelUsed,
  generatedAt,
}: {
  modelUsed: string;
  generatedAt: string;
}) {
  return (
    <p className="text-xs text-muted-foreground">
      Generated {formatDistanceToNow(new Date(generatedAt), { addSuffix: true })} · {modelUsed}
    </p>
  );
}
