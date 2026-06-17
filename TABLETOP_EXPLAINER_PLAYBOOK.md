# Tabletop "Levels-of-X" Explainer — Playbook

How to BUILD (from scratch) a calm, tactile 9:16 explainer that constructs a tiered idea one
physical layer at a time: a fictional talking-head presenter alternating with overhead
handcrafted-tabletop b-roll (a drawn pyramid + colored tier stickies, paper cut-out icons, a
radial card wheel, physical DNA/molecule models, a closing texture), real screenshot receipts,
and a flat animated flow diagram — under a soft orchestral bed and minimalist word-locked
captions. Recipe id: `tabletop-levels-explainer`. Engine scripts: `workflows/tabletop-levels-explainer/`.

This format wins by *earning trust through construction*: the viewer watches the idea get
physically assembled, layer by layer. It is the opposite of fast UGC energy — keep it measured.

## 0. When to use
Any "there are N levels/stages of X" concept where the payload is a hierarchy: levels of AI,
stages of a process, tiers of a market, a maturity model, a pyramid of needs. If the idea is a
ladder, this format makes it tangible.

## 1. Script = a ladder (write it first)
- **Hook (<=4s, presenter):** "There are N stages of X, and most people only know level one."
- **Tiers 1..N (alternate presenter + craft reveal):** one beat per tier, lowest -> highest. Each
  tier adds one physical sticker to the pyramid and/or shows a supporting prop.
- **Proof receipts:** real screenshots that the frontier is real/contested.
- **Stakes/consequence:** what the top tier unlocks (a fast montage of concrete examples).
- **Closing question (b-roll):** a provocative either/or that lingers.
Calm delivery, ~2-3.4 words/sec. Author `storyboard.json` (one row/beat: t0,t1, layout, job,
vo, caption, prop) so every cut lands on a sentence break.

## 2. The presenter — a DISTINCT fictional creator (no likeness cloning)
1. Source a royalty-free/licensed photo in the target staging (warm cozy room, podcast condenser
   mic in the lower-center foreground, light crew-neck). Pexels works; the photo is only for
   photographic realism.
2. Transform identity with gpt-image-2 (`tools/image_provider.py edit` or `openai_image_tool.py
   --reference-image`, quality=high, 1024x1536) into a NEW person in that exact staging. Prompt:
   "a NEW fictional woman, distinct new face (NOT the reference person), natural blonde hair,
   light blue-grey crew-neck, large dark condenser mic in the lower-center foreground, warm
   lamp-lit bokeh, looking directly at the camera, photorealistic, shot on Sony FX3 50mm, natural
   skin texture, no logos, no text." Save `assets/character/character_hero.png`.
3. Split the script into sentence-aligned chunks of `<=~12s` of speech (each fits one Seedance
   clip). Author `chunks.json`.
4. Generate each chunk with **Seedance reference-to-video + native audio** (the chunk dialogue
   lives in the prompt). **Lock the voice:** run chunk A first, extract a clean 4s WAV from it, and
   pass that as `--reference-audio` to every later chunk (rules 44a/44b). One `--seed`.
5. Whisper every clip; concatenate -> the continuous VO bed + a global word-time map that every
   cut and caption locks to (`whisper_timeline.py`).

> The concatenated presenter audio IS the continuous narration. You show the presenter only during
> talking-head beats; during craft beats you cover the video with b-roll while that same audio
> keeps playing. No external TTS required — and lip-sync stays perfect.

## 3. Craft b-roll — first-frame + last-frame steering
The signature texture. For each craft beat:
1. Make a gpt-image-2 **first frame** and **last frame** (the before/after of the prop). Overhead
   on dark walnut wood, warm tungsten, shallow DoF, real hands implied.
2. `gen_craft_clip.py` runs `fal_seedance_video.py --mode image --reference-image FIRST
   --reference-image LAST` (two images => `image_url` first + `end_image_url` last). The motion
   prompt describes the in-between action ("a hand draws the pyramid and presses the yellow LLM
   sticky onto the base tier"); Seedance fills realistic hand-craft motion.
3. **Keep the building pyramid consistent** by chain-editing ONE base image: blank sketchbook ->
   +tier1 sticky -> +tier2 -> +tier3 -> +apex, each a gpt-image-2 edit of the previous frame. Then
   each pyramid clip is `Pn -> P(n+1)`.

Supporting props that read well: paper cut-out app/idea icons, a radial wheel of ~20 index cards,
a plate of tiny symbolic objects (flask=scientist, note=artist, pawn=strategist), physical
DNA/molecule ball-and-stick models, a paper sun + paper city skyline, a closing street-art wall.
Match the platform's native res (720x1280 for IG/TikTok); it's cheaper and looks 1:1.

## 4. Receipts + diagram
- **Receipts:** real screenshots of the actual sources via `capture_receipts.py` (Playwright
  channel=chrome). Ken Burns push-in to the named phrase. Real beats generated every time.
- **Flow diagram:** a flat 2D animated graphic built as `diagram.html` with **paused** CSS
  keyframes, captured frame-accurate by `capture_anim.py` (it scrubs `getAnimations().currentTime`
  per frame). No AI-slop glow; flat icons + arrows + a token/checkmark reveal.

## 5. Assemble + caption + music
- `assemble.py` builds a **switched** timeline: presenter during talking beats, b-roll during craft
  beats, every boundary from `overlay_schedule.json` windows (derived from the global word times),
  with the continuous VO underneath. Missing craft clips auto-fall back to their last-frame still
  (Ken Burns) so a draft always renders.
- `build_captions.py` -> minimalist word-locked ASS (small white sans, 2-3 word groups, lower
  third, keyword color).
- Music: a soft orchestral underscore (strings + piano, slow swell, slightly ominous toward the
  closing question). Generate via ElevenLabs Music / Suno / Replicate; **if those are out of
  credit, drop a royalty-free/CC track** at `assets/music/orchestral_bed.wav`. `finalize.py` ducks
  it under the VO (sidechaincompress) and loudnorm's to `I=-16:TP=-1.5:LRA=11`, burning captions.

## 6. Gotchas (learned the hard way)
- **fal `--mode image` first+last:** TWO `--reference-image` => `image_url` (first) +
  `end_image_url` (last). This is the steering lever; the prompt only describes the motion.
- **zoompan on stills:** use `d=1` with a frame-rate-limited single image
  (`-loop 1 -r FPS -t DUR ... -frames:v N`). `-loop 1 -t` with `d=DUR*FPS` MULTIPLIES frames and
  explodes the duration.
- **`openai_image_tool.py` lowercases + hyphenates `--output-prefix`** (`P0_blank` -> `p0-blank-*`).
  Detect new files by dir-diff, not prefix glob.
- **ElevenLabs/Replicate out of credit?** Voice -> Seedance-native audio (rule 44b). Music ->
  royalty-free/CC. Never block the whole job on one credit-locked provider.
- **Keys** live in the app `.env` (point `SVM_ENV_DIR` at it), not necessarily the skill `.env`.

## 7. Compliance
The presenter must be a distinct fictional creator — a royalty-free photo may seed realism, but
transform identity so no real person is recreated, and never imply a real person's endorsement.
Prefer REAL screenshots for proof; generated craft is an approximation of physical craft, never a
substitute for a real source.
