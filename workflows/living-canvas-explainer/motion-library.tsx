/**
 * living-canvas motion library — battle-tested helpers + components for the
 * Living Canvas Product Explainer recipe (see LIVING_CANVAS_PLAYBOOK.md).
 *
 * Extracted verbatim from a shipped production composition. Adapt the C
 * (colors) and FONT constants to the client brand; everything else is
 * brand-agnostic. Requires: remotion ^4, @remotion/fonts, local TTFs in
 * public/fonts/ registered via a fonts.ts module.
 *
 * Contents: spr, actor, settle, slotAt, camRig (+creep+velocity blur),
 * shakeAt, rnd, typeOn, Grid, GhostTitle, WordPop (pov/scatter/strike),
 * Card, Skel, XChip, CheckPill (pendulum), SharpTag, Cursor, Sparks,
 * RingPulse, GlowSweep, Embers, HeatFlare, Flash, GloveHand, Ambient,
 * Streaks, EngineTile, grainy-logo pattern.
 */

import React from "react";
import { AbsoluteFill, interpolate, spring, useCurrentFrame } from "remotion";
import "./fonts";

/**
 * Distribb launch video: "The First SEO AI Agent for Buy Intent SEO"
 * 1920x1080 @ 30fps, 1440 frames (~48s). 1600.agency-style single flat
 * actor timeline: continuous canvas, element-level pacing, 2 hard cuts.
 * Timings are beat-locked to voiceover word timestamps (vo_words.json).
 */

const FPS = 30;
const W = 1920;
const H = 1080;

const CLAMP = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const C = {
  light: "#F5F5F5",
  dark: "#101012",
  ink: "#111111",
  paper: "#FFFFFF",
  soft: "#6A6A6A",
  subtle: "#9A9A9A",
  line: "rgba(17,17,17,0.08)",
  orange: "#E11D2A",
  orangeSoft: "rgba(225,29,42,0.14)",
  orangeGlow: "rgba(225,29,42,0.30)",
  red: "#E11D2A",
  redSoft: "rgba(229,72,77,0.12)",
  green: "#1FA355",
  cardShadow:
    "0 24px 80px rgba(17,17,17,0.10), 0 6px 24px rgba(17,17,17,0.07)",
  darkText: "#F4F4F5",
  darkSoft: "rgba(244,244,245,0.55)",
};

const FONT =
  '"Satoshi", "Avenir Next", "SF Pro Display", "Plus Jakarta Sans", "Inter", sans-serif';
const MONO =
  '"SF Mono", "JetBrains Mono", "Roboto Mono", ui-monospace, monospace';

/** Sharp Tag: split-cell data badge (3px radius, no glow) — the anti-pill */
const SharpTag: React.FC<{
  label: string;
  value: string | number;
  active: boolean;
  scale?: number;
}> = ({ label, value, active, scale = 1 }) => (
  <span
    style={{
      display: "inline-flex",
      alignItems: "stretch",
      borderRadius: 3,
      overflow: "hidden",
      border: `1.5px solid ${active ? "#E11D2A" : "rgba(17,17,17,0.20)"}`,
      transform: `scale(${scale})`,
    }}
  >
    <span
      style={{
        padding: "6px 11px",
        background: active ? "#E11D2A" : "transparent",
        color: active ? "#fff" : "#9A9A9A",
        fontFamily: FONT,
        fontWeight: 700,
        fontSize: 15,
        letterSpacing: "0.12em",
        display: "flex",
        alignItems: "center",
      }}
    >
      {label}
    </span>
    <span
      style={{
        padding: "6px 13px",
        fontFamily: MONO,
        fontWeight: 700,
        fontSize: 22,
        color: active ? "#111111" : "#9A9A9A",
        fontVariantNumeric: "tabular-nums",
        display: "flex",
        alignItems: "center",
        background: "#FFFFFF",
      }}
    >
      {value}
    </span>
  </span>
);

/* ---------------- motion helpers ---------------- */

const spr = (
  frame: number,
  start: number,
  damping = 11,
  stiffness = 210,
): number =>
  spring({
    fps: FPS,
    frame: Math.max(0, frame - start),
    config: { damping, stiffness, mass: 1 },
  });

type Actor = {
  visible: boolean;
  opacity: number;
  enter: number;
  exit: number;
  local: number;
};

/** Spring enter, directional-blur-friendly linear exit. */
const actor = (
  frame: number,
  enterAt: number,
  exitAt: number,
  exitDur = 10,
): Actor => {
  const enter = spr(frame, enterAt);
  const exit = interpolate(frame, [exitAt - exitDur, exitAt], [0, 1], CLAMP);
  return {
    visible: frame >= enterAt - 1 && frame <= exitAt,
    opacity: enter * (1 - exit),
    enter,
    exit,
    local: frame - enterAt,
  };
};

const wordAt = (t: number) => Math.round(t * FPS);

/** deterministic pseudo-random in [0,1) */
const rnd = (seed: number) => {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

const typeOn = (text: string, local: number, cps = 0.55) =>
  text.slice(0, Math.max(0, Math.floor(local * cps)));

/** micro-bounce settle factor applied after an element lands */
const settle = (local: number, from = 8) =>
  local > from
    ? 1 + Math.exp(-(local - from) / 7) * Math.sin((local - from) / 1.9) * 0.035
    : 1;

/** animated list-slot position: rows physically re-sort as better ones arrive (Blitz shuffle) */
const slotAt = (frame: number, sched: { f: number; slot: number }[]) => {
  let s = sched[0].slot;
  for (let i = 1; i < sched.length; i++) {
    if (frame < sched[i].f) break;
    const p = spr(frame, sched[i].f, 13, 200);
    s += (sched[i].slot - s) * p;
  }
  return s;
};

/** section camera rig: keys say where the camera CENTER aims (scene coords) and zoom.
 *  Each key fires a spring move when its frame is reached; moves chain smoothly. */
type CamKey = { f: number; x: number; y: number; s: number };

const camStateAt = (fr: number, keys: CamKey[]) => {
  let x = keys[0].x;
  let y = keys[0].y;
  let s = keys[0].s;
  let lastF = keys[0].f;
  for (let i = 1; i < keys.length; i++) {
    if (fr < keys[i].f) break;
    /* stiff spring: punches complete in ~0.3s like the reference footage */
    const p = spring({
      fps: FPS,
      frame: Math.max(0, fr - keys[i].f),
      config: { damping: 16, stiffness: 250, mass: 1 },
    });
    x += (keys[i].x - x) * p;
    y += (keys[i].y - y) * p;
    s += (keys[i].s - s) * p;
    lastF = keys[i].f;
  }
  /* always-on creep zoom during holds (~4%/s, capped +9%) — the frame is never static */
  const creep = Math.min(0.09, Math.max(0, fr - lastF - 10) * 0.00135);
  return { x, y, s: s * (1 + creep) };
};

const camRig = (frame: number, keys: CamKey[]) => {
  const a = camStateAt(frame, keys);
  const b = camStateAt(frame - 1, keys);
  const vel = Math.hypot(a.x - b.x, a.y - b.y) + Math.abs(a.s - b.s) * 280;
  return {
    ...a,
    blur: vel > 3.5 ? Math.min(8, (vel - 3.5) * 0.28) : 0,
    style: {
      transformOrigin: "center",
      transform: `scale(${a.s}) translate(${W / 2 - a.x}px, ${H / 2 - a.y}px)`,
    } as React.CSSProperties,
  };
};

/** expanding highlight ring at a scene point (fires once) */
const RingPulse: React.FC<{
  x: number;
  y: number;
  start: number;
  frame: number;
  color?: string;
  size?: number;
}> = ({ x, y, start, frame, color = C.orange, size = 150 }) => {
  const l = frame - start;
  if (l < 0 || l > 22) return null;
  const p = interpolate(l, [0, 22], [0, 1], CLAMP);
  const e = 1 - (1 - p) * (1 - p);
  return (
    <div
      style={{
        position: "absolute",
        left: x - (size * e) / 2,
        top: y - (size * e) / 2,
        width: size * e,
        height: size * e,
        borderRadius: "50%",
        border: `${4 - p * 2.5}px solid ${color}`,
        opacity: (1 - p) * 0.9,
        zIndex: 65,
      }}
    />
  );
};

/** diagonal light sweep across a persistent card (fires once) */
const GlowSweep: React.FC<{
  start: number;
  frame: number;
  w: number;
  h: number;
}> = ({ start, frame, w, h }) => {
  const l = frame - start;
  if (l < 0 || l > 18) return null;
  const p = interpolate(l, [0, 18], [0, 1], CLAMP);
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        width: w,
        height: h,
        overflow: "hidden",
        borderRadius: 22,
        pointerEvents: "none",
        zIndex: 60,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: -h * 0.3,
          left: -w * 0.45 + p * w * 1.5,
          width: w * 0.36,
          height: h * 1.6,
          transform: "rotate(14deg)",
          background:
            "linear-gradient(90deg, transparent, rgba(255,255,255,0.75), transparent)",
          opacity: 0.85 * (1 - Math.abs(p - 0.5) * 0.6),
        }}
      />
    </div>
  );
};

/** rising ember particles for dark-world payoff beats */
const Embers: React.FC<{
  frame: number;
  start: number;
  end: number;
  cx: number;
  cy: number;
  spread?: number;
}> = ({ frame, start, end, cx, cy, spread = 420 }) => {
  if (frame < start || frame > end) return null;
  const fade =
    interpolate(frame, [start, start + 10], [0, 1], CLAMP) *
    interpolate(frame, [end - 12, end], [1, 0], CLAMP);
  return (
    <div style={{ position: "absolute", zIndex: 55, pointerEvents: "none" }}>
      {Array.from({ length: 16 }).map((_, i) => {
        const cycle = 34 + rnd(i + 3) * 26;
        const l = (frame - start + rnd(i) * cycle) % cycle;
        const rise = l / cycle;
        const px = cx + (rnd(i + 11) - 0.5) * spread + Math.sin((frame + i * 29) / 9) * 14;
        const py = cy - rise * (170 + rnd(i + 7) * 130);
        const sz = 3 + rnd(i + 19) * 5;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: px,
              top: py,
              width: sz,
              height: sz,
              borderRadius: "50%",
              background: rnd(i + 5) > 0.4 ? C.orange : "#FF7A45",
              opacity: fade * (1 - rise) * (0.35 + rnd(i + 31) * 0.5),
              filter: "blur(0.6px)",
            }}
          />
        );
      })}
    </div>
  );
};

/** flame licks + heat glow over a highlighted row (gojiberry-style payoff fire) */
const HeatFlare: React.FC<{
  x: number;
  y: number;
  start: number;
  end: number;
  frame: number;
  w?: number;
}> = ({ x, y, start, end, frame, w = 280 }) => {
  if (frame < start || frame > end) return null;
  const life =
    interpolate(frame, [start, start + 8], [0, 1], CLAMP) *
    interpolate(frame, [end - 10, end], [1, 0], CLAMP);
  return (
    <div
      style={{
        position: "absolute",
        left: x - w / 2,
        top: y - 92,
        width: w,
        height: 130,
        zIndex: 58,
        pointerEvents: "none",
      }}
    >
      {[0, 1, 2, 3, 4, 5].map((i) => {
        const flick = 0.7 + rnd(Math.floor(frame * 0.8) * 2.3 + i * 7) * 0.6;
        const hx = (i / 5) * (w - 30) + (rnd(i + Math.floor(frame * 0.6)) - 0.5) * 10;
        const hh = (44 + rnd(i + 9) * 40) * flick * life;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: hx,
              bottom: 28,
              width: 30,
              height: hh,
              borderRadius: "50% 50% 46% 46% / 70% 70% 28% 28%",
              background:
                "linear-gradient(180deg, rgba(255,190,80,0) 0%, #FF9A2E 38%, #E11D2A 82%)",
              filter: "blur(6px)",
              opacity: 0.55 * life,
              transform: `scaleX(${0.75 + rnd(i + Math.floor(frame * 0.7)) * 0.4})`,
            }}
          />
        );
      })}
      <div
        style={{
          position: "absolute",
          inset: -10,
          background: `radial-gradient(ellipse at 50% 72%, rgba(225,29,42,${
            0.3 * life
          }) 0%, transparent 62%)`,
          filter: "blur(12px)",
        }}
      />
    </div>
  );
};

/** cartoon glove hand (the narrative actor for transformation chains) */
const GloveHand: React.FC<{
  x: number;
  y: number;
  opacity: number;
  blur?: number;
  rot?: number;
}> = ({ x, y, opacity, blur = 0, rot = 0 }) => {
  if (opacity <= 0.01) return null;
  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        opacity,
        transform: `translate(-50%,-50%) rotate(${rot}deg)`,
        filter: blur > 0.3 ? `blur(${blur}px)` : undefined,
        zIndex: 72,
      }}
    >
      <svg width="76" height="76" viewBox="0 0 64 64">
        <path
          d="M8 30 Q6 22 14 20 L34 16 Q40 15 41 20 L42 24 L53 21 Q59 20 59 25 Q59 29 54 30 L43 33 L45 40 Q46 46 40 47 L20 50 Q10 51 8 42 Z"
          fill="#fff"
          stroke="#111"
          strokeWidth="3.4"
          strokeLinejoin="round"
        />
        <path
          d="M34 24 L44 23 M35 31 L45 30 M33 39 L42 38"
          stroke="#111"
          strokeWidth="2.4"
          strokeLinecap="round"
        />
      </svg>
    </div>
  );
};

/** white-hot burst flash: pre-glow build, then bloom-out */
const Flash: React.FC<{
  start: number;
  frame: number;
  cx: number;
  cy: number;
}> = ({ start, frame, cx, cy }) => {
  const l = frame - start;
  if (l < -6 || l > 11) return null;
  const grow = interpolate(l, [-6, 0], [0.25, 1], CLAMP);
  const fade = interpolate(l, [0, 11], [1, 0], CLAMP);
  const r = 260 + grow * 420 + Math.max(0, l) * 90;
  return (
    <div
      style={{
        position: "absolute",
        left: cx - r,
        top: cy - r,
        width: r * 2,
        height: r * 2,
        borderRadius: "50%",
        background: `radial-gradient(circle, rgba(255,255,255,${
          0.95 * fade * grow
        }) 0%, rgba(255,255,255,${0.45 * fade * grow}) 32%, transparent 68%)`,
        zIndex: 75,
        pointerEvents: "none",
      }}
    />
  );
};

/** decaying camera shake burst */
const shakeAt = (frame: number, start: number, dur = 8, amp = 6) => {
  const l = frame - start;
  if (l < 0 || l > dur) return { x: 0, y: 0 };
  const d = 1 - l / dur;
  return {
    x: (rnd(frame * 3.7 + 1) - 0.5) * 2 * amp * d,
    y: (rnd(frame * 7.1 + 13) - 0.5) * 2 * amp * d,
  };
};

/* ---------------- timeline (beat-locked to VO) ---------------- */

const T = {
  // HOOK (dark) "Most SEO traffic never buys a thing." 0-2.66s
  hook: { enter: 0, exit: 80 },
  hookCard: { enter: 38, exit: 90 },
  // PROBLEM (light) "Blog posts. Pageviews. Zero pipeline." 2.66-5.66s
  problem: { enter: 80, exit: 170 },
  probChip1: { enter: wordAt(2.66), exit: 170 },
  probChip2: { enter: wordAt(3.7), exit: 170 },
  probChip3: { enter: wordAt(4.7), exit: 170 },
  // DARK TURN (hard cut) "That's not growth, that's noise." 5.66-8.16s
  turn: { enter: 170, exit: 245 },
  turnLine1: { enter: wordAt(5.66), exit: 245 },
  turnLine2: { enter: wordAt(6.78), exit: 245 },
  // REVEAL (light) "Meet Distribb..." 8.16-13.04s
  reveal: { enter: 245, exit: 398 },
  revealLogo: { enter: wordAt(8.5), exit: 398 },
  revealBadge: { enter: wordAt(9.34), exit: 398 },
  revealTag: { enter: wordAt(11.42), exit: 398 },
  // F1 KEYWORDS 13.24-17.08s
  f1: { enter: 390, exit: 520 },
  f1Row0: { enter: 410, exit: 520 },
  f1Row1: { enter: 422, exit: 520 },
  f1Row2: { enter: 434, exit: 520 },
  f1Row3: { enter: 446, exit: 520 },
  f1Ready: { enter: wordAt(15.9), exit: 520 },
  // F2 CONTENT 17.1-20.14s
  f2: { enter: 513, exit: 616 },
  f2Rank: { enter: 555, exit: 616 },
  f2One: { enter: wordAt(19.3), exit: 616 },
  // F3 PUBLISH 20.3-22.54s
  f3: { enter: 609, exit: 695 },
  f3Chips: { enter: 622, exit: 695 },
  f3Cal: { enter: 646, exit: 695 },
  // F4 BACKLINKS 22.98-25.58s
  f4: { enter: 689, exit: 780 },
  f4Row0: { enter: 698, exit: 780 },
  f4Row1: { enter: 710, exit: 780 },
  f4Row2: { enter: 722, exit: 780 },
  f4Av: { enter: wordAt(25.0), exit: 780 },
  // AI ANSWER (dark, hard cut) 26.22-31.14s
  ai: { enter: 778, exit: 933 },
  aiQ: { enter: 781, exit: 933 },
  aiA: { enter: 838, exit: 933 },
  aiChips: { enter: wordAt(26.44), exit: 933 },
  aiAnswerLine: { enter: wordAt(29.0), exit: 933 },
  // PROOF (light) "Buyers in, deals out, on autopilot" 31.14-34.02s
  proof: { enter: 934, exit: 1028 },
  proofP1: { enter: wordAt(31.14), exit: 1028 },
  proofP2: { enter: wordAt(31.8), exit: 1028 },
  proofSlam: { enter: wordAt(32.82), exit: 1028 },
  // CTA 34.02s-end
  cta: { enter: 1021, exit: 1290 },
  ctaLogo: { enter: 1021, exit: 1290 },
  ctaPill1: { enter: wordAt(35.1), exit: 1290 },
  ctaPill2: { enter: wordAt(36.5), exit: 1290 },
  ctaBtn: { enter: wordAt(37.9), exit: 1290 },
  ctaUrl: { enter: wordAt(38.66), exit: 1290 },
  ctaMicro: { enter: 1216, exit: 1290 },
};

/* background world: 1 = light, 0 = dark */
const lightAmount = (f: number): number => {
  if (f < 170) return 1; // story cold-open lives in the light world
  if (f < 245) return 0; // TURN: hard cut to dark
  if (f < 398) return interpolate(f, [245, 263], [0, 1], CLAMP); // reveal morph to light
  if (f < 779) return 1; // features light
  if (f < 934) return 0; // AI: hard cut to dark
  return interpolate(f, [934, 951], [0, 1], CLAMP); // proof morph to light
};

/* ---------------- tiny building blocks ---------------- */

const Grid: React.FC<{ dark?: boolean; frame: number }> = ({ dark, frame }) => (
  <div
    style={{
      position: "absolute",
      inset: -80,
      backgroundImage: `linear-gradient(${
        dark ? "rgba(255,255,255,0.035)" : "rgba(17,17,17,0.028)"
      } 1px, transparent 1px), linear-gradient(90deg, ${
        dark ? "rgba(255,255,255,0.035)" : "rgba(17,17,17,0.028)"
      } 1px, transparent 1px)`,
      backgroundSize: "44px 44px",
      transform: `translate(${(frame * 0.06) % 44}px, ${
        (frame * 0.03) % 44
      }px)`,
    }}
  />
);

const GhostTitle: React.FC<{
  text: string;
  frame: number;
  a: Actor;
  dark?: boolean;
}> = ({ text, frame, a, dark }) => (
  <div
    style={{
      position: "absolute",
      width: "100%",
      textAlign: "center",
      top: H / 2 - 190,
      fontFamily: FONT,
      fontWeight: 900,
      fontSize: 330,
      letterSpacing: "-0.05em",
      color: dark ? "rgba(255,255,255,0.05)" : "rgba(17,17,17,0.045)",
      opacity: a.opacity,
      transform: `scale(${1 + frame * 0.0004}) translateY(${
        (1 - a.enter) * 40
      }px)`,
      whiteSpace: "nowrap",
    }}
  >
    {text}
  </div>
);

/** headline word: spring pop with decaying blur + micro-bounce; optional accent.
 *  pov mode: words fly from the viewer (big + blurred) onto position. */
const WordPop: React.FC<{
  words: { t: string; accent?: boolean; at: number; strike?: number }[];
  frame: number;
  size?: number;
  dark?: boolean;
  exitAt?: number;
  exitDir?: 1 | -1;
  pov?: boolean;
  exitScatter?: boolean;
}> = ({
  words,
  frame,
  size = 84,
  dark,
  exitAt = 999999,
  exitDir = 1,
  pov,
  exitScatter,
}) => {
  const exit = interpolate(frame, [exitAt - 10, exitAt], [0, 1], CLAMP);
  return (
    <div
      style={{
        display: "flex",
        gap: size * 0.28,
        justifyContent: "center",
        flexWrap: "wrap",
        transform: exitScatter
          ? undefined
          : `translateX(${exit * exit * 180 * exitDir}px)`,
        filter: `blur(${exit * (exitScatter ? 8 : 14)}px)`,
        opacity: 1 - exit,
      }}
    >
      {words.map((w, i) => {
        const p = spr(frame, w.at, 10.5, 230);
        const rot = (rnd(i + 17) - 0.5) * 9 * (1 - p);
        const base = pov
          ? interpolate(p, [0, 1], [2.05, 1], CLAMP)
          : 0.82 + p * 0.18;
        /* scatter exit: words fly apart radially like debris */
        const scX = exitScatter ? exit * exit * (rnd(i * 3 + 1) - 0.5) * 940 : 0;
        const scY = exitScatter ? exit * exit * (rnd(i * 7 + 2) - 0.5) * 660 : 0;
        const scR = exitScatter ? exit * (rnd(i + 13) - 0.5) * 80 : 0;
        const struckP = w.strike
          ? interpolate(frame, [w.strike, w.strike + 6], [0, 1], CLAMP)
          : 0;
        return (
          <span
            key={i}
            style={{
              fontFamily: FONT,
              fontWeight: 900,
              fontSize: size,
              letterSpacing: "-0.045em",
              lineHeight: 1.04,
              position: "relative",
              color:
                struckP > 0.6
                  ? C.subtle
                  : w.accent
                    ? C.orange
                    : dark
                      ? C.darkText
                      : C.ink,
              opacity: Math.min(1, p * (pov ? 1.7 : 1.4)),
              display: "inline-block",
              transform: `translate(${scX}px, ${
                (1 - p) * size * (pov ? 0.1 : 0.5) + scY
              }px) scale(${base * settle(frame - w.at)}) rotate(${
                rot + scR
              }deg)`,
              filter: `blur(${(1 - p) * (pov ? 18 : 8)}px)`,
              textShadow: w.accent
                ? `0 6px 40px ${C.orangeGlow}`
                : undefined,
            }}
          >
            {w.t}
            {w.strike && frame >= w.strike ? (
              <span
                style={{
                  position: "absolute",
                  left: "-4%",
                  top: "52%",
                  width: "108%",
                  height: Math.max(5, size * 0.09),
                  background: C.orange,
                  borderRadius: 4,
                  transform: `scaleX(${struckP})`,
                  transformOrigin: "left center",
                }}
              />
            ) : null}
          </span>
        );
      })}
    </div>
  );
};

const Card: React.FC<{
  style?: React.CSSProperties;
  children?: React.ReactNode;
}> = ({ style, children }) => (
  <div
    style={{
      background: C.paper,
      borderRadius: 22,
      boxShadow: C.cardShadow,
      border: `1px solid ${C.line}`,
      ...style,
    }}
  >
    {children}
  </div>
);

const Skel: React.FC<{ w: number; h?: number; style?: React.CSSProperties }> = ({
  w,
  h = 12,
  style,
}) => (
  <div
    style={{
      width: w,
      height: h,
      borderRadius: 999,
      background: "rgba(17,17,17,0.09)",
      ...style,
    }}
  />
);

const XChip: React.FC<{ label: string; a: Actor }> = ({ label, a }) => (
  <div
    style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 10,
      padding: "12px 20px",
      borderRadius: 999,
      background: C.paper,
      border: `2px solid ${C.red}`,
      boxShadow: C.cardShadow,
      opacity: a.opacity,
      transform: `scale(${(0.7 + a.enter * 0.3) * settle(a.local)}) rotate(${
        (1 - a.enter) * -6
      }deg)`,
    }}
  >
    <svg width="18" height="18" viewBox="0 0 18 18">
      <path
        d="M4 4 L14 14 M14 4 L4 14"
        stroke={C.red}
        strokeWidth="3.4"
        strokeLinecap="round"
      />
    </svg>
    <span
      style={{
        fontFamily: FONT,
        fontWeight: 700,
        fontSize: 24,
        letterSpacing: "-0.02em",
        color: C.ink,
      }}
    >
      {label}
    </span>
  </div>
);

const CheckPill: React.FC<{
  label: string;
  a: Actor;
  size?: number;
}> = ({ label, a, size = 30 }) => (
  <div
    style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 12,
      padding: `${size * 0.45}px ${size * 0.85}px`,
      borderRadius: 999,
      background: C.paper,
      border: `1px solid ${C.line}`,
      boxShadow: C.cardShadow,
      opacity: a.opacity,
      transformOrigin: "50% -16px",
      transform: `translateY(${(1 - a.enter) * 26}px) scale(${
        (0.85 + a.enter * 0.15) * settle(a.local)
      }) rotate(${
        a.local > 0 ? Math.exp(-a.local / 11) * Math.sin(a.local / 2.6) * 6 : 0
      }deg)`,
    }}
  >
    <div
      style={{
        width: size,
        height: size,
        borderRadius: 9,
        background: C.orange,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxShadow: `0 4px 14px ${C.orangeGlow}`,
      }}
    >
      <svg width={size * 0.55} height={size * 0.55} viewBox="0 0 16 16">
        <path
          d="M2.5 8.5 L6.5 12 L13.5 4"
          stroke="#fff"
          strokeWidth="2.6"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
    <span
      style={{
        fontFamily: FONT,
        fontWeight: 700,
        fontSize: size * 0.9,
        letterSpacing: "-0.02em",
        color: C.ink,
      }}
    >
      {label}
    </span>
  </div>
);

const Cursor: React.FC<{ x: number; y: number; press?: number }> = ({
  x,
  y,
  press = 0,
}) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      zIndex: 80,
      transform: `scale(${1 - press * 0.12})`,
    }}
  >
    {press > 0.3 ? (
      <div
        style={{
          position: "absolute",
          left: -18,
          top: -16,
          width: 64,
          height: 64,
          borderRadius: "50%",
          border: `3px solid ${C.orange}`,
          opacity: 1 - press,
          transform: `scale(${0.5 + press * 1.1})`,
        }}
      />
    ) : null}
    <svg width="52" height="62" viewBox="0 0 52 62">
      <path
        d="M6 3 L6 47 L19 36 L26 58 L35 54 L27 34 L44 34 Z"
        fill={C.ink}
        stroke="#fff"
        strokeWidth="3"
        strokeLinejoin="round"
        style={{ filter: "drop-shadow(0 8px 16px rgba(17,17,17,0.3))" }}
      />
    </svg>
  </div>
);

/** radial spark burst */
const Sparks: React.FC<{
  cx: number;
  cy: number;
  start: number;
  frame: number;
  n?: number;
  dist?: number;
  color?: string;
}> = ({ cx, cy, start, frame, n = 12, dist = 130, color = C.orange }) => {
  const local = frame - start;
  if (local < 0 || local > 26) return null;
  const p = interpolate(local, [0, 26], [0, 1], CLAMP);
  const ease = 1 - (1 - p) * (1 - p);
  return (
    <div style={{ position: "absolute", left: cx, top: cy, zIndex: 70 }}>
      {Array.from({ length: n }).map((_, i) => {
        const ang = (i / n) * Math.PI * 2 + rnd(i) * 0.5;
        const d = dist * (0.6 + rnd(i + 40) * 0.7) * ease;
        const s = 5 + rnd(i + 9) * 7;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: Math.cos(ang) * d,
              top: Math.sin(ang) * d,
              width: s,
              height: s,
              borderRadius: rnd(i + 3) > 0.5 ? "50%" : 2,
              background: color,
              opacity: (1 - p) * 0.95,
              transform: `scale(${1 - p * 0.5}) rotate(${p * 180}deg)`,
            }}
          />
        );
      })}
    </div>
  );
};

/** real brand marks */
const GoogleG: React.FC = () => (
  <svg width="46" height="46" viewBox="0 0 24 24">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4" />
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
  </svg>
);

const ChatGPTKnot: React.FC = () => (
  <svg width="52" height="52" viewBox="0 0 2406 2406">
    <path
      id="cgpt-blade"
      d="M1107.3 299.1c-197.999 0-373.9 127.3-435.2 315.3L650 743.5v427.9c0 21.4 11 40.4 29.4 51.4l344.5 198.515V833.3h.1v-27.9L1372.7 604c33.715-19.52 70.44-32.857 108.47-39.828L1447.6 450.3C1361 353.5 1237.1 298.5 1107.3 299.1zm0 117.5-.6.6c79.699 0 156.3 27.5 217.6 78.4-2.5 1.2-7.4 4.3-11 6.1L952.8 709.3c-18.4 10.4-29.4 30-29.4 51.4V1248l-155.1-89.4V755.8c-.1-187.099 151.601-338.9 339-339.2z"
      fill="#fff"
    />
    <use href="#cgpt-blade" transform="rotate(60 1203 1203)" />
    <use href="#cgpt-blade" transform="rotate(120 1203 1203)" />
    <use href="#cgpt-blade" transform="rotate(180 1203 1203)" />
    <use href="#cgpt-blade" transform="rotate(240 1203 1203)" />
    <use href="#cgpt-blade" transform="rotate(300 1203 1203)" />
  </svg>
);

const ClaudeMark: React.FC = () => (
  <svg width="44" height="44" viewBox="0 0 24 24">
    <path fill="#D97757" d="m4.7144 15.9555 4.7174-2.6471.079-.2307-.079-.1275h-.2307l-.7893-.0486-2.6956-.0729-2.3375-.0971-2.2646-.1214-.5707-.1215-.5343-.7042.0546-.3522.4797-.3218.686.0608 1.5179.1032 2.2767.1578 1.6514.0972 2.4468.255h.3886l.0546-.1579-.1336-.0971-.1032-.0972L6.973 9.8356l-2.55-1.6879-1.3356-.9714-.7225-.4918-.3643-.4614-.1578-1.0078.6557-.7225.8803.0607.2246.0607.8925.686 1.9064 1.4754 2.4893 1.8336.3643.3035.1457-.1032.0182-.0728-.164-.2733-1.3539-2.4467-1.445-2.4893-.6435-1.032-.17-.6194c-.0607-.255-.1032-.4674-.1032-.7285L6.287.1335 6.6997 0l.9957.1336.419.3642.6192 1.4147 1.0018 2.2282 1.5543 3.0296.4553.8985.2429.8318.091.255h.1579v-.1457l.1275-1.706.2368-2.0947.2307-2.6957.0789-.7589.3764-.9107.7468-.4918.5828.2793.4797.686-.0668.4433-.2853 1.8517-.5586 2.9021-.3643 1.9429h.2125l.2429-.2429.9835-1.3053 1.6514-2.0643.7286-.8196.85-.9046.5464-.4311h1.0321l.759 1.1293-.34 1.1657-1.0625 1.3478-.8804 1.1414-1.2628 1.7-.7893 1.36.0729.1093.1882-.0183 2.8535-.607 1.5421-.2794 1.8396-.3157.8318.3886.091.3946-.3278.8075-1.967.4857-2.3072.4614-3.4364.8136-.0425.0304.0486.0607 1.5482.1457.6618.0364h1.621l3.0175.2247.7892.522.4736.6376-.079.4857-1.2142.6193-1.6393-.3886-3.825-.9107-1.3113-.3279h-.1822v.1093l1.0929 1.0686 2.0035 1.8092 2.5075 2.3314.1275.5768-.3218.4554-.34-.0486-2.2039-1.6575-.85-.7468-1.9246-1.621h-.1275v.17l.4432.6496 2.3436 3.5214.1214 1.0807-.17.3521-.6071.2125-.6679-.1214-1.3721-1.9246L14.38 17.959l-1.1414-1.9428-.1397.079-.674 7.2552-.3156.3703-.7286.2793-.6071-.4614-.3218-.7468.3218-1.4753.3886-1.9246.3157-1.53.2853-1.9004.17-.6314-.0121-.0425-.1397.0182-1.4328 1.9672-2.1796 2.9446-1.7243 1.8456-.4128.164-.7164-.3704.0667-.6618.4008-.5889 2.386-3.0357 1.4389-1.882.929-1.0868-.0062-.1579h-.0546l-6.3385 4.1164-1.1293.1457-.4857-.4554.0608-.7467.2307-.2429 1.9064-1.3114Z" />
  </svg>
);

const PerplexityMark: React.FC = () => (
  <svg width="42" height="42" viewBox="0 0 24 24">
    <path fill="#20808D" d="M22.3977 7.0896h-2.3106V.0676l-7.5094 6.3542V.1577h-1.1554v6.1966L4.4904 0v7.0896H1.6023v10.3976h2.8882V24l6.932-6.3591v6.2005h1.1554v-6.0469l6.9318 6.1807v-6.4879h2.8882V7.0896zm-3.4657-4.531v4.531h-5.355l5.355-4.531zm-13.2862.0676 4.8691 4.4634H5.6458V2.6262zM2.7576 16.332V8.245h7.8476l-6.1149 6.1147v1.9723H2.7576zm2.8882 5.0404v-3.8852h.0001v-2.6488l5.7763-5.7764v7.0111l-5.7764 5.2993zm12.7086.0248-5.7766-5.1509V9.0618l5.7766 5.7766v6.5588zm2.8882-5.0652h-1.733v-1.9723L13.3948 8.245h7.8478v8.087z" />
  </svg>
);

const GeminiMark: React.FC = () => (
  <svg width="44" height="44" viewBox="0 0 24 24">
    <defs>
      <linearGradient id="gemini-grad" x1="0%" y1="100%" x2="100%" y2="0%">
        <stop offset="0%" stopColor="#4285F4" />
        <stop offset="55%" stopColor="#9B72CB" />
        <stop offset="100%" stopColor="#D96570" />
      </linearGradient>
    </defs>
    <path fill="url(#gemini-grad)" d="M11.04 19.32Q12 21.51 12 24q0-2.49.93-4.68.96-2.19 2.58-3.81t3.81-2.55Q21.51 12 24 12q-2.49 0-4.68-.93a12.3 12.3 0 0 1-3.81-2.58 12.3 12.3 0 0 1-2.58-3.81Q12 2.49 12 0q0 2.49-.96 4.68-.93 2.19-2.55 3.81a12.3 12.3 0 0 1-3.81 2.58Q2.49 12 0 12q2.49 0 4.68.96 2.19.93 3.81 2.55t2.55 3.81"/>
  </svg>
);

/** engine tile: app-icon style with real brand mark */
const EngineTile: React.FC<{
  label: string;
  bg: string;
  a: Actor;
  children?: React.ReactNode;
}> = ({ label, bg, a, children }) => (
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 12,
      opacity: Math.min(1, a.enter * 1.7) * (1 - a.exit),
      transform: `scale(${(2.1 - a.enter * 1.1) * settle(a.local)})`,
      filter: `blur(${(1 - a.enter) * 15}px)`,
    }}
  >
    <div
      style={{
        width: 84,
        height: 84,
        borderRadius: 22,
        background: bg,
        border: "1px solid rgba(255,255,255,0.14)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxShadow: "0 14px 40px rgba(0,0,0,0.4)",
      }}
    >
      {children}
    </div>
    <span
      style={{
        fontFamily: FONT,
        fontWeight: 600,
        fontSize: 20,
        color: C.darkSoft,
      }}
    >
      {label}
    </span>
  </div>
);

/** real Distribb logo: grainy blurred orange radial (from site header) */
const DistribbDot: React.FC<{ size?: number; idSuffix: string }> = ({
  size = 144,
  idSuffix,
}) => (
  <svg width={size} height={size} viewBox="0 0 500 500">
    <defs>
      <filter
        id={`grainyBlur-${idSuffix}`}
        x="-20%"
        y="-20%"
        width="140%"
        height="140%"
      >
        <feGaussianBlur in="SourceGraphic" stdDeviation="35" result="blur" />
        <feTurbulence
          type="fractalNoise"
          baseFrequency="0.65"
          numOctaves="3"
          result="noise"
        />
        <feComposite
          operator="in"
          in="noise"
          in2="blur"
          result="maskedNoise"
        />
        <feBlend in="blur" in2="maskedNoise" mode="overlay" />
      </filter>
      <radialGradient
        id={`intenseOrangeRadial-${idSuffix}`}
        cx="50%"
        cy="50%"
        r="50%"
      >
        <stop offset="0%" stopColor="#FF0600" />
        <stop offset="30%" stopColor="#FF3500" />
        <stop offset="100%" stopColor="#FF8A00" stopOpacity="0" />
      </radialGradient>
    </defs>
    <circle
      cx="250"
      cy="250"
      r="165"
      fill={`url(#intenseOrangeRadial-${idSuffix})`}
      filter={`url(#grainyBlur-${idSuffix})`}
    />
  </svg>
);

/** ambient drifting micro-elements: keeps every frame alive */
const Ambient: React.FC<{ frame: number; light: number }> = ({
  frame,
  light,
}) => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    {Array.from({ length: 14 }).map((_, i) => {
      const depth = 0.4 + rnd(i + 5) * 0.9;
      const x = ((rnd(i) * 2100 + frame * (6 + depth * 9) * 0.06) % 2100) - 90;
      const y =
        80 +
        rnd(i + 21) * 920 +
        Math.sin((frame + i * 43) / (30 + i * 3)) * 18;
      const kind = i % 3;
      const op = (0.05 + rnd(i + 60) * 0.06) * depth;
      const col = light > 0.5 ? "17,17,17" : "255,255,255";
      return (
        <div
          key={i}
          style={{
            position: "absolute",
            left: x,
            top: y,
            opacity: op,
            transform: `scale(${depth}) rotate(${(frame + i * 31) * 0.4}deg)`,
            filter: depth < 0.8 ? "blur(2px)" : undefined,
          }}
        >
          {kind === 0 ? (
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: "50%",
                border: `2.5px solid rgba(${col},0.9)`,
              }}
            />
          ) : kind === 1 ? (
            <svg width="16" height="16" viewBox="0 0 16 16">
              <path
                d="M8 2 V14 M2 8 H14"
                stroke={`rgba(${col},0.9)`}
                strokeWidth="2.4"
                strokeLinecap="round"
              />
            </svg>
          ) : (
            <div
              style={{
                width: 22,
                height: 8,
                borderRadius: 999,
                background: `rgba(${col},0.8)`,
              }}
            />
          )}
        </div>
      );
    })}
  </AbsoluteFill>
);

/** speed streaks flashing during section whips */
const TRANSITIONS: { f: number; dir: 1 | -1 }[] = [
  { f: 170, dir: -1 },
  { f: 390, dir: 1 },
  { f: 513, dir: -1 },
  { f: 609, dir: 1 },
  { f: 689, dir: -1 },
  { f: 778, dir: 1 },
  { f: 934, dir: -1 },
  { f: 1021, dir: 1 },
];

const Streaks: React.FC<{ frame: number; light: number }> = ({
  frame,
  light,
}) => {
  const tr = TRANSITIONS.find((t) => frame >= t.f - 2 && frame <= t.f + 10);
  if (!tr) return null;
  const p = interpolate(frame, [tr.f - 2, tr.f + 10], [0, 1], CLAMP);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", zIndex: 60 }}>
      {[0, 1, 2, 3, 4].map((i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left:
              tr.dir === 1
                ? -400 + p * 2700 * (0.8 + rnd(i) * 0.5)
                : W + 400 - p * 2700 * (0.8 + rnd(i) * 0.5),
            top: 120 + rnd(i + 7) * 840,
            width: 200 + rnd(i + 3) * 260,
            height: 4 + rnd(i + 11) * 5,
            borderRadius: 999,
            background:
              i % 3 === 2
                ? C.orange
                : light > 0.5
                  ? "rgba(17,17,17,0.5)"
                  : "rgba(255,255,255,0.5)",
            opacity: (1 - p) * 0.55,
            filter: "blur(2px)",
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

