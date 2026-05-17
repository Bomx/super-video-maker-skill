export type CaptionWord = {
  word: string;
  start: number;
  end: number;
};

export type CaptionLine = {
  words: CaptionWord[];
  /** Start = first word start, end = last word end */
  start: number;
  end: number;
};

export function buildCaptionLines(
  words: CaptionWord[],
  maxWordsPerLine: number,
  maxChars: number,
): CaptionLine[] {
  const lines: CaptionLine[] = [];
  let cur: CaptionWord[] = [];
  let chars = 0;

  const flush = () => {
    if (!cur.length) {
      return;
    }
    const start = cur[0].start;
    const end = cur[cur.length - 1].end;
    lines.push({ words: cur, start, end });
    cur = [];
    chars = 0;
  };

  for (const w of words) {
    const piece = w.word;
    const add = piece.length + (cur.length ? 1 : 0);
    if (
      cur.length > 0 &&
      (cur.length >= maxWordsPerLine || chars + add > maxChars)
    ) {
      flush();
    }
    cur.push(w);
    chars += add;
  }
  flush();
  return lines;
}

export function resolveVideoSrc(publicRelativePathOrUrl: string): string {
  if (
    publicRelativePathOrUrl.startsWith("http://") ||
    publicRelativePathOrUrl.startsWith("https://") ||
    publicRelativePathOrUrl.startsWith("file:")
  ) {
    return publicRelativePathOrUrl;
  }
  const trimmed = publicRelativePathOrUrl.replace(/^\/+/, "");
  // Remotion resolves static assets from the public folder
  return trimmed;
}
