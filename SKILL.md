---
name: super-video-maker
description: |
  End-to-end AI video production skill for agentic frameworks. Use when the
  user asks to make, edit, repurpose, caption, soundtrack, or export videos
  using HeyGen avatars, Seedance or ByteDance b-roll, OpenAI image generation
  and editing, Remotion, HyperFrames, screen recordings, FFmpeg, captions,
  ElevenLabs music, Suno, or social-video variants.
metadata:
  requires:
    env:
      - HEYGEN_API_KEY
      - HEYGEN_AVATAR_ID
      - REPLICATE_API_TOKEN
      - OPENAI_API_KEY
      - ELEVENLABS_API_KEY
---

# Super Video Maker

## What this skill does

Turns a video idea, script, product flow, screen recording, avatar brief, or
existing long-form video into polished video assets. The skill can produce:

- **Avatar Explainers** (`avatar-explainer`): proof-driven avatar videos with a synthetic presenter, screen recordings/source receipts, UI micro-stories, captions, and action takeaways,
- avatar videos with HeyGen,
- AI b-roll with Seedance 2.0 through Replicate,
- generated or edited images with OpenAI image models,
- screen recordings with cursor/event logs,
- motion graphics in Remotion or HyperFrames,
- captions, subtitles, music, and final FFmpeg exports.

## Read these files when needed

- `REFERENCE.md` for provider capabilities and routing decisions.
- `FFMPEG_PLAYBOOK.md` for exact FFmpeg recipes.
- `WORKFLOW_EXAMPLES.md` for full production examples.
- `REMOTION_VIDEO_GUIDE.md` for Remotion motion-design rules.

## Operating rules

1. **Run a staged pipeline, not random tool calls.** Use: intake -> script/shot list -> assets -> assembly -> FFmpeg finishing -> QC -> exports.
2. **Confirm paid generation before the first paid call.** Show planned providers, number of clips/images, duration, resolution, and likely cost drivers.
3. **Prefer skill-local tools.** Use files in `tools/` before reaching for project-root scripts.
4. **Every tool should emit `RESULT: {...}`.** Parse that JSON as the source of truth.
5. **Keep job state.** Put each run in `tmp/video_jobs/<job_id>/` with `job_state.json`, inputs, intermediates, and final exports.
6. **Do not delete intermediate assets until QC passes.** Failed video jobs are easier to fix when the raw clips still exist.
7. **Never commit secrets or user sessions.** Do not publish `.env`, cookies, generated recordings, private avatars, or downloaded user videos.
8. **Make errors user-friendly.** Hide raw stack traces from end users, but save detailed logs for debugging.
9. **Default to story-first videos.** Do not make plain news slideshows. Use: hook -> transparent avatar intro -> news beat -> concrete story/example -> source proof -> action step.
9a. **Use `avatar-explainer` as the default recipe name** for the format combining HeyGen avatar narration, screen recordings/source receipts, UI micro-stories, b-roll, captions, and action takeaways.
10. **Disclose synthetic presenters via the avatar's own voice.** Bake the line "Quick note, this is the digital avatar of <name>" into the script right after the hook. Do NOT prepend a static disclaimer card. If the disclosure is missing from the audio, fall back to a small **transparent rounded-pill PNG badge in the top-left corner** during the first ~4 seconds (Pillow-rendered: dark navy fill `#0A1228` at 96% alpha, 2px brand-orange `#FF6B2C` outline, 16px accent dot, white sans-serif "Digital avatar of <name>", 22px corner radius, 50px from each edge). Never use a heavy `drawbox` lower-third in the bottom band — it collides with centered captions. Always include a permanent footer line on the outro card: "Digital avatar of <name>. <domain>".
11. **Match HeyGen avatar and voice deliberately.** Avatar and voice are separate IDs. If no voice is explicitly provided, first try to match the voice name to the selected avatar name before falling back.
12. **Screen recordings should look like investigation, not scrolling wallpaper.** Browser proof should show the agent verifying the claim: open the source, jump to the headline, highlight the exact phrase, use find-on-page for the feature name, scroll to the relevant paragraph, switch tabs to corroborating coverage, and zoom into the evidence. Avoid static pages, random wandering, repeated hero crops, ads, CAPTCHAs, cookie modals, and slow scrolling that does not reveal new information.
13. **Use b-roll as visual explanation, not decoration.** For every sentence, ask: "What surface changes because of this idea?" Do not match nouns with generic imagery ("founder" -> person at laptop). Show the environment where the change happens: a Google Doc, calendar, SERP, analytics dashboard, Slack thread, CMS editor, browser tab, or product UI with before/action/after states. Avoid copying any existing YouTube channel style; use original modern editorial motion, UI micro-stories, source receipts, and clean annotations.
14. **Beat-lock every visual to the narration.** Always Whisper-transcribe the avatar audio (word-level timestamps) and pin every screen change, b-roll cut, caption, and lower-third to the actual seconds the words appear. Never overlay visuals against assumed timing.
15. **Detect HeyGen script duplication.** Some HeyGen renders unexpectedly repeat the script. After download, compare the Whisper segments and trim the master to the first unique pass before composing.
16. **Build a visual hierarchy with non-colliding zones and a borderless PiP.** Avatar fullscreen for the hook beat. Avatar picture-in-picture for every other beat: **borderless, 24px rounded corners, soft drop shadow** — never a colored hard frame. Implementation: Pillow renders `pip_mask.png` (rounded-rectangle alpha mask) and `pip_shadow.png` (blurred dark shape) once per job; FFmpeg uses `chromakey -> scale -> alphamerge` to round the avatar's corners, then composites the shadow at offset `+4, +16` underneath. Default size 492x276 on a 1920x1080 master. **PiP corner adapts to caption alignment:** if captions are bottom-centered (default), put the PiP in the **top-right** at `x=W-pip_w-50, y=50`. Never place the PiP in the same band as the captions, and hide the PiP entirely during the outro CTA tail so the recap card owns the frame. Skip the static title card; open directly on the avatar fullscreen. Keep an outro recap card at the end with the action steps and a permanent disclosure footer.
17. **Burn karaoke captions centered at the bottom.** Bold uppercase Arial Black ~64px, 2-3 word groups with the active word highlighted in yellow, white drop shadow + 5px outline. ASS style: `Alignment=2` (bottom-center), equal `MarginL=MarginR=80`, `MarginV=90`. Generate from the Whisper word JSON with the master offset applied. Do NOT default to lower-left — left-aligned captions look amateur and clash with disclosure overlays.
18. **Loudness-normalize the master audio** to `I=-16:TP=-1.5:LRA=11` so the upload is broadcast-safe across YouTube, LinkedIn, X, and podcasts.
19. **When Replicate Seedance is throttled or out of credit**, fall back in this order: (a) real source screenshots, UI mockups, stock footage, or typographic cards that directly explain the beat; (b) OpenAI `gpt-image-2` stills at `quality=high`, native 16:9 (`2048x1152`) + FFmpeg Ken Burns with scale-to-fill/crop; (c) `local_explainer_broll.py` only when it can render an actual UI/event/state change. Never fall back to abstract dark-cosmic, glowing, floating, or symbolic "AI" imagery.
20. **Recover long HeyGen jobs by `video_id` instead of regenerating.** If the local poll times out, query the existing HeyGen job and download when complete to avoid double-charging credits.
21. **Never loop b-roll inside a long beat.** If a Whisper-aligned beat is longer than the clip, either (a) generate a complementary b-roll for the second half, (b) hold the final frame with `tpad=stop_mode=clone:stop_duration=N` for overflows up to ~2 seconds, or (c) cross-cut with a Ken Burns still. A visible loop snap is more disorienting than a brief held frame.
22. **Choose b-roll by beat purpose, not by prompt creativity. Prefer real over generated, always.** B-roll is decided by what the narration is doing in that moment, not by what is "cool to generate". Use this routing:
    - **News beat ("here's what changed"):** real screenshot of the announcement (official blog, product page, release post) → Ken Burns. Beats any generated render.
    - **Source proof:** agent-operated browser footage or a real screenshot of the proof page. Never replace this with generated b-roll.
    - **Story/example ("a founder doing X"):** real stock footage of a real person doing the thing (Pexels/Pixabay) > editorial photo + Ken Burns > generated only as last resort.
    - **Concept/metaphor:** prefer a typographic "pull-quote" card or a single real object photo over an abstract symbolic render.
    - **Aggregate/momentum ("everyone is talking"):** screenshot of Techmeme/Trends/HN with Ken Burns, or a photo of newspaper headlines on a desk, not a "data constellation" render.
    - **Action step:** real UI screenshot with a drawn arrow/highlight overlay, or a real hand performing the step. Not glowing icons in space.
    Generated b-roll (Seedance, OpenAI Ken Burns) is the **last** option in every category, only chosen when no real visual exists for that beat.
23. **Land every cut on a sentence break.** Whisper segments are the source of truth. The visual should change on the gap between sentences, never mid-phrase, so each beat reads as one inevitable "image + thought" pairing.
24. **Plan layout zones before composing — overlapping overlays is the #1 visual bug.** Before any FFmpeg overlay, decide which zone each element occupies and ensure they never share the same screen region at the same time. Default zone map for 1920x1080 with bottom-centered captions:
    - **Top-left (50,50):** disclosure badge during hook only (fades by ~4.5s).
    - **Top-right (1378,50):** avatar PiP (492x276) during all non-fullscreen beats.
    - **Center:** b-roll, browser proof, or fullscreen avatar.
    - **Bottom band (last ~140px):** karaoke captions only.
    - **Outro card:** permanent disclosure footer in the bottom-center, action steps in the middle.
    If two elements ever share a zone, redesign one of them or stagger their `enable=` time windows.
25. **Always end with a spoken CTA tail, never a silent outro.** Extend the avatar script with a 6-8s CTA after the action close (e.g. "If this is useful, hit follow at <domain> for more <topic>. See you in the next one."). Re-Whisper the new audio and let the **outro recap card stay on screen for the duration of the spoken CTA**, with the PiP hidden during this final stretch so attention lands on the action steps. A silent end card kills retention and looks unfinished.
26. **Pillow PNG overlays beat `drawbox` lower-thirds for any branded element.** Generate the badge, lower-third, chip, or button as a transparent PNG with Pillow (`Image.new("RGBA", (W,H), (0,0,0,0))`, `ImageDraw.rounded_rectangle`, anti-aliased text), then overlay with `[bg][badge]overlay=x:y:enable='between(t,t0,t1)'`. PNGs render with proper anti-aliasing, sub-pixel rounding, and transparent edges; `drawbox` produces hard-edged blocks that look amateur next to professional captions and PiPs.
27. **Reject AI-slop b-roll aesthetics by default.** When a generated clip is the only option, the prompt MUST NOT contain any of these AI-slop tells:
    - "dark cosmic / cyberspace / neon grid / glowing particles / data streams / neural network",
    - "floating" subjects (laptops, icons, glyphs, devices in a void with no grounding plane),
    - logo glyphs or brand marks of any kind (Android robot, Chrome ball, app icons, company logos — both copyright unsafe and instantly reads as AI),
    - "magic / ethereal / ethereal blue / volumetric light rays" cyber-fantasy vocabulary,
    - the orange/teal "Hollywood look" gradient as the entire palette,
    - symbolic visualization of abstract concepts (a "data constellation", a "merge of two operating systems", an "AI brain") — these always look generated.
    Instead, force the prompt into **documentary-realism** territory: a real human in a real environment doing a real action, natural light from a believable source, 35mm or 50mm photographic feel, shallow depth of field, editorial color grade matched to the mood (warm domestic, cool corporate, neutral documentary). Specific vocabulary that helps: "documentary photography", "editorial portrait", "natural window light", "shot on Sony FX3" (or similar), "shallow depth of field", "real environment", "candid moment". Vary the framing across clips (close-up macro, medium portrait, wide environmental) so the cut feels like a real edit, not a montage of one-style renders.
28. **Vary the b-roll aesthetic per clip — sameness reads as AI.** Pick at least three distinct visual textures across a 60-90s master (e.g. one editorial-photo Ken Burns, one stock-footage handheld clip, one typographic pull-quote card), and avoid two consecutive clips that share the same dominant color or composition. "One unified visual language" applies to brand cards/badges/captions, NOT to b-roll content. Documentary edits feel real because every clip looks different.
29. **Default OpenAI image generation to `gpt-image-2` at `quality=high`, native 16:9 sizes.** Use `2048x1152` (exact 16:9, both edges multiples of 16) for all documentary-realism photos and any other still that will appear full-frame in the master. Never default to `1024x1024` or `1536x1024` — those force letterbox padding when composited onto a 1920x1080 timeline. Permitted exceptions: branded icons/badges (`1024x1024`), portraits-only verticals (`1024x1536`).
30. **Scale b-roll with fit-to-fill + centre-crop, never pad-with-color.** Ken Burns and any image-to-video helper must use `scale=W*2:H*2:force_original_aspect_ratio=increase,crop=W*2:H*2` so the source covers the full frame and the slight content loss happens at the edges. Padding bars (`pad=W:H:...:color=#0F1320` etc.) are reserved for a deliberate cinematic letterbox look only — they are NOT a default, and they look amateur on documentary photos.
31. **Cut every 2-4 seconds on AI static images, every 3-6 seconds on real screenshots.** No single AI-generated still should hold the screen for more than ~3.5 s. Long beats (>5 s) MUST split into 2-3 cuts of different photos, different crops of the same screenshot, or alternating photo/screenshot/card textures. Holding a single AI photo for 5+ seconds advertises that it is generated; cutting fast keeps the documentary feel.
32. **Assign every visual one editorial job.** Every shot must be labeled in the storyboard as exactly one of: **Proof** ("this is real"), **Mechanism** ("this is how it works"), **Consequence** ("this is why it matters"), **Action** ("this is what to do"), or **Transition** ("we are moving to the next idea"). If a shot has no job, it is filler and must be cut. If two consecutive shots have the same job and use the same source, the second must prove a different detail or be replaced.
33. **Build a source deck before editing any news/explainer video.** Gather distinct source assets with unique roles before timeline assembly: official announcement hero, exact paragraph crop, feature section crop, product/UI image, byline/date crop, coverage aggregator, headline stack, and action-relevant UI. Do not reuse one website hero as generic wallpaper. The same website may appear multiple times only if each appearance answers a different question.
34. **Use screenshots and screen recordings as evidence, not background texture.** A screenshot must prove a specific sentence: headline, byline/date, exact phrase, feature UI, outlet list, number, quote, or action step. Screen recordings must have events: cursor jump, find-on-page search, scroll to target, phrase highlight, tab switch, source receipt overlay, or split-screen comparison. Slow scrolling without a new revealed fact is banned.
35. **For story/example beats, show the working surface where the change happens.** Do not show the affected person unless their expression/body language is the point. For "a founder lives in Google Docs," show a believable Google Docs-style launch plan with comments, TODOs, dates, image thumbnails, a pasted chart, and cursor-driven action cards. The visual should move through: before state -> cursor/action -> useful after state.
36. **Use modern editorial motion language.** Prefer fast UI inserts, source receipt cards, thin rounded callout boxes, cursor-driven reveals, split screens, headline montages, match cuts, before/after UI, and tight push-ins to exact phrases. Avoid generic stock people, repeated website zooms, slow Ken Burns-only sequences, decorative gradients, and any shot that merely "feels related" without explaining the sentence.
37. **Run a b-roll layout QC/edit pass before final composition.** Generated images, UI cards, screenshots, and video b-roll are not approved just because they rendered. Before composing the master, run `tools/broll_layout_qc.py` on every b-roll asset to create guided review frames/contact sheets with safe-margin, caption-band, and avatar-PiP overlays. Open/read those frames and mark each asset as `pass`, `crop-edit`, `layout-edit`, `re-render`, or `replace`. Fail any asset where important text/faces are under the PiP, key content is in the caption band, typography feels cramped, spacing is off, edge tangents are awkward, or the visual job is unclear.
38. **Fix b-roll layout problems in the cheapest order.** First crop/reframe (`scale-to-fill`, `crop`, `x_expr/y_expr`, zoompan start/end), then edit the layout/still (Pillow/Remotion/HTML), then re-render with a corrected prompt, then replace the shot. Do not accept "almost right" generated b-roll if spacing is obviously wrong; spacing/composition errors are taste errors.

## Standard workflow

### Stage 1: Intake

Collect:

- target platform: YouTube, TikTok, Reels, Shorts, ads, landing page, course, demo,
- output aspect ratios: `16:9`, `9:16`, `1:1`, `4:5`,
- desired duration,
- source assets,
- brand style,
- call to action,
- whether the user wants avatar, faceless, screencast, or hybrid.

Return a concise plan before generation.

### Stage 2: Script and shot list

Create:

- spoken script,
- visual shot list,
- source deck (each source asset has one unique editorial job),
- visual job labels for every shot: proof / mechanism / consequence / action / transition,
- b-roll prompts,
- on-screen text,
- caption style,
- music mood,
- export targets.

Script shape:

- Hook (first 5-6 seconds): why the viewer should care, in one breath.
- Casual avatar disclosure (one short clause, immediately after the hook, in the avatar's own voice): "Quick note, this is the digital avatar of <name>, walking you through the update." Never use a static disclaimer slide before the hook.
- News beat: what changed.
- Story/example: a concrete situation that makes the change feel real.
- Source proof: agent-operated browser footage or screenshot showing the source.
- Action step: what the viewer should do next (3 numbered moves works well for an outro card).
- Spoken CTA tail (6-8 seconds, mandatory): the avatar speaks a follow CTA over the outro recap card, e.g. "If this kind of teardown is useful, hit follow over at <domain> for more <topic>. See you in the next one." This is what gives the master a natural ending instead of a silent dead-air card.

Visual brief shape for every beat:

- **Narration:** the exact words or Whisper segment.
- **Visual job:** proof / mechanism / consequence / action / transition.
- **Surface:** source page, UI, doc, dashboard, calendar, editor, browser tab, etc.
- **Before state:** what is passive, messy, manual, unknown, or unproven.
- **Action/motion:** cursor move, highlight, crop, tab switch, card reveal, split-screen, montage, etc.
- **After state:** what the viewer now understands.
- **Reject list:** lazy visuals that are banned for this beat (generic person at laptop, same hero page again, abstract AI brain, floating icons, etc.).

After HeyGen renders the avatar, immediately:

1. Extract the avatar audio with FFmpeg (`-vn -acodec libmp3lame`).
2. Transcribe with OpenAI Whisper (`response_format=verbose_json`, `timestamp_granularities=['word','segment']`) to get word- and segment-level timestamps.
3. Inspect the segments. If the script is duplicated, set the avatar trim end to the last second of the first unique pass.
4. Build a `storyboard.json` mapping each segment to a layout (avatar fullscreen / b-roll PiP / browser PiP), a visual job, a surface, a before/action/after description, a source-deck asset, a chapter title, and a source attribution.
5. Use those exact timestamps everywhere downstream — captions, segment cuts, lower-thirds.

### Stage 3: Asset generation

Use the routing rules:

- HeyGen for presenter/avatar clips.
- Seedance 2.0 for cinematic b-roll and generated motion.
- OpenAI image generation/editing for storyboards, stills, thumbnails, and inserts.
- `agent_browser_recorder.py` for coherent agent-operated browser footage.
- `screen_recorder.py` for lower-level product walkthrough recordings.
- `local_explainer_broll.py` as a no-credit fallback when Replicate/Seedance is unavailable.
- ElevenLabs for voiceover and music when available.

### Stage 4: Timeline assembly

Choose the composition engine:

- Remotion for React timelines, reusable product mockups, captioned talking head, b-roll overlays, and browser preview.
- HyperFrames for HTML-native timelines, deterministic frame capture, GSAP/Lottie/CSS animations, and agent-friendly browser preview.
- FFmpeg for practical compositing, muxing, chroma key, subtitles, audio, and final platform exports.

### Stage 5: QC and export

Always check:

- video has a video stream and expected resolution,
- audio exists when expected,
- duration is within target,
- captions are readable and synced,
- no obvious black frames,
- final codec is compatible: `libx264`, `aac`, `yuv420p`.
- b-roll layout QC contact sheets were reviewed and all non-passing assets were fixed/replaced.

## Main tools

```bash
python3 .agents/skills/super-video-maker/tools/heygen_client.py
python3 .agents/skills/super-video-maker/tools/replicate_video.py generate --prompt "cinematic b-roll..." --duration 7 --resolution 1080p --aspect-ratio 16:9
python3 .agents/skills/super-video-maker/tools/agent_browser_recorder.py
python3 .agents/skills/super-video-maker/tools/local_explainer_broll.py
python3 .agents/skills/super-video-maker/tools/screen_recorder.py
python3 .agents/skills/super-video-maker/tools/demo_video_composer.py
python3 .agents/skills/super-video-maker/tools/video_captioner.py
python3 .agents/skills/super-video-maker/tools/ffmpeg_qc.py
python3 .agents/skills/super-video-maker/tools/broll_layout_qc.py
```

## Result contract

Each stage should end with one line:

```json
RESULT: {"status":"succeeded","stage":"asset_generation","job_id":"video_001","artifacts":[{"type":"video","path":"output_videos/clip.mp4"}],"metrics":{"duration_seconds":7,"aspect_ratio":"16:9"},"next_action":"assemble_timeline"}
```

On failure:

```json
RESULT: {"status":"failed","stage":"asset_generation","error":"friendly explanation","debug_log":"tmp/video_jobs/video_001/log.txt"}
```

## Provider defaults

- Avatar: HeyGen.
- AI video b-roll: Replicate `bytedance/seedance-2.0`.
- Images: OpenAI image generation/editing.
- Voice: ElevenLabs.
- Music: ElevenLabs Music first, then Replicate or Suno adapters if configured.
- Programmatic editor: Remotion.
- HTML-native editor: HyperFrames.
- Final render/QC: FFmpeg and ffprobe.

## When not to use this skill

- The user only wants a single image.
- The user only wants a plain transcript with no video work.
- The user asks for manual Premiere/DaVinci steps and does not want automation.
