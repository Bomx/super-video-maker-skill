# Motion Collage Explainer Style (SOP)

The recipe behind the `motion-collage-explainer` format: a bold, screen-print
**cutout collage** still (built with OpenAI `gpt-image-2`) that is then brought to
life with **Seedance 2.0 through fal.ai** and narrated in a calm **documentary
"explainer" voice** in the spirit of channels like Kurzgesagt ("In a Nutshell").

Read this before building any collage-style short. It defines the look, the
image prompt formula, the animation rules, the narration voice, and the QC bar.

---

## 1. When to use this style

Use it for **one-idea explainer shorts**: a single concept, idiom, mental model,
or "why does X happen" question, delivered in 20 to 45 seconds, 9:16 (Shorts /
Reels / TikTok) or 16:9. It is the opposite of a talking head. There is no
presenter and no screen recording. The whole video is one living illustrated
collage per beat, plus a warm explainer voiceover.

Good fits:
- A named concept made concrete ("bikeshedding", "glass jaw", "drowning in a glass of water").
- "Here is a simple question... here is the surprising answer."
- A mental model or analogy for a product/SEO/finance/science idea.

Not for: source-proof journalism, UGC ads, SaaS screen demos, or anything that
needs real screenshots as evidence (route those to `avatar-explainer`,
`ugc-ai-ad`, or `screencast-demo`).

---

## 2. The look, precisely

Every frame is a **flat screen-print / risograph collage**. Lock these traits so
all beats feel like one series:

- **Background:** one saturated flat color per video (cobalt blue, brick red,
  mustard, forest green, ink navy). No gradients, no vignette. Optional faint
  paper/newsprint grain.
- **Subject:** a **black-and-white halftone cutout** (vintage editorial photo,
  visible halftone dots / newsprint texture), treated as a **paper sticker**:
  thin white die-cut outline, slightly rough torn edge, soft drop shadow so it
  sits *above* the background. Grayscale subject against the colored field is the
  signature contrast.
- **The concept is literal and a little surreal.** Illustrate the phrase, do not
  decorate it. "Glass jaw" = a boxer taking a hit at the jaw with a comic starburst.
  "Drowning in a glass of water" = a tiny suited man flailing inside a wine glass.
- **Accent shapes:** 2 to 4 flat geometric cutouts in a tight palette (cream circle
  "sun", solid navy triangle, black zigzag, small star, scattered dots, ink
  splashes). Placed with intent around the subject, never centered clutter.
- **Caption label:** a **torn-paper strip** near the bottom carrying the concept in
  **bold condensed UPPERCASE** (newspaper / letterpress cutout feel). This is the
  poster title, kept short (1 to 4 words).
- **Palette discipline:** background + grayscale subject + at most 3 accent colors.
  Matte, printed, tactile. No neon, no glow, no 3D, no gradients.

**Reference the attached style samples' vibe, never their pixels.** Do not pass any
existing brand's frames as image references; generate the collage from the prompt.

---

## 3. Build the still with `gpt-image-2`

Use the skill-local image tool (equivalent to the repo-root `openai_image_tool.py`;
both call `gpt-image-2`):

```bash
python3 .agents/skills/super-video-maker/tools/image_provider.py generate \
  --prompt "@collage_prompt" \
  --size 1024x1536 \
  --quality high \
  --output-format png
```

Sizes: **`1024x1536`** for 9:16 Shorts (portrait), **`1536x1024`** or `2048x1152`
for 16:9. Generate the poster still first, approve it, then animate.

### Prompt formula (fill every slot)

```text
Flat screen-print collage poster, single saturated <COLOR> background, subtle
newsprint grain. Centerpiece: a black-and-white halftone cutout of <SUBJECT DOING
THE LITERAL CONCEPT>, treated as a paper sticker with a thin white die-cut outline,
slightly torn edges, and a soft drop shadow so it floats above the background.
Visible halftone dot texture, vintage editorial photo feel, grayscale subject.
Accent cutouts: <2-4 flat shapes, e.g. a cream circle top-left, a solid navy
triangle bottom-right, a small black zigzag, a few scattered dots>. A torn-paper
label near the bottom with the words "<CONCEPT PHRASE>" in bold condensed uppercase
newspaper type. Matte printed risograph aesthetic, limited palette (background +
grayscale subject + 2-3 accent colors). Composition leaves headroom at the top and
a clear band at the bottom for the label. No gradients, no glow, no neon, no 3D
render, no photorealism, no lens flare, no modern UI, no extra text.
```

Anti-AI-slop guardrails (append as explicit "avoid" clauses, `gpt-image-2` has no
negative-prompt field): avoid glossy 3D, avoid glowing/neon, avoid dark cosmic,
avoid floating-in-a-void, avoid gradient backgrounds, avoid photoreal color subject,
avoid watermark, avoid garbled label text. If the label text renders garbled,
regenerate with a shorter phrase or burn the label in post with Pillow/FFmpeg
instead of trusting the model's typography.

Generate **one poster per beat** if the video has multiple concepts, keeping the
same background color, texture, outline weight, and label style across all beats so
the set reads as one series.

---

## 4. Animate the still with Seedance 2.0 (fal.ai)

Bring the poster to life as a **living collage**, not a re-imagined scene. Use
`image-to-video` so Seedance animates the exact still you approved:

```bash
python3 .agents/skills/super-video-maker/tools/fal_seedance_video.py generate \
  --mode image \
  --reference-image output_images/collage_beat1.png \
  --prompt "@motion_prompt" \
  --duration 5 \
  --resolution 1080p \
  --aspect-ratio 9:16
```

Use `--mode reference` instead when you want several clips to share the collage
style/character across beats (pass the poster(s) as `--reference-image`, reuse the
same `--seed`).

### Motion prompt rules

Keep motion **small, physical, and looping-safe**. The collage should breathe:

```text
Subtle living-collage motion. The paper cutout gently bobs and has a soft parallax
against the flat background. Accent shapes drift and rotate slightly. <ONE literal
motion tied to the concept: water ripples and a droplet falls / the starburst
pulses on impact / the little figure flails>. Faint halftone shimmer, gentle slow
push-in. Everything stays a flat printed collage, paper texture preserved. No new
objects appear, no camera whip, no realistic 3D, no scene change, no morphing faces,
no added text.
```

Constraints:
- **Do not let Seedance repaint the still into a realistic scene.** Prompt for
  motion of the existing paper elements only. If it "realifies" the subject or
  changes the composition, lower motion, tighten the prompt, or switch to a
  FFmpeg Ken Burns + shape-parallax fallback on the static PNG.
- **One dominant motion per beat.** Living-collage, not chaos.
- **Duration 4 to 6s per beat.** Concat beats on sentence boundaries.
- **Loop-safe:** hold the final frame with `tpad` for short overflows rather than
  visibly looping the clip (SKILL rule 21).
- **Audio off** on the Seedance clip (`--no-generate-audio`, the default). The
  voice is a separate ElevenLabs track.

---

## 5. The narration ("In a Nutshell" documentary voice)

The visual is playful; the **voice is calm, warm, and curious** like a science
explainer. This contrast is the whole format.

Script shape (20 to 45s):
- **Open on a simple question or vivid scenario.** "Ever been in a meeting where
  everyone argues for an hour... about the color of a button?"
- **Name the concept.** "That is bikeshedding."
- **Explain the mechanism with one analogy.** Short sentences. One idea at a time.
- **Land the takeaway / why it matters.** One sentence the viewer keeps.
- **Soft CTA** if the video is for a channel ("More mental models every week.").

Voice rules:
- Second person, present tense, conversational but precise.
- Short sentences. One clause each. Let the VO breathe over the visual.
- Curiosity, not hype. No ad-speak, no hard sell.
- **No em dashes** in the script; use commas and periods.
- Ground any real claim; do not invent statistics for an explainer.

Produce the VO with ElevenLabs (`tools/music_provider.py` handles music; use the
project's voice for narration), Whisper-transcribe it for word-level timing, and
**beat-lock every collage cut to the sentence breaks** (SKILL rules 14, 23).

---

## 6. Assemble

1. One approved collage poster per beat, each animated to a 4 to 6s Seedance clip.
2. Concatenate clips on sentence boundaries (`tools/video_orchestrator.py` / FFmpeg).
3. Lay the ElevenLabs VO under the whole thing; optional soft music bed low in the mix.
4. **Captions:** bold, centered, 2 to 3 word karaoke groups (SKILL rule 17). The
   collage label is the poster title; the karaoke captions carry the spoken words.
   Keep captions out of the torn-paper label band.
5. Loudness-normalize to `I=-16:TP=-1.5:LRA=11` (SKILL rule 18).
6. Export 9:16 master first (`1080x1920`), plus 16:9 if requested.

---

## 7. QC bar

- Every frame still reads as a **flat printed collage** (Seedance did not realify it).
- Consistent background color, outline weight, and label style across all beats.
- No AI-slop tells: no glow, neon, dark cosmic, floating-in-void, 3D, gradient.
- Label text is legible (or was re-burned in post); no garbled model typography.
- Motion is subtle and loop-safe; no visible clip loop snap, no morphing faces.
- VO is calm/explainer, captions synced to Whisper word timing, sit clear of the label.
- `yuv420p` `h264` `aac`, correct resolution, no black frames at joins (run `ffmpeg_qc.py`).

---

## 8. One-idea run, end to end

```bash
# 1) Poster still (9:16)
python3 .agents/skills/super-video-maker/tools/image_provider.py generate \
  --prompt "@collage_prompt" --size 1024x1536 --quality high --output-format png

# 2) Animate the approved still
python3 .agents/skills/super-video-maker/tools/fal_seedance_video.py generate \
  --mode image --reference-image output_images/collage_beat1.png \
  --prompt "@motion_prompt" --duration 5 --resolution 1080p --aspect-ratio 9:16

# 3) VO + captions + concat + loudnorm  -> final/vertical_9x16.mp4
python3 .agents/skills/super-video-maker/tools/video_captioner.py   # captions
python3 .agents/skills/super-video-maker/tools/ffmpeg_qc.py         # QC gate
```

For the SEO-and-publish wrapper (keyword-led title, description, tags, publish to a
connected YouTube channel), this style is driven end to end by the Distribb skill's
**`/youtube-motion-video`** playbook.
