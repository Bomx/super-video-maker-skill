/**
 * SECTION TEMPLATE — one fully-assembled beat, every number explained.
 *
 * motion-library.tsx gives you the PARTS. This file shows the ASSEMBLY, which
 * is where most iterations get burned. Copy a block, swap the content, keep
 * the structure and the timing relationships.
 *
 * Two references below:
 *   A) FEATURE BEAT  — persistent card + camera journey + reflow + FX + exit
 *   B) STORY BEAT    — a cold-open vignette with a punchline
 *
 * Every frame number is expressed relative to the beat start (B) so you can
 * paste a beat anywhere by changing one constant. In production you set B from
 * the VO word map: B = round(wordStartSeconds * 30).
 */

import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import {
  C, FONT, W, H, CLAMP,
  spr, actor, settle, slotAt, camRig, rnd, typeOn,
  Card, SharpTag, Cursor, GhostTitle,
  RingPulse, GlowSweep, Flash, Sparks,
} from "./motion-library";

/* ═══════════════════════════════════════════════════════════════════════
   A) FEATURE BEAT — the workhorse. ~4.5s (135 frames).

   Beat anatomy (offsets from B, at 30fps):
     +0    card is born / flies in            <- S0 entrance settle
     +6..  content cascades (rows, chips)     <- camera LOCKED during cascade
     +40   commit punch on the VO word        <- S2, 1.30x, ~9fr
     +67   extraction punch on ONE element    <- S4, 1.66x, the money shot
     +72   FX fires (ring/sweep) w/ the punch <- same 2-4 frames, never after
     +90   pull-back, overshoot BELOW 1.0     <- reads as "exhale"
     +123  exit whip (12fr, heavy blur)       <- S7, next beat overlaps by 5-8
   ═══════════════════════════════════════════════════════════════════════ */

const FeatureBeat: React.FC<{ frame: number; B: number }> = ({ frame, B }) => {
  const a = actor(frame, B, B + 135, 12);
  if (!a.visible) return null;

  /* ---- CAMERA -------------------------------------------------------
     x,y = where the camera CENTER aims in scene coords (not the element's
     own position). s = zoom. Rule: punch centers on the SUB-REGION the VO
     names, never the card center — that's what makes it feel directed.
     Final key dips to 0.97 (below 1.0): the pull-back must overshoot or the
     beat feels like it just stopped rather than resolved.                */
  const cam = camRig(frame, [
    { f: B,       x: 960,  y: 500, s: 0.94 },  // land wide, slightly out
    { f: B + 40,  x: 960,  y: 430, s: 1.30 },  // commit: whole card
    { f: B + 67,  x: 1130, y: 398, s: 1.66 },  // extraction: THE badge/row
    { f: B + 90,  x: 960,  y: 500, s: 0.97 },  // pull back + exhale
  ]);

  /* ---- REFLOW SCHEDULE ----------------------------------------------
     Rows arrive in DISCOVERY order and re-sort. The weak row lands first
     and gets pushed down as each strong row inserts above it. 12-frame
     spacing = ~0.4s per arrival, the fastest that still reads.
     Row pitch 76px must match slotAt's multiplier below.                 */
  const ROW_H = 76;
  const rows = [
    { label: "weak item",   score: 12, buy: false, enter: B + 10,
      sched: [{ f: B + 10, slot: 0 }, { f: B + 20, slot: 1 },
              { f: B + 32, slot: 2 }, { f: B + 44, slot: 3 }] },
    { label: "strong one",  score: 94, buy: true,  enter: B + 20,
      sched: [{ f: B + 20, slot: 0 }] },
    { label: "strong two",  score: 91, buy: true,  enter: B + 32,
      sched: [{ f: B + 32, slot: 1 }] },
    { label: "strong three",score: 88, buy: true,  enter: B + 44,
      sched: [{ f: B + 44, slot: 2 }] },
  ];
  /* container height animates so the CARD PHYSICALLY GROWS row by row */
  const listH = rows.reduce(
    (acc, r) => acc + Math.min(1, spr(frame, r.enter, 14, 190)) * ROW_H, 0);

  /* ---- CURSOR: motivates the punch. Camera confirms ~6fr AFTER the click */
  const clickAt = B + 61;
  const cx = interpolate(frame, [B + 38, clickAt - 4], [1360, 1185], {
    ...CLAMP, easing: (t) => 1 - (1 - t) * (1 - t) });
  const cy = interpolate(frame, [B + 38, clickAt - 4], [900, 478], {
    ...CLAMP, easing: (t) => 1 - (1 - t) * (1 - t) });
  const press = interpolate(frame, [clickAt, clickAt + 3, clickAt + 8],
    [0, 1, 0], CLAMP);

  /* ---- EXIT WHIP: quadratic so it accelerates out of frame */
  const exit = interpolate(frame, [B + 123, B + 135], [0, 1], CLAMP);

  /* ---- 3D TILT: card lives tilted while ACCUMULATING, untilts flat for
     reading exactly when the commit punch arrives.                        */
  const flat = spr(frame, B + 40, 14, 150);
  const tiltX = (1 - flat) * (14 + Math.sin(frame / 17) * 2.5);
  const tiltY = (1 - flat) * (-9 + Math.cos(frame / 21) * 2);

  return (
    <AbsoluteFill style={{ zIndex: 10 }}>
      <GhostTitle text="HUNT" frame={frame} a={a} />

      {/* everything inside this div rides the camera */}
      <div style={{
        position: "absolute", inset: 0, ...cam.style,
        filter: cam.blur > 0.3 ? `blur(${cam.blur}px)` : undefined,
      }}>
        {/* FX layers sit ABOVE the card; fire WITH the punch, never after.
            Double ring (large then small, +12fr) reads as a click impact. */}
        <RingPulse x={1265} y={398} start={B + 70} frame={frame} size={190} />
        <RingPulse x={1265} y={398} start={B + 82} frame={frame} size={150} />

        <div style={{
          position: "absolute", left: W / 2 - 430, top: 262,
          opacity: a.opacity * (1 - exit),
          transform:
            `translateX(${-exit * exit * 320}px) scale(${settle(frame - B)})` +
            ` perspective(1300px) rotateX(${tiltX}deg) rotateY(${tiltY}deg)`,
          filter: `blur(${(1 - a.enter) * 8 + exit * 12}px)`,
        }}>
          <Card style={{ width: 860, padding: 30 }}>
            <div style={{ display: "flex", justifyContent: "space-between",
              alignItems: "center", marginBottom: 22 }}>
              <span style={{ fontFamily: FONT, fontWeight: 900, fontSize: 30,
                letterSpacing: "-0.03em", color: C.ink }}>Section title</span>
              {/* status chip: 3px radius + square pulsing dot, never a pill */}
              <div style={{ display: "flex", alignItems: "center", gap: 9,
                padding: "6px 14px", borderRadius: 3,
                border: `1.5px solid ${C.orange}`, color: C.orange,
                fontFamily: FONT, fontWeight: 700, fontSize: 15,
                letterSpacing: "0.14em" }}>
                <div style={{ width: 7, height: 7, background: C.orange,
                  opacity: 0.5 + Math.sin(frame * 0.3) * 0.5 }} />
                WORKING
              </div>
            </div>

            {/* the click THUMPS the list 3.5px — consequence, not decoration */}
            <div style={{ position: "relative", height: listH,
              transform: `translateY(${interpolate(frame,
                [clickAt, clickAt + 3, clickAt + 8], [0, 3.5, 0], CLAMP)}px)` }}>
              {rows.map((r, i) => {
                const ra = actor(frame, r.enter, B + 135, 8);
                if (!ra.visible) return null;
                const slotY = slotAt(frame, r.sched);
                /* displacement blur = how fast this row is being shoved */
                const shove = Math.abs(slotY - slotAt(frame - 1, r.sched)) * ROW_H;
                const scoreNow = Math.round(interpolate(frame,
                  [r.enter + 4, r.enter + 26], [0, r.score], CLAMP));
                const lit = r.buy && frame >= clickAt + 2 && i === 1;
                return (
                  <div key={i} style={{
                    position: "absolute", left: 0, right: 0, top: slotY * ROW_H,
                    display: "flex", alignItems: "center",
                    justifyContent: "space-between",
                    padding: "16px 20px", borderRadius: 14,
                    background: lit ? "rgba(225,29,42,0.10)" : "rgba(17,17,17,0.025)",
                    border: `2px solid ${lit ? C.orange : "transparent"}`,
                    opacity: ra.opacity,
                    transform: `translateX(${(1 - ra.enter) * 120}px)`,
                    filter: `blur(${(1 - ra.enter) * 5 + Math.min(6, shove * 0.55)}px)`,
                  }}>
                    <span style={{ fontFamily: FONT, fontWeight: 700, fontSize: 30,
                      letterSpacing: "-0.02em", color: C.ink,
                      textDecoration: r.buy ? "none" : "line-through",
                      textDecorationColor: C.orange, textDecorationThickness: 3 }}>
                      {r.label}
                    </span>
                    {/* badge pops 7fr AFTER its row lands — staggered landings */}
                    <span style={{ display: "inline-block", transform:
                      `scale(${(0.4 + 0.6 * Math.min(1,
                        spr(frame, r.enter + 7, 9, 260) * 1.2))
                        * settle(frame - r.enter - 7)})` }}>
                      <SharpTag label={r.buy ? "BUY" : "INFO"}
                        value={scoreNow} active={r.buy} />
                    </span>
                  </div>
                );
              })}
            </div>
          </Card>
          {/* light sweep 15fr after landing = "this surface is alive" */}
          <GlowSweep start={B + 15} frame={frame} w={860} h={470} />
        </div>

        {frame >= B + 38 && frame <= B + 127
          ? <Cursor x={cx} y={cy} press={press} /> : null}
      </div>
    </AbsoluteFill>
  );
};

/* ═══════════════════════════════════════════════════════════════════════
   B) STORY BEAT — cold-open vignette. The comedy is in the TIMING, so every
   element is pinned to a spoken word, and the punchline gets silence.

   Pattern: setup element -> action (cursor/type) -> consequence -> the joke
   arrives as a READABLE card while the VO reacts, then a metadata tag lands
   1-2 beats later to seal it ("BOT · JUST NOW").
   ═══════════════════════════════════════════════════════════════════════ */

const StoryBeat: React.FC<{ frame: number; B: number }> = ({ frame, B }) => {
  if (frame < B || frame > B + 180) return null;

  /* the vacuum: at the end everything spirals into one point, and the next
     scene's words shoot OUT of that same point (see playbook §11.3) */
  const suck = interpolate(frame, [B + 150, B + 176], [0, 1], CLAMP);
  const spiral = (x: number, y: number): React.CSSProperties => ({
    transform: `translate(${(960 - x) * suck}px, ${(540 - y) * suck}px)` +
      ` rotate(${suck * 80}deg) scale(${1 - suck * 0.85})`,
    opacity: 1 - suck * 0.9,
    filter: suck > 0.1 ? `blur(${suck * 7}px)` : undefined,
  });

  const cardP = spr(frame, B + 4, 11, 210);
  const title = typeOn("Your headline types here", frame - B - 10, 0.33);
  /* YIELD: when a second card claims space, the first one MUST move over.
     Two cards overlapping with no yield is the #1 "amateur" tell.        */
  const yieldP = spr(frame, B + 100, 12, 190);
  /* the punchline card is born big+blurred and snaps in (POV entrance) */
  const jokeP = spr(frame, B + 130, 11, 210);
  const jokeText = typeOn("The unexpected reply.", frame - B - 133, 0.34);

  return (
    <AbsoluteFill style={{ zIndex: 14 }}>
      <div style={{ position: "absolute", left: 520, top: 250,
        ...spiral(910, 465), opacity: Math.min(1, cardP * 1.6) * (1 - suck * 0.9) }}>
        <div style={{ transform:
          `translateY(${(1 - cardP) * -60}px) translateX(${-yieldP * 265}px)` +
          ` scale(${(0.9 + cardP * 0.1) * (1 - yieldP * 0.08) * settle(frame - B - 4)})` }}>
          <Card style={{ width: 780, padding: 34 }}>
            <div style={{ fontFamily: FONT, fontWeight: 900, fontSize: 42,
              letterSpacing: "-0.03em", color: C.ink, minHeight: 54 }}>
              {title}
              <span style={{ color: C.orange,
                opacity: title.length < 23 && Math.floor(frame / 4) % 2 ? 1 : 0 }}>|</span>
            </div>
          </Card>
        </div>
      </div>

      {/* THE PUNCHLINE — lands in near-silence (music hard-stops here). */}
      {frame >= B + 129 ? (
        <div style={{ position: "absolute", left: 660, top: 560,
          ...spiral(950, 680),
          opacity: Math.min(1, jokeP * 1.7) * (1 - suck * 0.9) }}>
          <div style={{ transform:
            `scale(${(2.0 - Math.min(1, jokeP)) * settle(frame - B - 130)})`,
            filter: `blur(${(1 - Math.min(1, jokeP)) * 12}px)` }}>
            <Card style={{ width: 580, padding: 26 }}>
              <div style={{ fontFamily: FONT, fontWeight: 700, fontSize: 30,
                color: C.ink, lineHeight: 1.3, minHeight: 78 }}>{jokeText}</div>
              {/* the tag that seals the joke, 1-2 beats late */}
              {spr(frame, B + 160, 12, 220) > 0.02 ? (
                <div style={{ display: "inline-block", marginTop: 12,
                  fontFamily: FONT, fontWeight: 700, fontSize: 15,
                  letterSpacing: "0.08em", color: C.subtle,
                  border: "1.5px solid rgba(17,17,17,0.2)", borderRadius: 3,
                  padding: "2px 8px",
                  transform: `scale(${0.6 + Math.min(1, spr(frame, B + 160, 12, 220)) * 0.4})` }}>
                  BOT · JUST NOW
                </div>
              ) : null}
            </Card>
          </div>
        </div>
      ) : null}
    </AbsoluteFill>
  );
};

/* ═══════════════════════════════════════════════════════════════════════
   C) ROOT — how beats compose. Note: ONE flat file, no <Sequence>, beats
   overlap by 5-8 frames so the canvas never empties.
   ═══════════════════════════════════════════════════════════════════════ */

export const ExampleComposition: React.FC = () => {
  const frame = useCurrentFrame();
  /* T: every number here comes from the VO word map, never from taste.
     wordAt(t) = Math.round(t * 30)                                        */
  const T = { story: 0, feature1: 470, feature2: 600 };

  /* shake bursts stack at the impact moments */
  const shake = [T.feature1 + 40, T.feature2 + 40]
    .map((f) => (frame >= f && frame <= f + 8
      ? (rnd(frame * 3.7) - 0.5) * 2 * 6 * (1 - (frame - f) / 8) : 0))
    .reduce((a, b) => a + b, 0);

  return (
    <AbsoluteFill style={{ background: C.light, fontFamily: FONT,
      transform: `translateX(${shake}px)` }}>
      <StoryBeat   frame={frame} B={T.story} />
      <FeatureBeat frame={frame} B={T.feature1} />
      <FeatureBeat frame={frame} B={T.feature2} />
      {/* burst that births the next scene (playbook §10) */}
      <Flash  start={T.feature1 - 6} frame={frame} cx={960} cy={470} />
      <Sparks start={T.feature1 - 5} frame={frame} cx={960} cy={470} n={16} dist={320} />
    </AbsoluteFill>
  );
};
