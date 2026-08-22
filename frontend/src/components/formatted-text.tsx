const BULLET_PREFIX = /^[-*•]\s+/;

interface Block {
  type: "paragraph" | "list";
  lines: string[];
}

function toBlocks(text: string): Block[] {
  const blocks: Block[] = [];
  // A blank line is a real paragraph break -- it must force a new block even when the line
  // before and after it are both plain (non-bullet) text, or two separate paragraphs would
  // silently merge into one.
  let sawBlankLine = false;

  for (const rawLine of text.split("\n")) {
    const line = rawLine.trim();
    if (!line) {
      sawBlankLine = true;
      continue;
    }

    const isBullet = BULLET_PREFIX.test(line);
    const content = isBullet ? line.replace(BULLET_PREFIX, "") : line;
    const kind: Block["type"] = isBullet ? "list" : "paragraph";
    const last = blocks[blocks.length - 1];

    if (last && last.type === kind && !sawBlankLine) {
      last.lines.push(content);
    } else {
      blocks.push({ type: kind, lines: [content] });
    }
    sawBlankLine = false;
  }
  return blocks;
}

// Renders free text extracted from an uploaded job description — plain paragraphs stay
// paragraphs, and lines that were originally bullet/numbered list items (marked "- " during
// extraction, see backend privacy_gateway/extraction.py) render as a real list instead of a flat
// wall of text with a literal "-"/"•" character sitting inline.
export function FormattedText({ text, className }: { text: string; className?: string }) {
  const blocks = toBlocks(text);
  return (
    <div className={className}>
      {blocks.map((block, i) =>
        block.type === "list" ? (
          <ul key={i} className="my-2 flex flex-col gap-1.5 first:mt-0 last:mb-0">
            {block.lines.map((line, j) => (
              <li key={j} className="flex items-start gap-2">
                <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-muted-foreground" />
                <span>{line}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p key={i} className="my-2 whitespace-pre-line first:mt-0 last:mb-0">
            {block.lines.join("\n")}
          </p>
        )
      )}
    </div>
  );
}
