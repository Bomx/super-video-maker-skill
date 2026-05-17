# Super Video Maker Skill

**Built by the team at Distribb — the SEO and growth autopilot for operators.**  
**→ Build and scale content systems with us at [distribb.io](https://distribb.io).**

---

> **An end-to-end AI video production skill for agentic coding frameworks.** Give your Cursor, Claude Code, or other shell-capable AI agent a video idea, source link, product flow, screen recording, or script, and this skill teaches the agent how to turn it into a polished video using HeyGen avatars, screen recordings, AI b-roll, OpenAI image generation, Remotion, HyperFrames, FFmpeg, captions, music, and quality-control loops.

This repo is designed to be dropped into an AI agent project as a reusable skill. It includes the actual instruction file (`SKILL.md`), deep production references, workflow examples, FFmpeg recipes, Python tools, and starter Remotion/HyperFrames templates.

The flagship format is:

**Avatar Explainers** (`avatar-explainer`) — proof-driven videos with a synthetic presenter, source receipts, screen recordings, UI micro-stories, captions, and action takeaways.

---

## What It Can Make

- **Avatar Explainers:** trending-news or tutorial videos with a HeyGen avatar, source receipts, b-roll, captions, and CTA outro.
- **Screen-recorded demos:** product walkthroughs with cursor logs, zooms, click effects, captions, narration, and optional S3 upload.
- **AI b-roll videos:** Seedance 2.0 clips through Replicate, with OpenAI image fallback and FFmpeg motion.
- **Captioned talking-head videos:** avatar or real video plus centered karaoke captions.
- **Faceless explainers:** motion graphics, UI cards, screenshots, typographic cards, and generated scenes.
- **Repurposed shorts:** long videos clipped, captioned, reformatted, and exported for social platforms.
- **Motion-graphic edits:** Remotion or HyperFrames timelines previewable in a browser.

---

## Why This Skill Exists

Most AI video tools stop at one layer:

- one avatar generator,
- one image generator,
- one screen recorder,
- one captioning tool,
- one FFmpeg command.

Real videos need the whole pipeline:

1. pick the story,
2. write the script,
3. gather source proof,
4. generate or capture the right visuals,
5. sync everything to the actual voiceover,
6. compose the timeline,
7. burn captions,
8. normalize audio,
9. check visual layout,
10. export clean files.

This skill gives an AI agent the operating system for that process.

---

## Repository Structure

```text
super-video-maker-skill/
├── SKILL.md                         # Main agent instructions
├── REFERENCE.md                     # Provider choices, design logic, quality gates
├── WORKFLOW_EXAMPLES.md             # Full recipes, including Avatar Explainers
├── FFMPEG_PLAYBOOK.md               # Practical FFmpeg recipes
├── REMOTION_VIDEO_GUIDE.md          # Remotion production style guide
├── requirements.txt                 # Python dependencies
├── package.json                     # Root JS tooling dependencies
├── .env.example                     # Environment variable template
├── tools/
│   ├── heygen_client.py             # HeyGen avatar generation + polling + download
│   ├── replicate_video.py           # Seedance 2.0 via Replicate
│   ├── image_provider.py            # OpenAI image generation/editing helper
│   ├── screen_recorder.py           # FFmpeg/Xvfb or Playwright screen recording
│   ├── agent_browser_recorder.py    # Agent-operated browser proof recording
│   ├── demo_video_composer.py       # Polished product demo composer
│   ├── video_captioner.py           # Whisper + ASS captions + shorts rendering
│   ├── music_provider.py            # ElevenLabs music helper
│   ├── local_explainer_broll.py     # Local fallback b-roll renderer
│   ├── broll_layout_qc.py           # Visual layout QC contact sheets
│   └── ffmpeg_qc.py                 # Final technical QC
├── remotion-template/               # Starter Remotion project
└── hyperframes-template/            # Starter HyperFrames/HTML timeline
```

---

## Install

Clone the repo:

```bash
git clone https://github.com/Bomx/super-video-maker-skill.git
cd super-video-maker-skill
```

Install Python dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 -m playwright install chromium
```

Install JavaScript dependencies if you want Remotion or HyperFrames:

```bash
npm install
cd remotion-template && npm install && cd ..
cd hyperframes-template && npm install && cd ..
```

Install system dependencies:

```bash
brew install ffmpeg
```

On Linux servers you may also need:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg xvfb
```

Create your environment file:

```bash
cp .env.example .env
```

Then fill in the keys you plan to use.

---

## Environment Variables

Minimum useful setup:

```bash
HEYGEN_API_KEY=
HEYGEN_AVATAR_ID=
HEYGEN_VOICE_ID=
OPENAI_API_KEY=
REPLICATE_API_TOKEN=
ELEVENLABS_API_KEY=
```

Optional:

```bash
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=us-east-1
AWS_S3_BUCKET=
SOUNDTRACKS_S3_BASE_URL=
ANTHROPIC_API_KEY=
```

Provider notes:

- **HeyGen** renders avatar video. `HEYGEN_AVATAR_ID` and `HEYGEN_VOICE_ID` are separate values.
- **OpenAI** is used for image generation/editing and Whisper transcription.
- **Replicate** runs Seedance 2.0 b-roll.
- **ElevenLabs** can generate voiceover or music.
- **AWS S3** is only needed if you use upload helpers in the demo composer.

Never commit `.env`, cookies, generated videos, recordings, or user sessions.

---

## Add It To An Agent

### Cursor Project Skill

Copy the folder into your project:

```bash
mkdir -p .agents/skills
cp -R super-video-maker-skill .agents/skills/super-video-maker
```

Then ask your agent:

```text
Use the super-video-maker skill to create an avatar explainer about this topic...
```

### Claude Code / Other Agentic Frameworks

Place `SKILL.md` and the supporting files wherever your framework loads skills or system prompts from. The important part is that the agent can read:

- `SKILL.md`,
- `REFERENCE.md`,
- `WORKFLOW_EXAMPLES.md`,
- `FFMPEG_PLAYBOOK.md`,
- `REMOTION_VIDEO_GUIDE.md`,
- the `tools/` directory.

If your framework does not support skills natively, paste `SKILL.md` into the agent's system prompt and keep the rest of the files in the working directory.

---

## Quick Start: Make An Avatar Explainer

Example prompt to your agent:

```text
Use the super-video-maker skill.

Make a 90-second Avatar Explainer about a trending SEO topic.
Use a recent X.com post as a trend signal, but verify the claims with official sources.
Use my HeyGen avatar.
Use screen/source receipts and UI micro-stories.
Do not make generic AI b-roll.
Pause before paid HeyGen/OpenAI/Replicate calls and show me the plan first.
```

Expected agent flow:

1. Pick the topic and trend signal.
2. Build a source deck with official/corroborating sources.
3. Write the avatar script.
4. Create a storyboard with one visual job per beat: proof, mechanism, consequence, action, or transition.
5. Ask before paid generation.
6. Render the HeyGen avatar.
7. Extract audio and transcribe with word-level timestamps.
8. Generate b-roll/source assets.
9. Run `broll_layout_qc.py`.
10. Compose with FFmpeg or Remotion.
11. Burn centered karaoke captions.
12. Run `ffmpeg_qc.py`.
13. Sample frames and visually review the result.

---

## The Avatar Explainer Recipe

Use `avatar-explainer` when the video combines:

- a synthetic presenter,
- source proof,
- screen recordings or screenshots,
- b-roll that explains the narration,
- UI micro-stories,
- centered captions,
- a spoken CTA ending.

The default structure:

```text
Hook
→ casual avatar disclosure
→ news/update beat
→ concrete example
→ source proof
→ action steps
→ spoken CTA tail over outro card
```

Important rules:

- Say the avatar disclosure in the script after the hook.
- Do not use a static disclaimer slide.
- Put the avatar PiP top-right, borderless, rounded, with a soft drop shadow.
- Keep captions bottom-centered.
- Never place captions and lower-thirds in the same band.
- Beat-lock visual changes to actual Whisper timestamps, not guessed timings.
- Use real screenshots/source receipts before generated b-roll.
- Run layout QC before final composition.

---

## Tool Examples

Generate a HeyGen avatar clip:

```bash
python3 tools/heygen_client.py \
  --script-file script.txt \
  --output tmp/video_jobs/my_job/avatar.mp4 \
  --avatar-id "$HEYGEN_AVATAR_ID" \
  --voice-id "$HEYGEN_VOICE_ID"
```

Generate Seedance b-roll:

```bash
python3 tools/replicate_video.py generate \
  --prompt "documentary-style browser research shot, source receipt, modern editorial pacing" \
  --duration 7 \
  --resolution 1080p \
  --aspect-ratio 16:9
```

Run b-roll layout QC:

```bash
python3 tools/broll_layout_qc.py tmp/video_jobs/my_job/assets/*.mp4 --job-dir tmp/video_jobs/my_job
```

Run final technical QC:

```bash
python3 tools/ffmpeg_qc.py tmp/video_jobs/my_job/final/master.mp4
```

---

## B-Roll Taste Rules

The skill strongly avoids generic "AI slop." A good visual answers:

```text
What state change should the viewer understand at this sentence?
```

Good visual choices:

- official source screenshots,
- exact paragraph crops,
- browser proof recordings,
- UI before/after states,
- headline walls,
- source receipt cards,
- action cards,
- dashboards,
- calendars,
- CMS editors,
- docs, spreadsheets, or SERPs where the work actually happens.

Bad visual choices:

- random person at a laptop,
- glowing AI brain,
- neon grid,
- floating icons,
- generic data streams,
- repeated website hero crops,
- slow scrolling with no new evidence.

---

## Quality Gates

Every serious video should pass:

- **Paid-call gate:** before HeyGen/OpenAI/Replicate calls, show planned providers, count, duration, resolution, and cost drivers.
- **Source-deck gate:** every major claim has a receipt or clear source.
- **Timestamp gate:** visuals and captions are locked to actual audio timestamps.
- **Layout gate:** `broll_layout_qc.py` confirms no PiP/caption collisions.
- **Technical gate:** `ffmpeg_qc.py` confirms stream, duration, codec, audio, resolution, and black-frame checks.
- **Human/vision gate:** sample final frames and inspect them like a viewer.

---

## Included Templates

### Remotion

Use `remotion-template/` when you want a React-based editor/timeline:

```bash
cd remotion-template
npm install
npm run dev
```

Render:

```bash
npx remotion render src/index.ts CaptionedTalkingHead out/video.mp4
```

### HyperFrames

Use `hyperframes-template/` when you want HTML-native timeline composition:

```bash
cd hyperframes-template
npm install
npm run dev
```

---

## Recommended Agent Prompt

```text
Use the super-video-maker skill.

Goal: create a polished Avatar Explainer.
Length: 90 seconds.
Format: 16:9.
Presenter: HeyGen avatar.
Style: source receipts, UI micro-stories, fast editorial pacing, centered captions.

Before paid calls:
- show the source deck,
- show the script,
- show the storyboard,
- list the paid generation calls and cost drivers.

After generation:
- transcribe the audio,
- align visuals to Whisper timestamps,
- run b-roll layout QC,
- run final FFmpeg QC,
- sample frames and visually inspect the result.
```

---

## Safety And Ethics

- Disclose synthetic presenters.
- Do not fake screenshots, tweets, source receipts, or publication claims.
- Do not publish private avatar IDs, session cookies, tokens, or generated user media.
- Avoid copyright-infringing visual prompts or copied channel styles.
- Use generated visuals as explanation, not deception.
- Prefer official sources for news/SEO/finance/health claims.

---

## Roadmap Ideas

- One-command `video_orchestrator.py` recipe runner for `avatar-explainer`.
- Built-in HTML source receipt renderer.
- Browser-based review dashboard for b-roll layout QC.
- Optional auto-upload adapters for YouTube, LinkedIn, TikTok, and X.
- More Remotion components for proof cards, source decks, and action cards.

---

## Built By Distribb

Distribb helps founders and operators build SEO systems: keyword research, original data research, content publishing, internal linking, backlinks, and content repurposing.

Learn more at [distribb.io](https://distribb.io).
