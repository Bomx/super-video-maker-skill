# Remotion Video Production Guide — RebelGrowth

This document is the canonical reference for creating motion-design explainer videos using the Remotion setup in `remotion-videos/`. It encodes every lesson learned from analyzing 1600.agency's professional SaaS explainer videos and iterating until the output matched boutique agency quality.

**Use this as a system prompt when creating or modifying Remotion videos.**

---

## 1. Project Structure

```
remotion-videos/
├── package.json              # Remotion 4.0, React 19, Zod
├── remotion.config.ts        # JPEG output, overwrite
├── generate_voiceover.py     # ElevenLabs TTS with word timestamps
├── public/
│   ├── audio/                # voiceover.mp3 + timestamps.json (generated)
│   └── logos/                # client logos for CTA marquee
└── src/
    ├── index.ts              # Remotion entrypoint
    ├── Root.tsx              # Registers compositions
    └── DistribbExplainer/
        ├── DistribbExplainer.tsx   # Single flat composition — ALL actors live here
        ├── config.ts              # Colors, fonts, features, script
        ├── motionUtils.ts         # Animation primitives + actor() / actorSpring()
        └── components/            # Reusable visual components
            ├── AnimatedCursor.tsx
            ├── FloatingObjects.tsx
            ├── HandDrawnAccent.tsx
            ├── DashboardMockup.tsx
            ├── CalendarMockup.tsx
            ├── BacklinkMockup.tsx
            ├── RedditMockup.tsx
            └── SocialMockup.tsx
```

**Important:** There are NO scene wrapper files. The composition is a single flat file where every visual element (a title, a subtitle, a mockup, a cursor, badges) is an independent "actor" with its own enter/exit timing.

### Commands

```bash
cd remotion-videos
npx remotion studio          # Preview at localhost:3000
npx remotion render src/index.ts DistribbExplainer out/video.mp4
python3 generate_voiceover.py  # Generate voiceover + timestamps
```

---

## 2. Video Specification

| Property | Value |
|----------|-------|
| Resolution | 1080 × 1350 (semi-square, slightly taller) |
| FPS | 30 |
| Total frames | 1140 (~38 seconds) |
| Format | MP4 |
| Voiceover | ElevenLabs (eleven_v3 model) |
| Font heading | Plus Jakarta Sans (800 weight) |
| Font body | Inter (400-600 weight) |
| Primary accent | `#FF6B00` (orange) |

---

## 3. Architecture — Actor-Based Timeline (NO Scenes)

### The core principle

Think of elements as **characters in a movie**, not slides in a presentation. A text line can be fading out while a mockup is already sliding in. A cursor can be clicking a button while badges are bouncing into view behind it. Nothing waits for anything else.

### Why NOT scenes

Traditional scene wrappers (`<Sequence>` + a scene component) create hard boundaries:
- Elements inside a scene all share the same entrance/exit opacity
- Transitions between scenes feel like "slide changes" no matter how fancy the animations inside
- You can't have element A from "scene 1" overlapping with element B from "scene 2"

In 1600.agency's videos, there are NO hard cuts. Elements flow continuously.

### How it works

Every visual element is an **actor** — an IIFE `(() => { ... })()` inside the single `DistribbExplainer.tsx` component. Each actor:

1. Calls `actor(frame, enterAt, exitAt)` or `actorSpring(frame, enterAt, exitAt)` from `motionUtils.ts`
2. Returns `null` if `!a.visible` (zero rendering cost when off-screen)
3. Uses `a.opacity` for its wrapper opacity (handles enter AND exit fades)
4. Uses `a.localFrame` for internal animation timing
5. Has its own `zIndex`, position, and animation logic

### The Timeline object (`T`)

All enter/exit frame numbers live in a single `T` object at the top of the composition:

```typescript
const T = {
  hookTitle:     { enter: 5,   exit: 90 },
  hookFloaters:  { enter: 15,  exit: 130 },
  hookSubtitle:  { enter: 55,  exit: 130 },
  revealLogo:    { enter: 140, exit: 260 },
  // ... every actor gets its own timing
};
```

**Overlap actors by 15-30 frames** so transitions feel continuous. The hook title exits at 90, but the hook floaters don't exit until 130, and the reveal logo enters at 140 — so there's always something moving.

### The `actor()` and `actorSpring()` functions

```typescript
const a = actor(frame, enterAt, exitAt, enterDuration?, exitDuration?);
// a.visible    — render at all?
// a.opacity    — enterProgress * (1 - exitProgress)
// a.localFrame — frame - enterAt (for internal animations)
// a.entered    — has the enter started?
// a.leaving    — has the exit started?

const a = actorSpring(frame, enterAt, exitAt, exitDuration?);
// Same interface but enter uses snapSpring for bouncy entrance
```

### Actor pattern

```tsx
{(() => {
  const a = actorSpring(frame, T.myElement.enter, T.myElement.exit, 15);
  if (!a.visible) return null;
  return (
    <AbsoluteFill style={{ opacity: a.opacity, zIndex: 12 }}>
      {/* element content */}
    </AbsoluteFill>
  );
})()}
```

### Background layers

Light/dark backgrounds are also actors — their opacity is controlled by `actor()` calls, creating smooth light↔dark transitions without any scene wrapper.

```typescript
const bgLight1 = actor(frame, T.bgLightReveal.enter, T.bgLightReveal.exit, 15, 20);
const bgLightOpacity = Math.max(bgLight1.opacity, bgLightFeat1.opacity, ...);
```

### Narrative flow

| Frames | What's happening |
|--------|-----------------|
| 0-155 | Hook: pain statement text, floating objects, accent underline |
| 130-420 | Reveal: logo, brand name, tagline, dashboard mockup, platform badges |
| 400-850 | Features: 4 feature title+mockup pairs, overlapping transitions |
| 830-1140 | CTA: trust text, logo marquee, badges, CTA button, URL, logo outro |

Note how every section overlaps with the next by 20-30 frames.

---

## 4. The 10 Rules of Agency-Quality Motion Design

These are the patterns extracted from frame-by-frame analysis of 1600.agency's SaaS explainers (Copilot CRM, Upmeet, Zylio, Butterfl.ai, SocialPerf). Every rule must be applied to produce professional output.

### Rule 1: TEXT IS THE HERO

Text should fill 40-70% of the frame during text beats. Use font sizes of 52-76px for headlines, not 30-40px. Words should feel massive and impactful.

```tsx
fontSize: 68,           // NOT 40
fontWeight: 800,
letterSpacing: "-2px",
textShadow: "0 4px 30px rgba(0,0,0,0.4), 0 1px 3px rgba(0,0,0,0.3)",
```

### Rule 2: PER-WORD ACCENT COLORING

Key words are colored in the brand accent while surrounding text stays neutral. This directs the viewer's eye.

```tsx
<span style={{ color: COLORS.accent, textShadow: `0 4px 30px ${COLORS.accentGlowStrong}` }}>
  Autopilot
</span>
```

### Rule 3: FLOATING DECORATIVE OBJECTS

Every text-heavy frame should have 6-10 floating items orbiting the text: emoji icons in rounded-corner cards, text labels ("SEO", "AI"), and abstract shapes. They bob and rotate gently. Use the `FloatingObjects` component.

```tsx
<FloatingObjects
  frame={frame}
  items={[
    { icon: "✍️", angle: 30, radius: 280, size: 48 },
    { text: "SEO", angle: 60, radius: 350, size: 36, color: "rgba(255,255,255,0.06)" },
    { angle: 140, radius: 230, size: 20, color: "#FF6B0015" }, // abstract shape
  ]}
  delay={15}
  orbitSpeed={0.2}
/>
```

### Rule 4: ANIMATED CURSOR

A white cursor moves smoothly between keyframe positions with ease-in-out. It clicks buttons and interacts with UI elements. Click events produce ripple rings. Use the `AnimatedCursor` component.

```tsx
<AnimatedCursor
  frame={frame}
  keyframes={[
    { frame: 0,   x: 600, y: 800 },
    { frame: 40,  x: 540, y: 400 },
    { frame: 80,  x: 480, y: 350, click: true },
  ]}
  delay={85}
/>
```

### Rule 5: HAND-DRAWN ACCENTS

Use SVG strokes that animate on (via strokeDasharray/offset) to circle key words, underline phrases, or point arrows. Use the `HandDrawnAccent` component.

```tsx
<HandDrawnAccent frame={frame} delay={58} type="circle" color="#FF6B00" width={160} height={46} />
<HandDrawnAccent frame={frame} delay={105} type="underline" color="#FF6B00" width={380} />
```

### Rule 6: LIGHT/DARK BACKGROUND ALTERNATION

Never use the same background color for every scene. Alternate between:
- **Dark:** `radial-gradient(ellipse at 50% 35%, #1A2035 0%, #0F1320 40%, #0A0E1A 100%)`
- **Light:** `linear-gradient(160deg, #F8F9FC 0%, #EEF1F7 50%, #E5E9F2 100%)`

Light backgrounds get a subtle grid texture overlay:
```tsx
backgroundImage: `
  linear-gradient(rgba(0,0,0,0.025) 1px, transparent 1px),
  linear-gradient(90deg, rgba(0,0,0,0.025) 1px, transparent 1px)
`,
backgroundSize: "35px 35px",
```

### Rule 7: TEXT-UI SPLIT LAYOUTS

Don't always center everything. Use 50/50 split layouts where text occupies one column and the UI mockup occupies the other. Alternate left/right across features.

```tsx
const FEATURE_LAYOUTS = ["text-top", "split-left", "text-top", "split-right"];
```

### Rule 8: LIVE ANIMATED UI MOCKUPS (Never Static Screenshots)

Product UI should be built as React components with animated elements — not static `<Img>` tags. Each mockup receives a `frame` prop and animates its internal elements (counters, progress bars, rows sliding in, badges bouncing).

Available mockup components:
- `DashboardMockup` — sidebar + stat cards + animated bar chart
- `CalendarMockup` — day grid + article queue with status dots
- `BacklinkMockup` — link rows + SVG DR gauge
- `RedditMockup` — thread cards + comment bubbles
- `SocialMockup` — center article radiating to platform icons

### Rule 9: ICON + TEXT BADGE PATTERNS

Feature callouts use rounded pill badges with colored check icons:

```tsx
<div style={{ display: "flex", alignItems: "center", gap: 6, padding: "6px 14px",
  borderRadius: 20, background: "rgba(255,255,255,0.05)", border: `1px solid ${color}30` }}>
  <div style={{ width: 16, height: 16, borderRadius: "50%", background: color,
    display: "flex", alignItems: "center", justifyContent: "center" }}>
    <span style={{ fontSize: 9, color: "#fff", fontWeight: 700 }}>✓</span>
  </div>
  <span style={{ fontSize: 12, color: "#94A3B8", fontWeight: 500 }}>Feature Name</span>
</div>
```

### Rule 10: CTA WITH CURSOR CLICK + URL TYPEWRITER

The closing scene should have:
1. Trust counter ("500+ Businesses") with logo marquee
2. Feature badges row
3. "Start Your Free Trial" as giant word-by-word text
4. A CTA button ("Get Started Free →") with pulsing glow and cursor approaching/clicking it
5. URL typed out with blinking cursor
6. Logo outro

---

## 5. Reusable Motion Utilities (`motionUtils.ts`)

### Spring Presets

| Preset | Use case | Feel |
|--------|----------|------|
| `snap` | Default entrance, text words | Quick and crisp |
| `bounce` | Cards, UI elements | Slight overshoot |
| `punch` | Logo reveals, impacts | Very fast, aggressive |
| `drift` | Background movements | Slow and smooth |
| `gentle` | Subtle shifts | Soft and natural |

### Actor Functions (NEW — Core of the architecture)

| Function | Signature | Purpose |
|----------|-----------|---------|
| `actor` | `(frame, enterAt, exitAt, enterDur?, exitDur?)` | Linear enter/exit with visibility, opacity, localFrame |
| `actorSpring` | `(frame, enterAt, exitAt, exitDur?)` | Same but enter uses snapSpring for bouncy entrance |

Both return `ActorTiming`: `{ visible, entered, leaving, enterProgress, exitProgress, opacity, localFrame }`

### Animation Functions

| Function | Signature | Purpose |
|----------|-----------|---------|
| `wordByWord` | `(text, frame, delay, stagger)` | Word-by-word text entrance with staggered spring |
| `continuousZoom` | `(frame, startScale, endScale, duration, startFrame)` | Linear camera drift |
| `breathingScale` | `(frame, intensity)` | Subtle sine-wave oscillation |
| `crossFade` | `(frame, sceneEnd, overlap)` | Enter/exit opacity ramps (legacy, use `actor()` instead) |
| `staggeredEntrance` | `(frame, count, delay, stagger)` | Items cascading in |
| `flyExit` | `(frame, exitStart, duration, direction)` | Elements leaving screen |
| `zoomThrough` | `(frame, enterStart, holdDuration)` | Enter → hold → zoom-out-exit |
| `typewriter` | `(text, frame, delay, speed)` | Character-by-character typing |
| `counterAnimation` | `(frame, delay, from, to, duration)` | Animated number counter |

### How to use springs

```tsx
const progress = snapSpring(frame, 20);  // starts at frame 20
const y = interpolate(progress, [0, 1], [30, 0]);
const opacity = interpolate(progress, [0, 1], [0, 1]);
```

---

## 6. Voiceover Pipeline

### Generate voiceover

```bash
cd remotion-videos
python3 generate_voiceover.py
```

This calls ElevenLabs with the script from `config.ts` and produces:
- `public/audio/voiceover.mp3`
- `public/audio/timestamps.json` (word-level `{word, start, end}` array)

### ElevenLabs settings

| Parameter | Value | Notes |
|-----------|-------|-------|
| Voice ID | `pNInz6obpgDQGcFmaJgB` | Adam voice |
| Model | `eleven_v3` | Latest quality |
| Stability | 0.55 | Balanced |
| Similarity Boost | 0.75 | Natural-sounding |
| Style | 0.35 | Moderate expression |

### Enable voiceover in composition

Set `showAudio: true` in `Root.tsx` defaultProps once `voiceover.mp3` exists.

---

## 7. How to Create a New Explainer Video

### Step 1: Copy the template

```bash
cp -r src/DistribbExplainer src/NewVideoName
```

### Step 2: Edit `config.ts`

- Update `COLORS` with new brand palette
- Update `FONT` if different brand fonts
- Rewrite `VOICEOVER_SCRIPT`
- Define new `FEATURES` array
- Update `CLIENT_LOGOS`

### Step 3: Create product mockup components

For each product feature, create a `components/FeatureNameMockup.tsx`:

```tsx
import React from "react";
import { interpolate } from "remotion";
import { COLORS, FONT } from "../config";
import { snapSpring, bounceSpring, counterAnimation } from "../motionUtils";

interface Props { frame: number; }

export const FeatureNameMockup: React.FC<Props> = ({ frame }) => {
  const rowP = snapSpring(frame, 10);
  return (
    <div style={{ width: "100%", height: "100%", background: "#0F1320",
      borderRadius: 12, padding: 16, fontFamily: FONT.body,
      border: `1px solid ${COLORS.cardBorder}`, overflow: "hidden" }}>
      {/* Animated UI elements here */}
    </div>
  );
};
```

Key rules for mockups:
- Accept `frame: number` as the only prop
- Use `snapSpring`/`bounceSpring` with staggered delays for each element
- Use `counterAnimation` for numbers
- Use `interpolate` for progress bars and gauge fills
- Never use static images — build everything with divs and inline styles

### Step 4: Define the timeline in `DistribbExplainer.tsx`

Create a `T` (timeline) object with enter/exit frames for every actor:

```typescript
const T = {
  hookTitle:   { enter: 5,   exit: 90 },
  hookSub:     { enter: 55,  exit: 130 },
  revealLogo:  { enter: 140, exit: 260 },
  feat0Title:  { enter: 400, exit: 500 },
  feat0Mockup: { enter: 415, exit: 520 },
  // ... one entry per visual element
};
```

Then write each element as an actor IIFE:

```tsx
{(() => {
  const a = actorSpring(frame, T.hookTitle.enter, T.hookTitle.exit, 15);
  if (!a.visible) return null;
  return (
    <AbsoluteFill style={{ opacity: a.opacity, zIndex: 10 }}>
      {/* title content */}
    </AbsoluteFill>
  );
})()}
```

**Never wrap actors in scene components or `<Sequence>` blocks.**

### Step 5: Register in Root.tsx

```tsx
<Composition
  id="NewVideoName"
  component={NewVideo}
  durationInFrames={TOTAL_DURATION}
  fps={30}
  width={1080}
  height={1350}
  schema={videoSchema}
  defaultProps={{ showAudio: false }}
/>
```

### Step 6: Generate voiceover

Update `generate_voiceover.py` with the new script, then run:
```bash
python3 generate_voiceover.py
```

### Step 7: Render

```bash
npx remotion render src/index.ts NewVideoName out/new-video.mp4
```

---

## 8. Design Tokens Quick Reference

### Colors

```typescript
bg:              "#0A0E1A"       // Dark background base
accent:          "#FF6B00"       // Primary orange
accentGlow:      "rgba(255, 107, 0, 0.12)"  // Soft glow
accentGlowStrong:"rgba(255, 107, 0, 0.25)"  // Medium glow
accentGlowHot:   "rgba(255, 107, 0, 0.4)"   // Bright glow
white:           "#FFFFFF"
textSecondary:   "#94A3B8"       // Body text on dark
textMuted:       "#64748B"       // De-emphasized text
cardBg:          "rgba(255, 255, 255, 0.04)" // Subtle card fill
cardBorder:      "rgba(255, 255, 255, 0.08)" // Subtle card border
green:           "#22C55E"       // SEO/published
purple:          "#6366F1"       // Backlinks
reddit:          "#FF4500"       // Reddit
blue:            "#0EA5E9"       // Social
```

### Light background text colors

```typescript
textOnLight:     "#1A1A2E"       // Headings on light bg
subtextOnLight:  "#64748B"       // Body on light bg
```

### Backgrounds

```typescript
// Dark scene
`radial-gradient(ellipse at 50% 35%, #1A2035 0%, #0F1320 40%, #0A0E1A 100%)`

// Light scene
`linear-gradient(160deg, #F8F9FC 0%, #EEF1F7 50%, #E5E9F2 100%)`
```

### Text shadow (dark backgrounds only)

```typescript
textShadow: "0 4px 30px rgba(0,0,0,0.4), 0 1px 3px rgba(0,0,0,0.3)"
```

### Glow effect behind elements

```tsx
<div style={{
  position: "absolute",
  width: 500, height: 500, borderRadius: "50%",
  background: `radial-gradient(circle, ${COLORS.accentGlowHot} 0%, ${COLORS.accentGlow} 35%, transparent 65%)`,
  top: "50%", left: "50%",
  transform: "translate(-50%, -50%)",
  filter: "blur(60px)",
  opacity: 0.6,
}} />
```

---

## 9. Common Patterns

### Word-by-word title entrance

```tsx
const titleWords = wordByWord("Your Title Here", frame, 5, 4);
// ...
{titleWords.map((w, i) => (
  <span key={i} style={{
    fontFamily: FONT.heading, fontSize: 68, fontWeight: 800,
    color: COLORS.white, letterSpacing: "-2px",
    opacity: w.opacity,
    transform: `translateY(${w.y}px) scale(${w.scale})`,
    display: "inline-block",
    textShadow: "0 4px 30px rgba(0,0,0,0.4)",
  }}>
    {w.word}
  </span>
))}
```

### Browser chrome frame for UI mockups

```tsx
<div style={{ height: 26, background: "rgba(30,35,50,0.95)",
  display: "flex", alignItems: "center", padding: "0 12px", gap: 6 }}>
  {["#FF5F56","#FFBD2E","#27C93F"].map(c => (
    <div key={c} style={{ width: 7, height: 7, borderRadius: "50%", background: c }} />
  ))}
  <div style={{ flex: 1, textAlign: "center", fontFamily: FONT.body,
    fontSize: 9, color: COLORS.textMuted }}>
    app.yoursite.com/dashboard
  </div>
</div>
```

### Actor enter/exit (replaces manual opacity math)

```tsx
const a = actorSpring(frame, 140, 260, 15);
if (!a.visible) return null;
// a.opacity handles both enter and exit automatically
// a.localFrame gives you time since enter for internal animations
```

### Logo marquee (infinite scroll)

```tsx
const marqueeOffset = (frame * 1.5) % totalWidth;
<div style={{ display: "flex", gap: 35, transform: `translateX(-${marqueeOffset}px)`, width: "200%" }}>
  {[...logos, ...logos, ...logos].map((logo, i) => (
    <Img key={i} src={staticFile(logo)}
      style={{ height: 26, filter: "brightness(0) invert(1)", opacity: 0.45, flexShrink: 0 }} />
  ))}
</div>
```

### Pulsing glow button

```tsx
boxShadow: `0 0 ${20 + Math.sin(frame * 0.1) * 10}px ${COLORS.accentGlowStrong}`
```

---

## 10. Anti-Patterns (What NOT to Do)

| Don't | Do instead |
|-------|------------|
| **Wrap elements in scene components** | Every element is an independent actor in one flat file |
| **Use `<Sequence>` to group elements** | Use `actor()` / `actorSpring()` for per-element timing |
| **Wait for one element to finish before starting the next** | Overlap enter/exit by 15-30 frames |
| Use static `<Img>` for product features | Build animated React mockup components |
| Keep text small (30-40px) | Use 52-76px for headlines |
| Use the same dark background everywhere | Alternate light/dark via background layer opacity |
| Center everything vertically | Use split layouts (text left, UI right) |
| Skip cursor interactions | Add AnimatedCursor clicking buttons/UI |
| Use flat unstyled text | Add textShadow, accent coloring, hand-drawn accents |
| Show empty frames with just one element | Always have 3-5 actors visible simultaneously |
| Use long crossfade transitions | Use fast spring-based transitions (15 frames max) |
| Use the same entry direction for every element | Alternate left/right/scale/bottom entries |
| Leave backgrounds static | Add breathingScale and continuousZoom |

---

## 10b. CaptionedTalkingHead — talking-head MP4 + word captions + PiP b-roll

**Exception:** This composition intentionally composites **real `<Video>`** layers (main + optional B-roll), not the actor-only `DistribbExplainer` pattern. Use `<Sequence>`-free layout inside a single component; timing comes from **ASR word timestamps**, not a `T` frame map.

| Piece | Location |
|--------|----------|
| Composition | `src/CaptionedTalkingHead.tsx` (Zod `captionedTalkingHeadSchema`) |
| Layout helpers | `src/captionLayout.ts` |
| Main footage | `public/source/main.mp4` (gitignored — copy your MP4 here) |
| B-roll clips | `public/broll/*.mp4`, referenced in `bRollClips` props |
| Full props from Groq words JSON | `python3 remotion-videos/build_caption_props.py` — set **`CAPTION_WORDS_JSON`**, optional **`CAPTION_MAIN_VIDEO_PUBLIC_PATH`**, optional **`CAPTION_BROLL_JSON`** (manifest path, see below) → **`public/render-props.json`** |

**B-roll manifest:** JSON object with **`bRollClips`** array (or a bare JSON array). Each item: **`src`** (path under `public/`, e.g. `broll/screen-source.mp4`), **`startSec`** / **`durationSec`** (when and how long PiP shows on the **main edit** timeline), **`srcStartSec`** (optional, default `0`) — trim into the B-roll file so **one long screen recording** can power multiple PiP windows without splitting files. Optional **`xPct`**, **`yPct`**, **`widthPct`**, **`cornerRadiusPx`**, **`borderOpacity`** for layout.

Example shipped for the Claude SEO backlinks tutorial: **`remotion-videos/broll_manifest.claude-seo-tutorial.json`** plus **`public/broll/screen-source.mp4`** (copy the original full-length screen capture; gitignored).

**Studio:** `cd remotion-videos && npx remotion studio` → composition **`CaptionedTalkingHead`**.

**Render:**

```bash
cd remotion-videos
npx remotion render src/index.ts CaptionedTalkingHead out/captioned.mp4 --props="$(pwd)/public/render-props.json"
```

If **`esbuild` / `package.json` timeouts** occur (Google Drive sync), sync **`remotion-videos/`** to **`/tmp/`** (excluding **`node_modules`**), run **`npm ci`**, and render from there.

**Caption design:** Distribb orange accent `#FF6B2C`, pill tokens, spring pop on active word, dim previous line, bottom readability gradient.

**Remotion license:** See skill / [remotion.pro/license](https://remotion.pro/license) for commercial use.

---

## 11. Iteration Checklist

Before considering a video "done", verify:

**Architecture:**
- [ ] Single flat composition — NO scene wrapper components, NO `<Sequence>` grouping
- [ ] Every visual element uses `actor()` or `actorSpring()` for its own timing
- [ ] Timeline object (`T`) at the top defines all enter/exit frames
- [ ] Adjacent actors overlap by at least 15 frames for continuous flow
- [ ] Every actor returns `null` when `!a.visible` for zero rendering cost

**Visual quality:**
- [ ] Every text-heavy beat has floating decorative objects
- [ ] Key words are accent-colored, not all-white
- [ ] Text fills at least 40% of the frame during text beats
- [ ] At least 2 feature sections use a light background
- [ ] At least 2 features use split (text|UI) layout
- [ ] AnimatedCursor appears in at least 2 sections
- [ ] HandDrawnAccent (circle or underline) appears at least twice
- [ ] All UI is animated React components, not screenshots
- [ ] CTA section has: trust counter, badges, button with cursor, URL typewriter
- [ ] breathingScale applied to the root container
- [ ] continuousZoom (Ken Burns drift) on every mockup display
- [ ] No beat lasts longer than 4 seconds without visual change
- [ ] Playing the video shows continuous motion — no frame ever feels "static" or "waiting"
