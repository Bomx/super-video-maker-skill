import React, { useMemo } from "react";
import {
  AbsoluteFill,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Video,
} from "remotion";
import { z } from "zod";
import type { CaptionLine, CaptionWord } from "./captionLayout";
import { buildCaptionLines, resolveVideoSrc } from "./captionLayout";

export const captionedTalkingHeadSchema = z.object({
  durationInSeconds: z.number().positive(),
  /** Path under `public/` (e.g. `source/main.mp4`) OR https/file URL */
  mainVideoSrc: z.string(),
  words: z.array(
    z.object({
      word: z.string(),
      start: z.number(),
      end: z.number(),
    }),
  ),
  fps: z.number().default(30),
  width: z.number().default(1920),
  height: z.number().default(1080),
  accentHex: z.string().default("#FF6B2C"),
  maxWordsPerLine: z.number().default(8),
  maxCharsPerLine: z.number().default(46),
  bRollClips: z
    .array(
      z.object({
        src: z.string(),
        /** When this PiP appears on the main composition timeline (seconds). */
        startSec: z.number(),
        /** How long the PiP stays visible (seconds). */
        durationSec: z.number(),
        /** Trim into the B-roll file (seconds). Lets one long screen recording supply multiple windows. */
        srcStartSec: z.number().optional().default(0),
        xPct: z.number().default(70),
        yPct: z.number().default(5.5),
        widthPct: z.number().default(28),
        cornerRadiusPx: z.number().default(18),
        borderOpacity: z.number().default(0.35),
      }),
    )
    .default([]),
});

export type CaptionedTalkingHeadProps = z.infer<
  typeof captionedTalkingHeadSchema
>;

const FONT_STACK =
  '"SF Pro Display", "Avenir Next", "Plus Jakarta Sans", "Inter", system-ui, sans-serif';

function toAssetUrl(raw: string): string {
  const r = resolveVideoSrc(raw);
  if (
    r.startsWith("http://") ||
    r.startsWith("https://") ||
    r.startsWith("file:")
  ) {
    return r;
  }
  return staticFile(r);
}

function activeWordGlobalIndex(words: CaptionWord[], tSec: number): number {
  if (!words.length) {
    return -1;
  }
  if (tSec < words[0].start) {
    return 0;
  }
  for (let i = 0; i < words.length; i++) {
    const { start, end } = words[i];
    if (tSec >= start && tSec <= end + 1e-4) {
      return i;
    }
  }
  for (let i = 0; i < words.length - 1; i++) {
    if (tSec >= words[i].end && tSec < words[i + 1].start) {
      return i;
    }
  }
  return words.length - 1;
}

export const CaptionedTalkingHead: React.FC<CaptionedTalkingHeadProps> = ({
  mainVideoSrc,
  words,
  accentHex,
  maxWordsPerLine,
  maxCharsPerLine,
  bRollClips,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;

  const lines: CaptionLine[] = useMemo(
    () => buildCaptionLines(words, maxWordsPerLine, maxCharsPerLine),
    [words, maxWordsPerLine, maxCharsPerLine],
  );

  const gIdx = useMemo(
    () => (words.length ? activeWordGlobalIndex(words, t) : -1),
    [words, t],
  );

  const activeLineIdx = useMemo(() => {
    if (gIdx < 0 || !lines.length) {
      return 0;
    }
    let acc = 0;
    for (let li = 0; li < lines.length; li++) {
      const n = lines[li].words.length;
      if (gIdx < acc + n) {
        return li;
      }
      acc += n;
    }
    return lines.length - 1;
  }, [gIdx, lines]);

  const mainSrc = useMemo(() => toAssetUrl(mainVideoSrc), [mainVideoSrc]);

  const resolvedBrolls = useMemo(
    () =>
      bRollClips.map((c, i) => ({
        ...c,
        key: `broll-${i}`,
        resolvedSrc: toAssetUrl(c.src),
      })),
    [bRollClips],
  );

  const prevLineIdx = activeLineIdx > 0 ? activeLineIdx - 1 : null;
  const wordsBeforePrev =
    prevLineIdx !== null
      ? lines.slice(0, prevLineIdx).reduce((s, l) => s + l.words.length, 0)
      : 0;
  const wordsBeforeCur = lines
    .slice(0, activeLineIdx)
    .reduce((s, l) => s + l.words.length, 0);

  return (
    <AbsoluteFill style={{ backgroundColor: "#0a0a0a" }}>
      <AbsoluteFill>
        <Video
          src={mainSrc}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
          }}
          volume={1}
        />
      </AbsoluteFill>

      <AbsoluteFill
        style={{
          pointerEvents: "none",
          boxShadow: "inset 0 0 180px rgba(0,0,0,0.35)",
        }}
      />

      {resolvedBrolls.map((clip) => {
        const from = Math.round(clip.startSec * fps);
        const durationInFrames = Math.max(
          1,
          Math.round(clip.durationSec * fps),
        );
        if (frame < from || frame >= from + durationInFrames) {
          return null;
        }
        const wPx = (width * clip.widthPct) / 100;
        const xPx = (width * clip.xPct) / 100;
        const yPx = (height * clip.yPct) / 100;
        return (
          <AbsoluteFill
            key={clip.key}
            style={{ pointerEvents: "none" }}
          >
            <div
              style={{
                position: "absolute",
                left: xPx,
                top: yPx,
                width: wPx,
                aspectRatio: "16 / 9",
                borderRadius: clip.cornerRadiusPx,
                overflow: "hidden",
                boxShadow: `0 16px 48px rgba(0,0,0,0.45), 0 0 0 2px rgba(255,255,255,${clip.borderOpacity})`,
                background: "rgba(0,0,0,0.25)",
              }}
            >
              <Video
                src={clip.resolvedSrc}
                trimBefore={Math.max(
                  0,
                  Math.round((clip.srcStartSec ?? 0) * fps),
                )}
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
                volume={0}
              />
            </div>
          </AbsoluteFill>
        );
      })}

      <AbsoluteFill
        style={{
          pointerEvents: "none",
          justifyContent: "flex-end",
          alignItems: "center",
        }}
      >
        <div
          style={{
            position: "absolute",
            inset: 0,
            background:
              "linear-gradient(180deg, transparent 58%, rgba(0,0,0,0.62) 100%)",
            zIndex: 0,
          }}
        />

        <div
          style={{
            position: "relative",
            zIndex: 1,
            width: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            paddingBottom: height * 0.065,
            paddingLeft: width * 0.05,
            paddingRight: width * 0.05,
            gap: 14,
            maxWidth: Math.min(1180, width * 0.94),
            margin: "0 auto",
          }}
        >
          {prevLineIdx !== null && lines[prevLineIdx] ? (
            <CaptionLineRow
              line={lines[prevLineIdx]}
              globalWordStartIndex={wordsBeforePrev}
              activeGlobalIndex={gIdx}
              accentHex={accentHex}
              fps={fps}
              muted
            />
          ) : null}

          {lines[activeLineIdx] ? (
            <CaptionLineRow
              line={lines[activeLineIdx]}
              globalWordStartIndex={wordsBeforeCur}
              activeGlobalIndex={gIdx}
              accentHex={accentHex}
              fps={fps}
            />
          ) : null}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const CaptionLineRow: React.FC<{
  line: CaptionLine;
  globalWordStartIndex: number;
  activeGlobalIndex: number;
  accentHex: string;
  fps: number;
  muted?: boolean;
}> = ({
  line,
  globalWordStartIndex,
  activeGlobalIndex,
  accentHex,
  fps,
  muted,
}) => {
  const frame = useCurrentFrame();
  const { width } = useVideoConfig();
  const fontSizePrimary = Math.min(54, Math.round(width * 0.022));
  const fontSizeMuted = Math.min(44, Math.round(width * 0.017));
  return (
    <div
      style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        gap: muted ? 6 : 8,
        rowGap: muted ? 6 : 10,
        opacity: muted ? 0.42 : 1,
        transform: muted ? "scale(0.9)" : "scale(1)",
      }}
    >
      {line.words.map((w, wi) => {
        const g = globalWordStartIndex + wi;
        const isActive = g === activeGlobalIndex;
        const startF = Math.floor(w.start * fps);
        const pop = spring({
          fps,
          frame: frame - startF,
          config: { damping: 18, stiffness: 220, mass: 0.45 },
        });
        const scale = isActive ? 0.92 + pop * 0.12 : 1;
        const raw = w.word;
        return (
          <span
            key={`${g}-${wi}-${raw}`}
            style={{
              display: "inline-block",
              transform: `scale(${scale})`,
              fontFamily: FONT_STACK,
              fontWeight: isActive ? 800 : 600,
              fontSize: muted ? fontSizeMuted : fontSizePrimary,
              lineHeight: 1.22,
              letterSpacing: -0.03,
              color: isActive ? "#ffffff" : "rgba(255,255,255,0.9)",
              backgroundColor: isActive ? accentHex : "rgba(16,16,20,0.58)",
              padding: isActive ? "10px 16px" : "8px 13px",
              borderRadius: 14,
              boxShadow: isActive
                ? `0 10px 32px ${accentHex}60, 0 2px 10px rgba(0,0,0,0.4)`
                : "0 4px 18px rgba(0,0,0,0.3)",
              border: isActive
                ? "1px solid rgba(255,255,255,0.32)"
                : "1px solid rgba(255,255,255,0.14)",
            }}
          >
            {raw}
          </span>
        );
      })}
    </div>
  );
};
