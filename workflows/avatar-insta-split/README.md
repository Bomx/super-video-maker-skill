# avatar-insta-split

Instagram / Reels / Shorts **split-screen** format with an AI avatar:

```
┌──────────────────────────────┐
│   screen-recording b-roll     │  top ~53%  (cuts on every beat)
│   (CLI, docs, dashboard, …)   │
├───────────[ caption ]─────────┤  karaoke pill sits on the seam
│        avatar / talking head  │  bottom ~47% (auto-cropped from its
│        (cap + face + mic)     │  content band, so letterboxed HeyGen
└──────────────────────────────┘  renders fill the region cleanly)
```

- Hook badge (e.g. a brand pill) shown over the first few seconds.
- **Typing SFX** runs under the first ~2s at very low volume (pairs with a CLI/typing hook).
- A subtle **click SFX** lands on every b-roll cut.
- Captions are generated from the avatar's own audio (Groq Whisper), with a held
  CTA pill at the end.

The presenter is a landscape-recorded avatar, so this format keeps a **consistent
split the whole way through** (no fullscreen talking-head), which is where a
letterboxed avatar frames best. For real vertical selfie footage you can raise
`avatar_bottom_h` and the auto band-detect will simply use the full frame.

## Pipeline

```bash
WF=.agents/skills/super-video-maker/workflows/avatar-insta-split

# 0) (optional) regenerate the bundled SFX
python3 $WF/make_sfx.py $WF/assets

# 1) generate the avatar clip (HeyGen).  Avatar/voice come from CLI or
#    HEYGEN_AVATAR_ID / HEYGEN_VOICE_ID in your .env.  9:16, normalized to 30fps.
python3 $WF/gen_avatar.py --script-file script.txt --out job/avatar.mp4

# 2) author a plan.json (copy plan.example.json): set avatar_clip, broll_source,
#    the hook badge, and one beat per b-roll cut (t0/t1 + broll_in + crop).
#    Land beat boundaries on sentence/phrase breaks from the transcript.

# 3) build the reel (split body + captions + badge + SFX + loudnorm export)
python3 $WF/build_reel.py plan.json out.mp4
```

`build_reel.py` prints `RESULT: {...}` with the output path, duration, beat/cut
counts, and whether SFX were mixed.

## plan.json fields

| field | meaning |
|---|---|
| `canvas` | `w`,`h`,`fps` of the master (default 1080x1920@30) |
| `split.broll_top_h` / `avatar_bottom_h` | pixel heights of the two regions (sum = `h`) |
| `split.avatar_content_band` | `"auto"` (trim letterbox bars) or `{ "y": .., "h": .. }` |
| `avatar_clip` / `broll_source` | the talking-head clip and the screen recording |
| `badge_png` / `badge_enable` / `badge_xy` | hook badge PNG, `[start,end]` seconds, top-left xy |
| `transcript` | path to a Groq `verbose_json` transcript, or `null` to auto-transcribe |
| `caption` | `font`,`pt`,`seam_cy`, pill padding/radius, `cta_word`/`cta_text`, regex `fixups` |
| `sfx` | `typing`/`click` wavs, `typing_vol` (keep low), `click_vol`, `enabled` |
| `beats[]` | `t0`,`t1` (seconds), `broll_in` (b-roll in-point), `crop` (`CW:CH:CX:CY` source crop) |

Boundaries are frame-aligned, so the avatar audio and lip-sync stay continuous
across the concat.

## Requirements

`ffmpeg`/`ffprobe`, ImageMagick (`magick`), `GROQ_API_KEY` (captions), and
`HEYGEN_API_KEY` + an avatar/voice id (avatar generation). Put keys in `.env`.

## SFX

`assets/typing.wav` (2s keyboard bed) and `assets/click.wav` (UI tick) are
synthesized procedurally by `make_sfx.py` (royalty-free, no external assets).
Tune `typing_vol` / `click_vol` in the plan.
