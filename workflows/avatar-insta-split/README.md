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

# 1) generate the avatar clip (HeyGen). LANGUAGE-AWARE:
#    English  -> HeyGen text voice (HEYGEN_VOICE_ID) — unchanged.
#    non-EN   -> a dynamically-picked ElevenLabs voice (eleven_v3) lip-synced by the avatar.
python3 $WF/gen_avatar.py --script-file script.txt --out job/avatar.mp4 \
        --language Dutch --gender female --avatar-id <HEYGEN_AVATAR_ID>

# 2a) (article-scroll reel) capture a tall article screenshot (headline at top + section offsets)
python3 $WF/capture_article.py "https://site/blog/best-x" job/article.png

# 2b) make the '#1 PICK' badge in-pipeline — correctly shaped + localized
python3 $WF/make_badge.py --brand "De Vries Geveltechniek" --language Dutch --out job/badge.png

# 2c) author plan.json (copy plan.example.json): set language/platform, avatar_clip,
#     broll_source, badge_png + badge_w, and the beats. For a scroll reel use
#     scroll_from/scroll_to (incl. a headline beat with scroll_from:0).

# 3) build the reel (split body + scroll/cuts + captions + badge + SFX + loudnorm)
python3 $WF/build_reel.py plan.json out.mp4
```

`build_reel.py` prints `RESULT: {...}` with the output path, duration, beat/cut
counts, and whether SFX were mixed.

## plan.json fields

| field | meaning |
|---|---|
| `canvas` | `w`,`h`,`fps` of the master (default 1080x1920@30) |
| `language` | project language. `English` = HeyGen text voice (unchanged); anything else = ElevenLabs VO + localized captions/badge/CTA |
| `platform` | `youtube` (brand-callout CTA) or `instagram` (comment-DM CTA) |
| `split.broll_top_h` / `avatar_bottom_h` | pixel heights of the two regions (sum = `h`) |
| `split.avatar_content_band` | `"auto"` (trim letterbox bars) or `{ "y": .., "h": .. }` |
| `avatar_clip` / `broll_source` | the talking-head clip and the b-roll: a tall **article screenshot** (`.png`, scrolled) or a **screen recording** (`.mp4`, static crops) |
| `badge_png` / `badge_enable` / `badge_xy` / `badge_w` | hook badge PNG, `[start,end]` seconds, top-left xy, and the **target width** (the badge is scaled to it with square pixels so it can't render out of shape) |
| `transcript` | path to a Groq `verbose_json` transcript, or `null` to auto-transcribe (captions auto-follow the VO language) |
| `caption` | `font`,`pt`,`seam_cy`, pill padding/radius, `cta_word`/`cta_text`, `cta_anchor` (`"tail"` holds the CTA over the last `cta_tail_s`s — language/platform-agnostic), regex `fixups` |
| `sfx` | `typing`/`click` wavs, `typing_vol` (keep low), `click_vol`, `enabled` |
| `beats[]` | `t0`,`t1` (seconds). **Scroll mode:** `scroll_from`/`scroll_to` (px in the article at canvas width — explicit, tunable scroll speed; `scroll_from:0` frames the headline). **Static mode:** `broll_in` (in-point) + `crop` (`CW:CH:CX:CY`, aspect-preserved) |

Boundaries are frame-aligned, so the avatar audio and lip-sync stay continuous
across the concat.

## Localization (the De Vries / non-English fix)

For a non-English project the VO is generated with a dynamically-picked ElevenLabs
voice that matches the language (`tools/elevenlabs_voice.py`, `eleven_v3`), uploaded to
HeyGen, and lip-synced by the avatar. Captions auto-follow (Whisper is multilingual), the
badge is generated localized (`make_badge.py`), and the CTA is platform-correct (YouTube
brand callout vs Instagram comment-DM). **English projects are unchanged.**

## Requirements

`ffmpeg`/`ffprobe`, ImageMagick (`magick`), `GROQ_API_KEY` (captions), and
`HEYGEN_API_KEY` + an avatar/voice id (avatar generation). Put keys in `.env`.

## SFX

`assets/typing.wav` (2s keyboard bed) and `assets/click.wav` (UI tick) are
synthesized procedurally by `make_sfx.py` (royalty-free, no external assets).
Tune `typing_vol` / `click_vol` in the plan.
