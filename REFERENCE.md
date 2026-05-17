# Super Video Maker Reference

Use this file for provider decisions, capabilities, and constraints. Keep
`SKILL.md` focused; read this file when planning a real video job.

## Core production modes

| Mode | Best for | Primary tools |
|---|---|---|
| Avatar Explainer (`avatar-explainer`) | Proof-driven news/tutorial videos with avatar narration, source receipts, screen recordings, UI micro-stories, captions, and action takeaways | HeyGen, browser recorder, OpenAI images/UI stills, FFmpeg |
| Avatar-led | Presenter, educational videos, product intros, CTAs | HeyGen, FFmpeg, Remotion |
| Agent-operated browser tutorial | News, research, proof-driven explainers | agent browser recorder, HeyGen, FFmpeg |
| Screencast demo | SaaS demos, tutorials, walkthroughs | screen recorder, demo composer, FFmpeg |
| Faceless ad | UGC-style ads, b-roll, hooks, kinetic captions | Seedance, OpenAI images, captions, FFmpeg |
| Motion graphics | Explainers, launch videos, UI mockups | Remotion or HyperFrames |
| Repurposing | Long video to shorts, clips, captions | video captioner, FFmpeg, Remotion |

## Default storytelling pattern

Use this structure unless the user asks for something simpler:

1. **Hook:** say why the update matters.
2. **Transparency:** if the presenter is synthetic, say so immediately after the hook.
3. **News beat:** describe the change.
4. **Story/example:** show a concrete situation, such as a founder, publisher, or site owner affected by the change.
5. **Source proof:** show browser footage or screenshots that verify the claim.
6. **Action step:** give the viewer a practical next move (3 numbered moves on the outro card works well).
7. **Spoken CTA tail (6-8s):** the avatar speaks a follow CTA over the outro recap card so the video has a natural ending instead of a silent end-card.

Do not copy Kurzgesagt, The Infographics Show, or any named channel. The
acceptable direction is original educational-explainer energy: symbolic scenes,
clean shapes, strong contrast, simple metaphors, and fast pacing.

## Editorial taste system

The editor's first question is not "what image matches this word?" It is:

> What state change should the viewer understand at this exact sentence?

Every visual must have one clear job:

| Visual job | Meaning | Good examples | Bad examples |
|---|---|---|---|
| Proof | This is real | Official headline, byline/date, exact paragraph crop, outlet cluster | Same hero page reused as wallpaper |
| Mechanism | This is how it works | Cursor hover -> action card, UI before/after, step-by-step screen event | Generic laptop/hand/AI brain |
| Consequence | This is why it matters | Founder workflow gets automated, traffic/reporting surface changes, citation flow changes | Abstract "importance" montage |
| Action | This is what to do | Checklist, UI audit, search query, dashboard filter, calendar action | Motivational stock footage |
| Transition | We are moving to the next idea | Match cut, chapter chip, quick headline montage, split-screen bridge | Decorative gradient or random b-roll |

If a shot cannot be labeled as one of those, cut it before generation.

### Surface-first story beats

For story/example narration, avoid showing the affected person as the default.
Show the surface where the change happens:

| Narration type | Better surface | Why |
|---|---|---|
| "Founder lives in Google Docs" | A believable Google Docs-style launch plan full of comments, TODOs, dates, screenshots, pasted chart | Shows the workspace where the agent will act |
| "Cursor becomes Gemini" | Same document before/after: inert cursor -> contextual action menu | Shows the mechanism, not the metaphor |
| "AI answers decide citations" | SERP/AI answer surface with cited sources highlighted | Shows the distribution surface |
| "Design content for ambient AI" | Split screen: article content block -> AI answer / widget / sidebar excerpt | Shows how content travels |
| "Audit visibility" | Spreadsheet/dashboard with queries and cited/not-cited status | Shows the action step |
| "Everyone covered it" | Headline wall or Techmeme/outlet stack with source labels | Shows momentum without repeating the official source |

The useful pattern is:

```text
Narration -> Surface -> Before state -> Cursor/action -> After state -> Viewer takeaway
```

Example:

```text
Narration: "Picture this. You're a founder who lives in Google Docs all day."
Surface: Google Docs-style launch plan.
Before state: messy doc with TODOs, comments, "Launch date: Friday 2:00 PM",
image thumbnails, pasted chart, "Need pricing page screenshots".
Action: cursor scans the document; date highlights; action card appears.
After state: "Schedule launch review?" and "Create launch graphic?" cards appear.
Reject: stock founder photo, hand on laptop, glowing AI icon, same Google source page.
```

This is the difference between low-effort b-roll and modern fancy editing:
the viewer sees the exact workflow changing.

## Source deck and screenshot grammar

Before editing a news/explainer video, build a source deck. A source deck is a
small manifest of screenshots/screen-recordings where each item has a unique
role. Do not start timeline assembly until each major claim has an asset.

Recommended source deck for a product/news explainer:

| Asset | Job | Example use |
|---|---|---|
| Official announcement hero | Proof | Establish the story is real |
| Byline/date crop | Proof | Show who published it and when |
| Exact paragraph crop | Proof | Highlight "Android + ChromeOS + Gemini" |
| Feature section crop | Mechanism | Show "Magic Pointer" or the actual UI section |
| Product screenshot / media asset | Mechanism | Show what the feature looks like |
| Coverage aggregator | Consequence | Prove "covered by 40+ outlets" |
| Headline wall | Consequence / transition | Fast montage of 4-6 outlet headlines |
| Action UI / checklist | Action | Turn the news into what the viewer should do |

Rules:

- One website can appear multiple times only if every appearance proves a
  different fact. "Same page, slightly different zoom" is a failure.
- A second crop of the same page must change one of: source role, visible
  phrase, crop target, motion direction, annotation, or layout.
- Use full-page establishing shots for 1-2 seconds, then move to precision
  proof: exact phrase crop, callout box, byline/date, source label.
- Use screenshots as receipts, not wallpaper. Receipts should have source
  name, date, and the exact highlighted claim.

### Better usage for the Googlebook example

Instead of returning to the Google Keyword hero repeatedly:

| Narration | Visual |
|---|---|
| "Google killed the Chromebook brand" | Motion card: `Chromebook -> Googlebook`, then official headline receipt |
| "Unified Android plus ChromeOS" | Exact paragraph crop with the phrase highlighted |
| "Gemini built directly into the OS" | "Designed for Gemini Intelligence" section, not the hero again |
| "Magic Pointer" | Actual Magic Pointer section plus cursor hover annotation |
| "The Verge, Wired, Engadget..." | Headline wall / Techmeme cluster, not the Google page |
| "Three moves this week" | Action UI cards: audit visibility, design ambient surfaces, try Gemini agents |

### Source repetition budget

For a 60-100s master:

- Official source hero: max 1 establishing shot.
- Same official page again: max 2 additional precision crops.
- Aggregator page: max 1 establishing shot + 1 tight crop.
- Any screenshot held longer than 6 seconds must split into new crops or
  alternate with a different texture.
- If the viewer could say "I already saw this page," the shot probably needs a
  new annotation, a new crop, or replacement.

## B-roll layout QC and edit loop

Generated b-roll, UI cards, proof screenshots, and Ken Burns clips must pass a
composition review before the final master. This is a required taste gate,
separate from technical FFmpeg QC.

Run:

```bash
python3 .agents/skills/super-video-maker/tools/broll_layout_qc.py \
  tmp/video_jobs/<job_id>/assets/v5_clips/*.mp4 \
  --job-dir tmp/video_jobs/<job_id>
```

The tool extracts representative frames, overlays visual guides, creates a
contact sheet, and emits `RESULT` JSON. The guides show:

- outer safe margin,
- top-right avatar PiP reserved zone,
- bottom caption band,
- center crosshair.

Review checklist:

| Check | Why it matters | Fix |
|---|---|---|
| Important subject/text is under PiP | PiP will hide the point of the shot | Move subject left/down, change crop, or move PiP for that beat |
| Important subject/text is in caption band | Captions will collide with it | Raise/crop content, simplify card, or use split layout |
| Text feels cramped | Cheap/generic look | Increase margins, reduce copy, use fewer elements |
| Edge tangents / clipped UI | Looks accidental | Reframe with more breathing room |
| Main subject too centered under captions | Weak composition | Move subject to upper-left/center-left safe area |
| Visual job unclear | Filler | Rewrite asset as proof/mechanism/consequence/action/transition |

Disposition labels:

- `pass`: safe for master composition.
- `crop-edit`: use FFmpeg crop/zoom/x/y expression changes.
- `layout-edit`: edit the still/card/mockup with Pillow, Remotion, or HTML.
- `re-render`: prompt/image/video needs regeneration with explicit spacing.
- `replace`: the concept is wrong; choose a better visual.

Preferred fix order:

1. **Crop/reframe**: adjust `scale`, `crop`, `zoompan`, `x_expr`, `y_expr`.
2. **Layout edit**: move elements, reduce copy, add margins, resize cards.
3. **Prompt edit and re-render**: specify subject placement and empty space.
4. **Replace**: choose a different surface/asset if the visual job is weak.

Prompt/layout instructions for future generated stills:

```text
16:9 frame, subject placed in the center-left safe area, generous negative
space in the top-right for an avatar PiP overlay, no important text or faces in
the bottom 20% caption band, clean margins, no cropped hands/faces, no cramped
UI, editorial composition with breathing room.
```

For UI cards:

- Keep primary headline inside the left/center safe area.
- Reserve top-right for PiP if the avatar will be visible.
- Reserve bottom ~170px for captions.
- Use fewer words; prefer 3 bullets max.
- Leave at least 90px margin from all edges.

## Layout zones (1920x1080 master)

The single biggest visual bug in our v1 masters was overlay collisions
(captions, lower-third, and PiP all in the bottom band). Treat these zones as
mutually exclusive in space-and-time:

| Zone | Element | Coordinates | Time window |
|---|---|---|---|
| Top-left | Disclosure badge (PNG) | `x=50, y=50` (~360x60 pill) | Hook only, ~0.5–4.5s, fade out before PiP appears |
| Top-right | Borderless avatar PiP with rounded corners + soft drop shadow | `x=W-pip_w-50, y=50` (1378,50 for 492x276) | All non-fullscreen beats |
| Center | B-roll / browser proof / fullscreen avatar | full frame minus reserved zones | Per storyboard |
| Bottom band (last ~140px) | Karaoke captions | `Alignment=2, MarginV=90, MarginL=MarginR=80` | Whole timeline |
| Outro card | Action steps + permanent disclosure footer | full frame | After action close, plays under spoken CTA tail |

Rules:
- If captions are bottom-centered, the avatar PiP **must** be top-right (never bottom-right).
- Disclosure badge fades out before the avatar PiP appears, so they never share the top-right corner.
- During the outro CTA tail, hide the avatar PiP and let the recap card own the frame.

## Disclosure badge (Pillow PNG, top-left)

Render once with Pillow into `assets/disclosure_badge.png`:

```python
from PIL import Image, ImageDraw, ImageFont
W, H = 420, 80
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle((10, 10, W-10, H-10), radius=22,
                    fill=(10, 18, 40, 245),         # dark navy
                    outline=(255, 107, 44, 235),    # brand orange
                    width=2)
d.ellipse((30, H/2-8, 46, H/2+8), fill=(255, 107, 44, 255))  # accent dot
font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 22)
d.text((58, H/2-13), "Digital avatar of <name>", fill=(255, 255, 255, 255), font=font)
img.save("assets/disclosure_badge.png")
```

Overlay with FFmpeg during the hook only:

```text
[bg][badge]overlay=50:50:enable='between(t,0.5,4.5)'
```

This replaces the heavy `drawbox` lower-third we used in v1 jobs and is the
default for any branded chip, badge, or callout.

## Avatar PiP styling (borderless, rounded, drop shadow)

The avatar PiP must look like a floating modern card, not a hard-bordered
TV-news lower-third. Render two reusable PNG assets once per job and reuse
them across every PiP overlay:

```python
# build_pip_assets.py
from PIL import Image, ImageDraw, ImageFilter
W, H, R = 492, 276, 24

mask = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(mask).rounded_rectangle(
    (0, 0, W - 1, H - 1), radius=R, fill=(255, 255, 255, 255)
)
mask.save("assets/pip_mask.png")

# Shadow: same shape, padded with 32px halo, blurred
SH_PAD = 32
SW, SH = W + SH_PAD * 2, H + SH_PAD * 2
shadow = Image.new("RGBA", (SW, SH), (0, 0, 0, 0))
ImageDraw.Draw(shadow).rounded_rectangle(
    (SH_PAD, SH_PAD, SW - SH_PAD - 1, SH_PAD + H - 1),
    radius=R + 4, fill=(0, 0, 0, 180),
)
shadow = shadow.filter(ImageFilter.GaussianBlur(radius=14))
shadow.save("assets/pip_shadow.png")
```

FFmpeg compose with rounded corners + drop shadow (top-right placement at
`PX=1378, PY=50`, shadow offset `+4, +16`):

```bash
ffmpeg -y \
  -i background.mp4 \
  -i avatar_green.mp4 \
  -i assets/pip_mask.png \
  -i assets/pip_shadow.png \
  -filter_complex "\
[1:v]chromakey=0x00ff00:0.18:0.08,scale=492:276,format=rgba[av];\
[2:v]format=rgba[mask];\
[av][mask]alphamerge[avr];\
[3:v]format=rgba[sh];\
[0:v][sh]overlay=x=1378-32+4:y=50-32+16:enable='between(t,15.8,77.8)'[bg2];\
[bg2][avr]overlay=x=1378:y=50:enable='between(t,15.8,77.8)':format=auto[v]" \
  -map "[v]" -map 0:a? \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a copy with_pip.mp4
```

Why these defaults:

- 24px corner radius matches modern UI conventions (Notion, Linear, Vercel).
- Shadow is wider than the PiP by 32px on each side, blurred at sigma 14,
  alpha 180 → reads as soft and natural, not hard-edged.
- Offset `+4 / +16` simulates a single overhead light source, the same
  direction as a typical UI elevation shadow.
- No colored border. The rounded crop alone gives the PiP a card feel; the
  border would add visual noise next to clean centered captions.
- During the outro CTA tail, the PiP is hidden via the `enable=` clause so
  the recap card owns the frame.

## HeyGen

Use HeyGen when the video needs a human face, digital twin, talking avatar,
photo avatar, or lip-synced presenter.

Capabilities:

- public avatars, photo avatars, and custom instant avatars,
- text-to-video using HeyGen voices,
- cloned/custom voices when configured,
- green-screen background for later chroma-key compositing,
- 16:9 or 9:16 avatar outputs depending on account support.

Default package tool:

```bash
python3 .agents/skills/super-video-maker/tools/heygen_client.py
```

Recommended composition pattern:

1. Select the avatar by exact name or ID.
2. Select the voice deliberately. If no voice is passed, match voice name to avatar name first.
3. Generate the avatar clip.
4. Use the avatar clip's own audio as narration in the final render.
5. Place avatar over screen recording, AI b-roll, or Remotion scene.
6. Add captions and music last.

Important lesson: HeyGen avatars and voices are separate. A selected avatar does
not guarantee the matching voice. If the avatar API returns `default_voice_id:
null`, query voices and choose the matching voice by name.

## Seedance 2.0 via Replicate

Use Seedance for short generated b-roll, product-inspired visuals, drone-style
clips, cinematic inserts, or stylized UGC footage.

Default:

```bash
python3 .agents/skills/super-video-maker/tools/replicate_video.py generate \
  --prompt "slow dolly-in shot of a founder using a laptop in a modern office, cinematic" \
  --duration 7 \
  --resolution 1080p \
  --aspect-ratio 16:9
```

Prompting guidance:

- Lead with camera movement.
- Name subject, environment, lighting, and lens feel.
- Keep prompts under about 80 words.
- For reference images, say what each reference controls.
- For educational b-roll, use original metaphors: citation networks, helpful-content labs, source constellations, traffic flow maps.
- Avoid "in the style of" named channels. Describe the visual language instead.
- If Replicate returns insufficient credit or throttling, do not keep retrying aggressively. Use local animated b-roll as a temporary fallback, or wait for credits.

## Agent-operated browser recording

Use this for news/tutorial footage where the screen must support what the avatar
is saying.

Best practices:

- Preload and clean pages before recording if ad/CAPTCHA risk is high.
- Prefer source pages over search-result pages in final footage.
- Show active investigation: tab switching, cursor jumps, callout highlights, find-on-page searches, fast scroll-to-target, exact-phrase zooms, byline/date receipt overlays, and corroborating tab switches.
- Avoid blank pages, CAPTCHA pages, large ads, cookie modals, newsletter popups, and unrelated AI tools unless the narration explicitly discusses them.
- Align segments to narration beats. A typical 55-70s video needs 4-6 source/visual beats.
- Use browser footage for proof and b-roll/screenshot scenes for storytelling examples.
- Never record slow scrolling as filler. Every recording event should reveal a new fact, source, quote, feature, or action.

Good proof-recording pattern:

```text
1. Open official post.
2. Cursor jumps to headline.
3. Thin rounded callout highlights the headline.
4. Find-on-page search for the feature name.
5. Browser jumps to the exact section.
6. Cursor highlights the relevant paragraph.
7. Tab switch to aggregator / outlet list.
8. Fast scroll to the headline cluster.
9. Zoom into source list.
10. Source receipt card appears: source, date, claim.
```

Bad pattern:

```text
Open one page -> slow scroll -> same page later with a different zoom -> slow scroll again.
```

Permanent tool:

```bash
python3 .agents/skills/super-video-maker/tools/agent_browser_recorder.py
```

The tool should create one `RESULT:` JSON line with recording and events paths.

## ByteDance direct

ByteDance direct is optional. Use it only when the user has configured direct
access and it is cheaper after subscription or volume thresholds. The skill
should treat it as a provider adapter behind the same b-roll interface as
Replicate.

## OpenAI image generation and editing

Use OpenAI image generation/editing for:

- thumbnails,
- scene stills,
- storyboard frames,
- background plates,
- product mockups,
- image cleanup,
- visual continuity edits,
- **b-roll fallback when Seedance is throttled or out of credit** (generate a still and animate with FFmpeg Ken Burns).

The package should route image work through `tools/image_provider.py` so future
model names and endpoint details can change without rewriting the skill.

### B-roll design system: choose by beat purpose, prefer real over generated

Most "AI slop" comes from defaulting to generative b-roll for every beat. Pick
the visual *category* by what the narration is doing in that moment, then pick
the actual asset within that category.

| Beat purpose | First choice | Second | Third (generated as last resort) |
|---|---|---|---|
| News beat — "here's what changed" | Real screenshot of the official announcement (blog post, product page) → Ken Burns | Editorial photo of the company/founder/event | Documentary-realism Ken Burns (see below) |
| Source proof | Agent-operated browser recording of the source page | Real screenshot of the source page → Ken Burns | (never generated — proof must be real) |
| Story / example — "a founder doing X" | Real stock footage of a person doing X (Pexels/Pixabay) | Editorial photo of a real person + Ken Burns | Documentary-realism Ken Burns |
| Concept / metaphor | Typographic "pull-quote" card with a real quote + attribution | Real object photo (a single specific thing) + Ken Burns | Documentary-realism Ken Burns of an analog scene |
| Aggregate / momentum — "everyone is talking" | Techmeme/HN/Trends screenshot → Ken Burns | Photo of newspaper headlines on a desk | Documentary-realism Ken Burns |
| Action step | Real UI screenshot + drawn-arrow overlay | Real stock footage of a hand doing the step | Documentary-realism Ken Burns |
| Statistic / number | Animated typography card (one number, large, on a clean background) | Real chart screenshot | (never generated — numbers should be sourced) |

Rules:

- A 60-90s master should mix **at least 3 distinct visual textures**
  (editorial photo Ken Burns, real stock-footage handheld clip, typographic
  pull-quote card). Sameness reads as AI.
- Two consecutive clips must NOT share the same dominant color or
  composition. Documentary edits feel real because every clip looks
  different.
- Stock footage providers: Pexels (free API), Pixabay (free API), Coverr
  (free, no API), Unsplash for stills. Build a `pexels_search.py` or
  `pixabay_search.py` adapter and route stock requests through it.
- For typographic pull-quote cards, use a clean editorial layout (one bold
  quote, attribution line in smaller weight, optional small metadata strip)
  on a neutral background — not on a dark cosmic backdrop.

### OpenAI image model defaults

- **Model:** `gpt-image-2` (snapshot `gpt-image-2-2026-04-21` as of mid-2026). State-of-the-art, recommended for any new build. `gpt-image-1` is legacy.
- **Quality:** `high`. Always pass it explicitly — the API default is `auto` and can pick `medium`, which loses skin-texture/depth detail on documentary photos.
- **Size:** `2048x1152` for all full-frame stills. This is **exact 16:9**, both edges multiples of 16, well within the 655K–8.3M pixel budget. Eliminates letterbox padding when composited onto a 1920x1080 timeline.
- **Permitted size exceptions:** `1024x1024` for branded icons/badges; `1024x1536` for vertical portraits going into a 9:16 short.
- **Output format:** `png` for stills consumed by Ken Burns (lossless, alpha not needed); `webp` quality 90 for web thumbnails.

### Documentary-realism prompt pattern (when generated b-roll is the last resort)

Use this when you must generate a clip and no real visual exists. The goal is
to look like a frame from a real documentary, not a Pixar-meets-cyberpunk
montage.

Recommended prompt pattern:

```
<one specific real-world scene with a real human or real object as subject>.
Documentary photography, editorial style. Natural <window/morning/golden-hour/overcast>
light from a believable source. 35mm or 50mm photographic feel, shallow depth
of field, real environment with believable clutter and texture. Candid moment,
no posing. Color grade <warm domestic / cool corporate / neutral documentary>
matched to mood. No logos, no on-screen text, no glow effects, no floating
subjects, no cosmic backgrounds, no neon, no orange-and-teal Hollywood grade.
Shot on Sony FX3 / Canon R5 aesthetic. 16:9 cinematic.
```

Hard prompt prohibitions (these always trigger AI slop):

- "cosmic / cyberspace / neon grid / glowing particles / data streams /
  neural network",
- "floating" subjects (laptops, icons, devices in a void without a
  grounding plane),
- logo glyphs or brand marks of any kind (Android robot, Chrome ball, app
  icons, company logos),
- "magic / ethereal / volumetric light rays" cyber-fantasy vocabulary,
- the orange-and-teal Hollywood gradient as the entire palette,
- symbolic visualization of abstract concepts (a "data constellation", a
  "merge of two operating systems", an "AI brain").

Vary framing across clips (close-up macro, medium portrait, wide
environmental) so the cut feels like a real edit, not a montage of one-style
renders.

### FFmpeg Ken Burns recipe

Recommended FFmpeg `zoompan` (oversample to 2x target, scale-to-fill +
centre-crop so non-16:9 sources still cover the full frame, then downscale
through `zoompan` to 1920x1080 so the zoom stays clean):

```bash
ffmpeg -y -loop 1 -i still.png \
  -vf "scale=3840:2160:flags=lanczos:force_original_aspect_ratio=increase,\
crop=3840:2160,setsar=1,\
zoompan=z='min(zoom+0.000556,1.10)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30,\
trim=duration=6.0,setpts=PTS-STARTPTS,format=yuv420p" \
  -t 6.0 -an -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p out.mp4
```

Notes:

- `force_original_aspect_ratio=increase` + `crop=3840:2160` is the **default** for any non-16:9 source. Never default to `pad=...:color=...` for documentary photos — letterbox bars look amateur on photographic content.
- Tune `0.000556` to match the desired zoom rate for your duration: it equals `(z_end - 1.0) / (duration_seconds * fps - 1)` where `z_end` is the final zoom factor. Use `1.10` for a subtle 6 s push-in; `1.18-1.22` for short 2-3 s cuts so each cut still has visible motion.
- For long beats, generate 2-3 separate Ken Burns clips of different crops (different `x_expr`/`y_expr`) and concat — never hold one zoom for >3.5 s on AI-generated stills.

## Remotion

Use Remotion when the video needs React components, stateful props, reusable
mockups, captions based on JSON, or a real browser preview/editor.

Best fit:

- product explainers,
- captioned talking-head + b-roll,
- animated UI mockups,
- platform variant rendering from one prop file.

Key package files:

- `REMOTION_VIDEO_GUIDE.md`
- `remotion-template/README.md`
- `remotion-template/src/CaptionedTalkingHead.tsx`
- `remotion-template/src/captionLayout.ts`

Basic commands:

```bash
cd .agents/skills/super-video-maker/remotion-template
npm install
npx remotion studio
npx remotion render src/index.ts CaptionedTalkingHead out/captioned.mp4 --props=public/render-props.json
```

## HyperFrames

Use HyperFrames when an agent can define the video as HTML. It is strong for
deterministic rendering, agent-generated compositions, GSAP/Lottie/CSS motion,
and browser preview without inventing a custom timeline format.

Basic commands:

```bash
cd .agents/skills/super-video-maker/hyperframes-template
npm install
npx hyperframes preview compositions/demo.html
npx hyperframes render compositions/demo.html --output out/demo.mp4
```

## Captions and transcripts

Use `video_captioner.py` for:

- extracting audio,
- Whisper transcription,
- word-level timestamps,
- ASS subtitle generation,
- burned-in captions,
- vertical short exports.

For high-stakes captions:

- transcribe once,
- review the transcript,
- generate captions from reviewed words,
- burn captions only after timing and spelling are acceptable.

## Music and voice

Use ElevenLabs for voiceover and as the preferred first music provider when the
account supports music generation. Use Replicate music models or Suno through
adapters when configured.

Music workflow:

1. Decide mood, tempo, and intensity.
2. Generate or select music.
3. Trim or loop to video length.
4. Duck under voiceover.
5. Normalize final loudness.

## FFmpeg role

FFmpeg is the final assembly and repair tool. Use it to:

- remove green screen,
- compose picture-in-picture,
- scale/pad/crop platform variants,
- burn subtitles,
- mix voice/music/SFX,
- normalize loudness,
- concatenate clips,
- probe output health.

Read `FFMPEG_PLAYBOOK.md` before writing custom FFmpeg commands.

## Suggested fallback order

| Need | First choice | Fallback |
|---|---|---|
| Avatar presenter | HeyGen | static presenter card + voiceover |
| News-beat visual | Real screenshot of the announcement → Ken Burns | Editorial photo + Ken Burns |
| Source-proof visual | Agent-operated browser recording | Real screenshot → Ken Burns |
| Story/example visual | Pexels/Pixabay real stock footage | Editorial photo + Ken Burns, then documentary-realism generated |
| Concept/metaphor visual | Typographic pull-quote card | Real object photo + Ken Burns |
| Generated b-roll (last resort) | Documentary-realism Seedance | Documentary-realism `gpt-image-2` high-quality still + Ken Burns, then `local_explainer_broll.py` |
| Image insert | OpenAI image generation | stock image, screenshot, SVG |
| Motion graphics | Remotion | HyperFrames |
| HTML-native ad | HyperFrames | Remotion |
| Music | ElevenLabs Music | Replicate music, Suno adapter |
| Captions | Whisper + ASS | Remotion captions from word JSON |
| Avoid b-roll loop in long beat | Companion clip from same provider | `tpad=stop_mode=clone` freeze (≤2s) or Ken Burns still |

## Public package safety

Do not include:

- `.env`,
- API keys,
- cookies,
- generated private videos,
- screen recordings,
- local absolute paths,
- client logos or private brand assets unless they are examples.

Use `.env.example` or documentation for required environment variables.
