# avatar-vo-broll

Fullscreen **"talking-head hook + voiceover-over-b-roll"** reel (the "film my laptop
screen with my phone and talk over it" style):

```
hook   ▶ FULLSCREEN avatar talking head        (letterboxed renders are blurred-filled)
body   ▶ FULLSCREEN screen-capture b-roll       (one clip per beat, VO keeps playing)
body   ▶ FULLSCREEN screen-capture b-roll
close  ▶ FULLSCREEN avatar  (optional)
```

- The avatar audio is ONE continuous voiceover under the whole reel. The avatar VIDEO
  only shows on `type: "avatar"` beats (hook / close); on `type: "broll"` beats a library
  clip fills the frame while the VO continues.
- Lower-third karaoke captions, a top **badge sequence** (topic label on the hook,
  swapping to a CTA over the b-roll), and the typing bed + click-on-cut SFX.
- B-roll clips that are already 9:16 (e.g. phone captures of a laptop, 576x1024) fill the
  frame directly. Low-res / dim phone-capture footage is fine — that is the look.

This is the sibling of `avatar-insta-split` (split-screen). Use **this** one when the
talking head should disappear during the b-roll, like Borja's most-successful reels.

## Pipeline

```bash
SPLIT=.agents/skills/super-video-maker/workflows/avatar-insta-split
VO=.agents/skills/super-video-maker/workflows/avatar-vo-broll

# 1) avatar clip (reuses the avatar-insta-split generator; its audio is the VO).
#    FLUID-VOICE RULE: HeyGen text-to-speech inserts a ~0.3s pause at every comma and
#    period, so short choppy sentences -> a choppy VO (and over fullscreen b-roll there's
#    no face to explain the pause). Write the script as flowing connected speech with
#    minimal punctuation. The audio is laid under the whole reel as ONE continuous track,
#    never cut or stitched per clip.
python3 $SPLIT/gen_avatar.py --script-file script.txt --out job/avatar.mp4 --avatar-id <HEYGEN_AVATAR_ID>

# 2) (optional) badges — topic on the hook, CTA over the b-roll
python3 $SPLIT/make_badge.py --brand "Your Topic" --out job/badge_topic.png
python3 $SPLIT/make_badge.py --brand "Comment SKILL" --out job/badge_cta.png

# 3) author plan.json (copy plan.example.json): mark hook/close beats type:"avatar",
#    middle beats type:"broll" + clip path, on phrase breaks; beats cover the whole VO.

# 4) build
python3 $VO/build_vo_broll.py plan.json out.mp4
```

`build_vo_broll.py` prints `RESULT: {...}` with the output path, duration, beat/cut
counts, and whether SFX were mixed.

## plan.json fields

| field | meaning |
|---|---|
| `canvas` | `w`,`h`,`fps` (default 1080x1920@30) |
| `avatar_clip` | the talking-head clip; its audio is the continuous voiceover |
| `avatar_content_band` | `"auto"` (trim letterbox bars for the blurred-fill) or `{ "y": .., "h": .. }` |
| `transcript` | Groq `verbose_json` path, or `null` to auto-transcribe |
| `badges[]` | `{png, from, to, xy, w}` overlaid in sequence (topic -> CTA) |
| `caption` | `font`,`pt`,`cy` (lower third), padding/radius, `cta_word`/`cta_text`/`cta_anchor`, regex `fixups` |
| `sfx` | `typing`/`click` wavs (defaults to the avatar-insta-split assets), `typing_vol`, `click_vol` |
| `beats[]` | `t0`,`t1`; `type:"avatar"` (hook/close) or `type:"broll"` + `clip` (+ optional `clip_in`). Beats must cover the whole avatar duration. |

Boundaries are frame-aligned so the VO and lip-sync stay continuous across the cuts.

## Requirements

`ffmpeg`/`ffprobe`, ImageMagick (`magick`), `GROQ_API_KEY` (captions), `HEYGEN_API_KEY`
+ an avatar id (avatar generation). Shares the SFX + helpers with `avatar-insta-split`.
