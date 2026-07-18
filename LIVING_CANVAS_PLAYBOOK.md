# Living Canvas Playbook — Boutique-Grade Motion Design Explainers

This playbook teaches an agent to produce SaaS launch/explainer videos at the
quality bar of top boutique motion studios. It was distilled from frame-level
reverse-engineering (8fps frame reconstruction, cut statistics, transcripts) of
reference-grade commercial explainers, then battle-tested across ten production
iterations of a real launch video. Every number in here was measured or earned.

**The one-sentence thesis: the video is ONE continuous living canvas — pacing
lives at the element level, not the cut level, and every element must answer
"what physical event causes me?"**

Use with the `living-canvas-explainer` recipe. Implementation target: Remotion
(single flat actor timeline). Audio: beat-locked VO + three-band music + a
30-60 event SFX bus, mixed in FFmpeg.

---

## 1. The Ten Laws

1. **Element-level pacing, not cut-level.** Reference-grade 60-75s explainers
   contain **0-3 hard cuts total** yet feel frantic. The canvas meaningfully
   reconfigures every **2.0-2.5s** via morphs, pops, punches, and swaps. A
   settled composition never holds more than **3.5s** (105 frames absolute
   ceiling) without a whole-canvas change.
2. **The hard cut is a spent resource.** Spend each one on a narrative pivot
   (problem→dark turn, light↔dark world flip). Because cuts are rare, each one
   lands like a punch.
3. **Camera choreography over persistent scenes.** A card lands ONCE and
   survives 4-9 seconds while a virtual camera walks the viewer through it:
   land → punch into the sub-region the VO names → creep → second focus → FX →
   whip out. Never re-enter the same element; never zoom without a target.
4. **Causal physics everywhere.** Elements don't "appear" — something makes
   them happen: a click thumps the list, an article emits its ranking, a
   collapse-burst births the next scene, landing chips push their neighbors.
   One DISTINCT mechanic per beat; repeating a trick reads as template.
5. **Layout reflow is choreography.** Lists rank-sort themselves on arrival
   with displacement blur; cards grow row by row; existing elements yield space
   when new ones claim it; chat pushes history upward.
6. **Story before pitch.** Open with a 10-15s first-person micro-story with
   emotional voice acting and a visual punchline, then hand off to the
   confident announcer at the dark turn. Comedy timing: the punchline reads in
   near-silence.
7. **Music is a narrator.** Three bands: naive/mundane bed under the story that
   HARD-STOPS the instant the punchline appears → deadpan silence → the real
   score slams in with the thesis line. Steady dynamics only — never sidechain
   ducking (audible pumping); carve VO space with static EQ instead.
8. **Accent discipline.** Exactly ONE brand-accent phrase per headline. Accent
   color is reserved for: emphasis words, FX (sparks/rings/fire), CTA button,
   score chips, the horizon line. Negatives may share the accent family.
   Green only for tiny success ticks.
9. **Micro-motion floor.** No frame is ever mathematically static: 1-6%/s creep
   zoom on every hold, background grid drift, ambient micro-glyph layer,
   counters ticking, pills breathing. Contact-sheet test: no two adjacent
   frames at 2fps may be identical.
10. **Blur telegraphs speed.** Any camera or element move completing in under
    ~9 frames carries 1-3 frames of directional blur; settled frames are
    perfectly crisp. Motion blur on fast moves is THE single detail separating
    pro output from template output.

---

## 2. Reference-Study Method (do this before styling any new video)

Reverse-engineer 4-8 reference videos in the target style:

```bash
# download
yt-dlp -f "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b" -o "ref.%(ext)s" <URL>
# hard-cut statistics (the number will be LOW for this style — that's the point)
ffmpeg -i ref.mp4 -vf "select='gt(scene,0.22)',metadata=print:file=cuts.txt" -an -f null -
# coarse pass: 2fps contact sheets to LOCATE choreographed sequences
ffmpeg -y -i ref.mp4 -vf "fps=2,scale=480:-1,tile=4x4" sheet_%02d.png
# dense pass: 8fps runs over each 4-10s sequence to RECONSTRUCT choreography
ffmpeg -y -ss <start> -t <dur> -i ref.mp4 -vf "fps=8,scale=420:-1,tile=6x4" dense_%02d.png
# transcript for VO-sync mapping
# (any word-level whisper; store words with start/end)
```

For each sequence write a second-by-second timeline distinguishing:
**ELEMENT motion** (card translating/scaling) vs **CAMERA motion** (whole scene
scaling/translating) vs **NEW LAYERS** (chips, cursors, particles ON TOP), and
which VO word each move syncs to. Estimate zoom factors by comparing element
sizes between adjacent frames. Generalize into numbers before writing code.

---

## 3. Numeric Pacing Spec

| Metric | Target |
|---|---|
| Total duration | 55-70s (launch), 40-50s (ad cutdown) |
| Hard cuts | 1-3 total; 0 in the first 10s |
| Meaningful beat (new headline/prop/mockup) | every 2.0-2.5s → 28-35 beats/60s |
| Sub-events inside a beat (word pop, chip, click, tick) | every 0.3-0.5s, 2-4 per beat |
| Montage/list items | 0.9-1.2s per item |
| Max settled hold | 3.5s (105 fr) before a whole-canvas morph |
| Frames with zero motion | 0 (bg drift + ≥1 fg element minimum) |
| Landing stagger | headline lands, prop +8-10 fr, badges +10-15 fr. Never simultaneous |
| Enter/exit overlap | next element starts entering 4-8 fr before current finishes exiting |
| Hold micro-motion | 1-2%/s scale/position drift on all settled elements |
| End card | 5-7s, strict sequential pops at 10-15 fr stagger, cursor clicks CTA in final 30 fr |

---

## 4. Script & Story Structure

### 4.1 The arc (60s version)

| Section | Duration | Content |
|---|---|---|
| **Story cold-open** | 10-15s | First-person micro-story, emotional VO, visual punchline (see 4.2) |
| **Dark turn** | 2-3s | THE hard cut. Canvas inverts to near-black. One brutal thesis line, kinetic type, optional glitch |
| **Product reveal** | 4-6s | Logo self-assembles (squash-stretch drop), name types on, badge pendulum-swings in, tagline with accent underline draw |
| **Features** | 3-4 chapters × 3-5s | Each chapter: one persistent card + camera journey + one causal mechanic |
| **AI/payoff beat** | 4-6s | The consequence moment (dark world OK), one cheeky microcopy aside |
| **Proof** | 3-4s | Claims land ON the evidence (pills sitting on the chart line), one full-canvas word slam |
| **CTA end card** | 5-7s + outro hold | Logo + pills + headline with a strike-through joke + button + cursor click + URL type-on |

### 4.2 Story cold-open rules (the humor engine)

- First person, present tense, mundane-specific actions. The audience must
  recognize themselves in <2 seconds.
- **Emotional VO**: generate with an expressive TTS that supports audio tags
  (e.g. ElevenLabs `eleven_v3` with `[tired] [hopeful] [excited] [disappointed]
  [sighs]` inline). Settings that worked: stability 0.35, style 0.6.
- **CRITICAL: tagged emotional reads render 40-60% dead air.** A 12s script
  comes back 23s. Fix in two passes:
  1. `silenceremove=stop_periods=-1:stop_duration=0.26:stop_threshold=-38dB,atempo=1.08`
  2. Whisper the result, then CUT AN ENTIRE BEAT if still >15s. (Cutting the
     "hope" beat so the payoff lands immediately after the action is usually
     both faster AND funnier.) Splice with `atrim` + `anullsrc` gaps of
     0.3-0.45s + `concat`.
- Keep the character drawls that ARE the joke (the tired "aaand— publish").
- Punchline structure: hope → interruption → deflation. The deflating reveal
  must be VISUAL (a card the viewer reads) while the VO reacts, and it gets a
  metadata tag that lands the joke 1-2 beats after the text ("BOT · JUST NOW").
- Beat-lock everything: whisper the final story audio, convert word times ×30
  to frames, and key every visual to a word.
- The story voice is intimate/quieter; the announcer takes over at the turn.
  Keep the step ≤ 7-8 dB (lift story VO ~+3 dB in the mix or the handoff reads
  as a volume bug instead of drama).

### 4.3 VO style for the pitch half

Clipped 2-second clauses, second person, present tense, zero hedging:
"It hunts the exact keywords people search when they're ready to pay."
18-30 VO segments per 40s. Every clause gets its own visual. One accent-colored
keyword phrase per headline. End with a friction-killer microcopy line
("Setup in minutes. No agency retainers.").

---

## 5. Architecture — Single Flat Actor Timeline

- ONE composition file. NO scene wrappers, NO `<Sequence>` grouping for actors.
- Every visual element is an **actor**: an IIFE with its own enter/exit frames
  from a central `T` timeline object, returning `null` when invisible.
- Frame numbers in `T` are **beat-locked to Whisper word timestamps**
  (`wordAt(t) = Math.round(t * 30)`).
- Background light/dark worlds are crossfaded fills driven by a pure
  `lightAmount(frame)` function — world flips are morphs (12-18 fr) except the
  1-2 designated hard cuts (instant).

### 5.1 The timeline-splice technique (adding/replacing sections later)

To prepend or replace an opening without re-timing 200 constants:

```tsx
export const STORY_SHIFT = 293;           // new opening length - old section length
const absFrame = useCurrentFrame();
const frame = absFrame - STORY_SHIFT;     // ALL existing internals keep their numbers
```

- New section renders on `absFrame`; downstream code uses shifted `frame`.
- Gate out replaced sections with an early `return null`.
- **GOTCHA:** internal frames 0-N now occur DURING the new opening (abs =
  internal + SHIFT). Any old section living in that internal window will render
  mid-story unless gated.
- **GOTCHA:** sections that must start before their internal frame 0 (e.g. a
  transition chain that begins during the previous section's exit) need their
  visibility gate widened manually — `actor()` visibility starts at enterAt-1,
  which may be later than the chain's first frame.
- Backgrounds/ambient layers should take `absFrame` so motion stays alive
  during the new opening; clamp `lightAmount` for `frame < firstCut` to the
  opening's world.
- Old VO splices under the new one: `atrim=start=<oldCutSec>,asetpts=PTS-STARTPTS,adelay=<ms>`
  so old second X lands exactly at the new absolute time of its internal frame.

---

## 6. Motion Helper Library (copy verbatim)

```tsx
const FPS = 30;
const CLAMP = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

/* snappy default spring — d11/s210 gives crisp pops with slight overshoot */
const spr = (frame: number, start: number, damping = 11, stiffness = 210): number =>
  spring({ fps: FPS, frame: Math.max(0, frame - start), config: { damping, stiffness, mass: 1 } });

/* actor: spring enter + linear exit window */
const actor = (frame: number, enterAt: number, exitAt: number, exitDur = 10) => {
  const enter = spr(frame, enterAt);
  const exit = interpolate(frame, [exitAt - exitDur, exitAt], [0, 1], CLAMP);
  return { visible: frame >= enterAt - 1 && frame <= exitAt,
           opacity: enter * (1 - exit), enter, exit, local: frame - enterAt };
};

/* micro-bounce after landing — apply as a scale multiplier to EVERYTHING that lands */
const settle = (local: number, from = 8) =>
  local > from ? 1 + Math.exp(-(local - from) / 7) * Math.sin((local - from) / 1.9) * 0.035 : 1;

/* animated list-slot position: rows physically re-sort as better ones arrive */
const slotAt = (frame: number, sched: { f: number; slot: number }[]) => {
  let s = sched[0].slot;
  for (let i = 1; i < sched.length; i++) {
    if (frame < sched[i].f) break;
    s += (sched[i].slot - s) * spr(frame, sched[i].f, 13, 200);
  }
  return s;
};

/* section camera rig: keys aim the camera CENTER (scene coords) + zoom.
   Stiff spring so punches complete in ~0.3s like the reference footage.
   Always-on creep (~4%/s capped +9%) so holds are never static. */
type CamKey = { f: number; x: number; y: number; s: number };
const camStateAt = (fr: number, keys: CamKey[]) => {
  let x = keys[0].x, y = keys[0].y, s = keys[0].s, lastF = keys[0].f;
  for (let i = 1; i < keys.length; i++) {
    if (fr < keys[i].f) break;
    const p = spring({ fps: FPS, frame: Math.max(0, fr - keys[i].f),
                       config: { damping: 16, stiffness: 250, mass: 1 } });
    x += (keys[i].x - x) * p; y += (keys[i].y - y) * p; s += (keys[i].s - s) * p;
    lastF = keys[i].f;
  }
  const creep = Math.min(0.09, Math.max(0, fr - lastF - 10) * 0.00135);
  return { x, y, s: s * (1 + creep) };
};
const camRig = (frame: number, keys: CamKey[]) => {
  const a = camStateAt(frame, keys), b = camStateAt(frame - 1, keys);
  /* velocity blur with a DEAD ZONE — without it, big zooms smear for 15+ frames */
  const vel = Math.hypot(a.x - b.x, a.y - b.y) + Math.abs(a.s - b.s) * 280;
  return { ...a, blur: vel > 3.5 ? Math.min(8, (vel - 3.5) * 0.28) : 0,
    style: { transformOrigin: "center",
      transform: `scale(${a.s}) translate(${W / 2 - a.x}px, ${H / 2 - a.y}px)` } };
};
// Usage per section:
// const cam = camRig(frame, [
//   { f: ENTER, x: 960, y: 500, s: 0.94 },   // wide land
//   { f: PUNCH, x: 960, y: 430, s: 1.3 },    // commit punch on VO word
//   { f: FOCUS, x: 1130, y: 398, s: 1.66 },  // extraction punch on the exact row/badge
//   { f: PULL,  x: 960, y: 500, s: 0.97 },   // pull-back with overshoot BELOW 1.0
// ]);
// <div style={{ position:"absolute", inset:0, ...cam.style,
//   filter: cam.blur > 0.3 ? `blur(${cam.blur}px)` : undefined }}>

/* decaying camera shake burst — sum several at the punch moments */
const shakeAt = (frame: number, start: number, dur = 8, amp = 6) => {
  const l = frame - start;
  if (l < 0 || l > dur) return { x: 0, y: 0 };
  const d = 1 - l / dur;
  return { x: (rnd(frame * 3.7 + 1) - 0.5) * 2 * amp * d,
           y: (rnd(frame * 7.1 + 13) - 0.5) * 2 * amp * d };
};

/* deterministic pseudo-random (Remotion requires render determinism) */
const rnd = (seed: number) => {
  const x = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

const typeOn = (text: string, local: number, cps = 0.55) =>
  text.slice(0, Math.max(0, Math.floor(local * cps)));
```

### 6.1 Kinetic headline (WordPop)

Per-word spring pops, each word keyed to its Whisper timestamp. Includes the
POV mode (words fly from the viewer: scale 2.05→1 + 18px blur), scatter-exit
(words fly apart radially like debris), strike-through support (a later word's
landing draws a bar through an earlier word), per-word entrance rotation
(±4.5° settling to 0), and micro-bounce. Weight 900, letterSpacing -0.045em,
key words in accent color with a soft glow textShadow. Sizes: 84-128px
headlines, up to 200px for the one full-canvas word slam.

```tsx
const p = spr(frame, w.at, 10.5, 230);
const rot = (rnd(i + 17) - 0.5) * 9 * (1 - p);
const base = pov ? interpolate(p, [0, 1], [2.05, 1], CLAMP) : 0.82 + p * 0.18;
const scX = exitScatter ? exit * exit * (rnd(i * 3 + 1) - 0.5) * 940 : 0;
const scY = exitScatter ? exit * exit * (rnd(i * 7 + 2) - 0.5) * 660 : 0;
transform: `translate(${scX}px, ${(1 - p) * size * (pov ? 0.1 : 0.5) + scY}px)
  scale(${base * settle(frame - w.at)}) rotate(${rot + (exitScatter ? exit * (rnd(i+13)-0.5) * 80 : 0)}deg)`
filter: `blur(${(1 - p) * (pov ? 18 : 8)}px)`
// strike-through: absolutely-positioned bar inside the word span,
// height max(5, size*0.09), scaleX 0→1 over 6 fr, transformOrigin left;
// word color dims to subtle after strike+6.
```

---

## 7. Camera Choreography Grammar (the state machine)

Canonical lifecycle of one persistent card. Beat length 2.5-8s. S3/S4 may
repeat once; S5 optional; the rest mandatory.

```
S0 ENTRANCE-SETTLE -> S1 HOLD -> S2 PUNCH -> S3 CREEP-HOLD -> [S4 SECOND FOCUS]
   -> [S5 FX BURST] -> S6 EXIT-RAMP -> S7 WHIP-OUT/HANDOFF
```

| State | Duration | Camera behavior | Next-state trigger |
|---|---|---|---|
| S0 Entrance-settle | 6-12 fr | Born 1.3-1.4x oversized + blur (from camera) OR 0.85x rising; ~5% overshoot; locks | settle completes |
| S1 Hold | 30-80 fr | Locked except creep +1-4%/s. All motion INSIDE the card (rows fill, text types, cursor glides ~0.5s) | VO word naming the sub-feature, or cursor arrival +6 fr |
| S2 Punch | 6-9 fr | 1.08x (highlight) to 1.40x (commit), hard-eased, **centered on the sub-region, not the card center**; 1-2 blurred frames; highlight FX fires in the SAME 2-4 frames; max ONE hard punch per beat | punch lands |
| S3 Creep-hold | 25-80 fr | Creep 3-6%/s drifting TOWARD the working control (≤+15% total). Micro-events every 18-24 fr — camera never reacts to them | VO word / elapsed |
| S4 Second focus | pan 12-22 fr / extraction 18-24 fr | (a) lateral/vertical pan 35-50% frame dimension at ZERO zoom with directional blur, or (b) extraction zoom 1.66-2.2x onto ONE sub-element which morphs into the next hero. Never pan+zoom combined | VO phrase |
| S5 FX burst | FX 5-10 fr, decay ≤45 fr | **Camera fully locked.** Counter rolls (24-30 fr), particles peak at value-landing frame, fire ring 6 fr. The biggest emotional beat gets ZERO camera motion | FX decay done |
| S6 Exit-ramp | 12-15 fr | Accelerating push 1.10→1.23x (ease-IN into the cut). Never cut out of stillness | elapsed |
| S7 Whip-out | 6-9 fr | Directional whip, heavy blur. **Asymmetric**: chrome exits first, the proof surface survives 30-45 fr longer or is carried into the next beat. Scenes overlap 5-8 fr | next S0 |

**Sync rules:** every reframe is earned by a VO word, tolerance ±4 fr at 30fps
(or the visual LEADS by 6-18 fr — never lags more than 4). The punch lands ~6
fr AFTER the cursor arrives — cursor motivates, camera confirms.

**Anti-rules:** never re-enter an exited element; never zoom without a named
target; camera and element moves are mutually exclusive (except always-on
creep); camera frozen during cascades, counters, and shuffles.

---

## 8. FX Layer Catalog

All FX render ABOVE the persistent card; the card is never redrawn.

| FX | Spec |
|---|---|
| **RingPulse** | expanding circle at target: size×ease over 22 fr, border 4→1.5px, opacity (1-p)×0.9. Fires in the same 2-4 fr as its punch. Double-fire (large then small, +12 fr) for clicks |
| **GlowSweep** | diagonal white light band (rotate 14°, width 36% of card) sweeping across over 18 fr, opacity peaks mid |
| **Sparks** | 10-18 deterministic particles, radial burst, distance ease-out, mixed circles/squares, decay 26 fr |
| **HeatFlare** (payoff fire) | 6 flame-lick shapes (borderRadius `50% 50% 46% 46% / 70% 70% 28% 28%`), heights 44-84px flickering via `rnd(floor(frame*0.8)+i)`, blur 6px, opacity 0.55, gradient transparent→#FF9A2E→accent, + a radial heat glow. **Place it licking from BEHIND the row's TOP edge (y = rowTop − ~50) — centered on the row it COVERS the text** |
| **Embers** | 16 rising particles for dark-world payoffs, cycle 34-60 fr, opacity ∝ (1-rise), blur 0.6px |
| **Flash** (burst) | white radial: pre-glow builds 6 fr BEFORE the hit (grow 0.25→1), blooms out 11 fr after, radius 260+grow×420+l×90 |
| **Streaks** | 5 horizontal speed lines flashing through frame during section whips (12 fr), 1-in-3 accent colored, blur 2px |
| **Ambient** | 14 tiny glyphs (dot outlines, plus signs, dashes) at 3 depths drifting continuously, opacity 0.05-0.11, far layer blurred 2px. Runs on ABSOLUTE frame so it never freezes |
| **Ghost chapter titles** | 280-330px word behind each feature card at 4-6% opacity, drifting +0.04%/fr scale. Names the chapter without a title card |
| **Cursor** | chunky arrow (~52px, white outline, drop shadow), eased approach over 15-26 fr, 1-fr press state (button depresses 4-5px, shadow shrinks), accent ripple ring on click. The CLICK TARGET must be verified against the button's actual layout coordinates — compute, don't eyeball |
| **Camera shakes** | sum `shakeAt()` bursts at: hard cuts (amp 7), logo land (5), word slam (9), burst moments (6), CTA click (6) |

---

## 9. Layout Reflow Physics

- **Rank-sort shuffle** (the signature): rows land in "discovery order"; each
  better row inserts ABOVE, physically pushing others down. Rows are
  `position:absolute; top: slotAt(frame, sched) * 76` inside a relative
  container whose height animates: `Σ min(1, spr(frame, row.enter)) * 76`
  (the card physically GROWS a row at a time). Displacement blur:
  `|slotY(f)−slotY(f−1)| * 76 * 0.55` capped 6px. Row schedule example:
  info-row enters f420 slot0 → pushed to slot1 at f430, slot2 at f442, slot3
  at f454 as buy-rows land above it, then struck through.
- **Width-push reflow**: chips in a centered flex row get an outer wrapper with
  `width: enterSpring * naturalWidth; overflow: visible` — each landing chip
  physically pushes its neighbors as the row re-centers.
- **Yield reflow**: when a second card claims screen space, the first one
  translates away (-265px) and steps back (scale ×0.92) via its own spring.
  Two cards must NEVER overlap "awkwardly" — any new arrival displaces.
- **Column re-centering**: a growing vertical lockup (logo → badge → tagline)
  lifts its top by ~40-46px per added element so the optical center holds.
- **Chat push-up**: each new message/tile row pushes prior bubbles up 26-46px.
- **Micro-thump**: a click dips the whole list 3.5px over [click, +3, +8].

---

## 10. Transformation Chains (scene B born from scene A's matter)

The signature transition. Use 1-2× per video, spaced 20s+, on the most
important handoffs (reveal→feature-1; proof→CTA).

Full chain (~1.3-1.6s), beat-locked to the VO phrase it illustrates:

| Phase | Frames | What happens |
|---|---|---|
| Gather | 15-17 fr | A cartoon glove hand glides in from off-screen (smoothstep ease) trailing 5 content chips (staggered 34px, ±35px scatter, each fading in over 4 fr) |
| Flick-launch | 3-4 fr | Hand accelerates +190px, rotates -24°, exits with 3px/fr blur |
| Orbit | 10-12 fr | Chips lerp from trail positions onto a circle r≈205 (blend factor = launch spring), ring stroke fades in, formation rotates 0.014 rad/fr, chips glow (boxShadow accent 10→34px) |
| Collapse | 6-8 fr | Radius springs 205→6 (d11/s240), chips shrink ×0.45 + blur 7px, glow intensifies |
| Burst | 6-11 fr | `Flash` (pre-glow started 6 fr earlier) + `RingPulse` size 680 + `Sparks` n16 d320 + camera `shakeAt` amp 6 |
| Birth | 10-14 fr | The next scene's hero card scales 0.12→1 from the collapse point (spring d11/s210) with `brightness(2.5→1)` + blur 9→0, then its internal cascade begins |

Small echo variant: a giant word slam collapses (scale ×0.07, translateY -200,
blur 10, over 9 fr) → Flash/Ring/Sparks → the logo drops out of the burst.

**GOTCHA:** if the chain starts during the previous section's exit, widen the
host section's visibility gate to the chain's first frame or the hand never
renders.

---

## 11. Causal Mechanics Catalog (one per beat, never repeat)

1. **Tip-over fall** — a "dead" card rotates 34° around a bottom corner
   (`transformOrigin: 85% 100%`) and drops off screen with fall² gravity.
2. **Gravity rain** — cards drop from -640px with damping-9 spring (overshoot
   = bounce), staggered 6 fr.
3. **Vacuum spiral** — on exit everything translates toward one point
   (×0.92 suck), rotates ±130°, shrinks ×0.85, blurs 8px; the next beat's
   words shoot OUT of that same point.
4. **Debris scatter** — headline words fly apart radially on exit (see WordPop).
5. **Squash-stretch drop** — logo falls -340px with bouncy spring (d7.5/s150);
   squash = `min(0.28, |Δp| * 5)`; `scaleX(1+sq*0.75) scaleY(1−sq)`,
   `transformOrigin: 50% 100%`.
6. **Pendulum swing-in** — badges/pills hang from above:
   `rotate(exp(-l/12)·sin(l/2.8)·9°)`, `transformOrigin: 50% -24px`.
7. **Click thump** — see reflow.
8. **Arc emission** — rank rows fly from the editor card in a parabola:
   `translateX((1-p)·-470) translateY(-sin(min(1,p)·π)·85)` + 6px blur.
9. **Cell drops** — calendar dots fall -46px into their cells with d9 bounce,
   staggered 1.1 fr.
10. **Wire-draw** — an SVG path draws (dashoffset, 9 fr) from the header icon
    to each row as it's verified; three wires staggered with the ring pulses.
11. **Convergence beams** — thin white lines (1.6px, opacity 0.7→0.45) draw
    from each source tile to the answer card, staggered 3 fr.
12. **Evidence-mounted claims** — proof pills sit ON the chart line at their
    data points and pulse `1 + exp(-(f-pass)/6)·0.14` as the line-draw passes
    through them (compute pass frames from path-length fraction).
13. **Typographic strike** — when the correcting word lands, a bar draws
    through the corrected word (6 fr) and it dims.

---

## 12. Design System

- **Type**: one geometric-humanist sans (e.g. Satoshi via `@remotion/fonts`
  local TTFs: 500/700/900). Headlines 900, UI labels 700, muted 500. Ghost
  titles 280-330px at 4-6% opacity. Sentence case. letterSpacing -0.02 to
  -0.07em. No thin weights ever.
- **Canvas**: light world `#F5F5F5` + 44px grid at ~2.8% contrast (drifting
  0.06px/fr) + 2-3 giant blurred accent-tinted blobs at 6-7% opacity drifting
  on sin/cos; dark world `#101012` with the same grid (reads as inversion, not
  a new video) + a glowing accent horizon line at y=86% (breathing shadow
  26±8px).
- **Cards**: white, radius 22, `0 24px 80px rgba(17,17,17,0.10), 0 6px 24px
  rgba(17,17,17,0.07)`, 1px line border. Skeleton bars for all non-load-bearing
  text (only 4-6 labels legible per card). NO browser chrome, NO bezels, NO
  screenshots — everything redrawn as animated components.
- **Sharp Tag data badges (the anti-pill)**: fully-rounded glowing pills read
  as template output. Data badges are split cells: 3px radius, 1.5px border
  (accent when active, `rgba(17,17,17,0.20)` when not), label cell (accent bg,
  white 700 15px, letterSpacing 0.12em) + value cell (white bg, MONO 700 22px
  tabular). Status chips: 3px-radius rectangle, 1.5px accent border, square
  7px dot (pulsing opacity), LETTERSPACED UPPERCASE 15px. Stamps ("PUBLISHED"):
  2px border, rotate -7°, scale-in 1.7→1 with settle. Statement pills (checked
  claims) may stay rounded — they're statements, not data.
- **3D tilts**: power cards live tilted — `perspective(1200-1400px)
  rotateX(12-16°) rotateY(±8-14°)` + slow sin wobble (±2-2.5° at /17-23 fr
  periods) — and UNTILT flat (spring d14/s150) exactly when the camera punches
  in to read them. Tilt while accumulating; flat for reading.
- **Accent discipline**: see Law 8. Competitor/engine logos are allowed as
  real inline-SVG marks in app-icon tiles (their colors vs your restraint is
  the point) — check trademark comfort for paid placements.

---

## 13. Audio System

### 13.1 Three-band music grammar

```
[ mundane bed ]––hard-stop––[ SILENCE under punchline ]––[ score enters at the turn ]
0s              punchline-appear (~9-10s)              turn (~15s)              end
```

- Bed: "light elevator jazz, lounge muzak, soft brushed drums, walking bass,
  mellow noodling piano, cheerful mundane office waiting-room mood,
  instrumental, steady volume" (generate ~12s). Mix at ~0.30 with a -5dB EQ
  notch at 1.8kHz; fade-in 0.5s; **hard-stop with a 0.2s fade the exact frame
  the punchline element pops** — the joke then reads in near-silence.
- Score: cinematic orchestral, "building strings, warm brass, driving staccato
  ostinato, no vocals, steady consistent dynamics, no sudden volume drops".
  Enters via `adelay` AT the hard cut with its own 1s fade-in.
- **Steady-bed mixing (never sidechain)**: `acompressor=threshold=-24dB:ratio=4:
  attack=25:release=450:makeup=3` to flatten swells, then STATIC EQ carve for
  VO space (`equalizer=f=1800:width_type=o:width=2.2:g=-6`, `f=350:g=-2`),
  then constant `volume=0.16`. Sidechain ducking = audible pumping = rejected.
- Target: music 10-11 dB under VO; program −16 LUFS / TP −1.5 via `loudnorm`;
  LRA ~1.5-4 for pitch-only videos, up to ~10 when a story open is present
  (the intimate→announcer step is intentional, capped ~7-8 dB).

### 13.2 SFX bus (30-60 beat-locked events)

Generate a 9-effect kit via text-to-SFX (min duration 0.5s!):
`whoosh_short` (0.8s), `whoosh_deep` (1.2s), `click` (0.5s), `typing_fast`
(2.2s), `pop` (0.5s), `glitch` (0.9s), `riser` (1.5s), `impact` (1.2s),
`chime` (0.9s).

Event mapping (volumes are pre-bus; bus runs at 0.7 into the mix):

| Event | SFX | vol |
|---|---|---|
| Section whip transitions | whoosh_short | 0.45 |
| Camera punch-ins | whoosh_short trimmed 0.5s | 0.22 |
| Row shuffles | whoosh_short trimmed 0.4s | 0.15 |
| Hard cut to dark | whoosh_deep | 0.5 |
| Glitch word | glitch | 0.4 |
| Into reveal / into slam / chain collapse | riser (trim 0.6-1.0s) | 0.3-0.42 |
| Logo land / slam / bursts | impact | 0.3-0.5 |
| Every type-on (title, question, URL, bot comment) | typing_fast trimmed to the visible typing duration | 0.28-0.33 |
| Cursor clicks | click | 0.6 |
| Chip/pill/stamp landings (pick ~10, don't do all) | pop | 0.3 |
| Notification / #1 rank / "you" | chime | 0.28-0.34 |

Build the bus programmatically (python generates an ffmpeg
`filter_complex_script`): one input per SFX file, `asplit=N` per usage count,
each instance `atrim`(optional)+`afade out 0.2`+`volume`+`adelay=ms|ms`, then
`amix=inputs=N:normalize=0` + `apad=whole_dur=<len>` → `sfx_bus.wav`. Verify
placement with windowed `volumedetect` at 3-4 event times vs a silent window.

### 13.3 Final mix graph (4 stems)

```
[storyVO ×1.45][mainVO atrim/adelay] → amix → [vo]
[jazz: EQ, 0.30, fades, atrim 0:stop] 
[orch: compressor+EQ+0.16+fades+atrim, adelay to turn]
[sfx_bus ×0.7]
[vo][jazz][orch][sfx] amix normalize=0 → loudnorm I=-16:TP=-1.5:LRA=11
```

---

## 14. Production Pipeline & QC

1. **VO first.** Generate → Whisper word timestamps → build `T` from words.
   The audio drives every frame number. New voice = re-lock everything.
2. **Probe-still QC loop** (the workhorse): render 10-20 single frames at the
   critical beats (`npx remotion still ... --frame=N`), READ them, fix, repeat.
   Check every punch frame, every shuffle mid-flight, every FX peak, both
   transitional (blurred) and settled (crisp) states.
3. **Render**: `npx remotion render src/index.ts <Comp> out.mp4 --concurrency=4
   --timeout=120000`. **GOTCHA:** local-font `loadFont` delayRender times out
   at concurrency 8 on full renders (probes fine) — use 4 + 120s timeout.
   **GOTCHA:** if the project lives in a cloud-synced folder (Drive/Dropbox),
   rsync to local tmp (exclude node_modules) and build there — sync daemons
   break esbuild.
4. **Mix in FFmpeg** (never in the renderer): `-c:v copy` remux keeps video
   untouched across audio iterations.
5. **Verify**: duration, `ebur128` I/LRA, windowed `volumedetect` at splice
   points and SFX events, final proof frames from the actual export.
6. Keep `job_state.json` current (version, artifacts, metrics, changes).

### Iteration checklist (ship gate)

- [ ] 0-3 hard cuts, each on a narrative pivot
- [ ] No settled hold > 105 frames; creep running on every hold
- [ ] Every reframe earned by a VO word (±4 fr)
- [ ] Every landing staggered; everything that lands gets `settle()`
- [ ] Fast moves carry blur; settled frames crisp; blur dead-zone active
- [ ] One distinct causal mechanic per beat, none repeated
- [ ] Reflow: no two cards ever overlap without a yield
- [ ] Cursor targets verified against computed layout coordinates
- [ ] 1-2 transformation chains max, 20s apart
- [ ] Story punchline in near-silence; music bands land on their frames
- [ ] One accent phrase per headline; data badges are Sharp Tags, not pills
- [ ] Fire/particle FX never cover the text they highlight
- [ ] −16 LUFS, TP ≤ −1.5, music 10-11 dB under VO
- [ ] Watch the 2fps contact sheet of YOUR OWN render: no two adjacent frames identical

---

## 15. Failure Modes Observed (don't repeat these)

- Sidechain-ducked music → audible pumping → client rejection. Static EQ carve.
- Emotional TTS dead air (23s from a 12s script) → silence surgery + cut a beat.
- Fire FX centered on a row → covered the punchline text. Lick from behind the top edge.
- Velocity blur without a dead zone → 15-frame smears after big zooms.
- Cursor "clicking" 165px below the button → compute the target from card layout.
- Two cards stacked with no yield → "awkward". Displacement is mandatory.
- Section gate at enterAt-1 ate a transition chain's first 13 frames.
- Full-frame renders failing at concurrency 8 with local fonts (delayRender).
- Fully-rounded glowing badge pills → instantly reads as AI-template output.
- 21s of stage-setting before the pitch → compress to ≤15s; cut the hope beat.
- zsh word-splitting in `for pair in "a b"` loops silently merging outputs — use `printf | while read`.
