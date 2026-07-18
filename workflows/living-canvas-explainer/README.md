# living-canvas-explainer — workflow assets

Boutique-grade single-canvas SaaS explainer. **Read `LIVING_CANVAS_PLAYBOOK.md`
at the skill root first** — it contains the full grammar (pacing numbers,
camera state machine, causal-mechanics catalog, audio system, failure modes).
This directory holds the reusable implementation assets.

## Files

- `motion-library.tsx` — the complete, production-tested helper + component
  library (springs, actor system, camRig with creep + velocity-blur dead zone,
  rank-sort slot system, settle micro-bounce, WordPop kinetic type with
  pov/scatter/strike modes, Sharp Tag badges, all FX layers: RingPulse,
  GlowSweep, HeatFlare, Embers, Flash, Sparks, Streaks, Ambient, GloveHand,
  Cursor, ghost titles, grid/blob backgrounds). Copy into a Remotion 4 project;
  adapt the `C` color constants + `FONT` stack to the client brand.

## Build order for a new video

1. **VO first** — script → TTS (expressive model + audio tags for the story
   half, announcer read for the pitch half) → silence surgery → Whisper word
   timestamps → `wordAt(t) = round(t*30)` becomes the `T` timeline object.
2. **Skeleton** — one flat composition; per section: background world value,
   ghost title, persistent card, camera keys (wide → punch → extraction →
   pull-back), exit whip.
3. **Choreography pass** — one distinct causal mechanic per beat (catalog §11
   of the playbook); reflow physics on every list/collision; 1-2
   transformation chains on the top handoffs.
4. **FX + SFX pass** — rings/sweeps/fire/embers on the payoff frames; build
   the 30-60 event SFX bus from the playbook's mapping table.
5. **Probe-QC loop** — `npx remotion still` at every critical frame, read the
   images, fix. Only then full render (`--concurrency=4 --timeout=120000`).
6. **Mix in FFmpeg** — 4 stems (VO splice, bed, score, SFX), static-EQ carve
   (never sidechain), `loudnorm I=-16:TP=-1.5:LRA=11`, `-c:v copy`.

## Timing quick card (30fps)

| Move | Frames |
|---|---|
| Word pop | 8-12/word, stagger = word timestamps |
| Entrance settle | 6-12 (oversized 1.3-1.4x → 1.0, ~5% overshoot) |
| Commit punch | 6-9 (1.3-1.4x, centered on sub-region) |
| Extraction punch | 18-24 (1.66-2.2x) |
| Whip exit | 6-9 + heavy directional blur |
| Micro-bounce settle | `1 + e^(-l/7)·sin(l/1.9)·0.035` after l=8 |
| Shuffle displacement | slot spring d13/s200, blur `|Δy|·0.55` cap 6px |
| Ring pulse | 22 · fires within 2-4 fr of its punch |
| Transformation chain | ~40-48 total (gather 15 → flick 4 → orbit 11 → collapse 7 → burst+birth 11) |
| Hold ceiling | 105 (with 1-6%/s creep always running) |
