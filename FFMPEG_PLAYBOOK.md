# FFmpeg Playbook

Use FFmpeg after generation. It is the glue between HeyGen, screen recordings,
Seedance b-roll, Remotion/HyperFrames renders, captions, voice, and music.

All commands are examples. Replace paths with job-local files.

## Probe before editing

```bash
ffprobe -v error -show_streams -show_format -of json input.mp4
```

Check:

- duration,
- width and height,
- fps,
- audio stream exists when expected,
- codec compatibility.

## Normalize a video for editing

```bash
ffmpeg -y -i input.mp4 \
  -vf "fps=30,format=yuv420p" \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 192k \
  normalized.mp4
```

## Remove HeyGen green screen

```bash
ffmpeg -y -i heygen_green.mp4 \
  -vf "chromakey=0x00ff00:0.18:0.08,format=yuva420p" \
  -c:v qtrle \
  avatar_alpha.mov
```

For MP4 output with compositing in one command, use overlay instead of exporting
alpha.

## Avatar over screen recording

```bash
ffmpeg -y \
  -i screen_recording.mp4 \
  -i heygen_green.mp4 \
  -filter_complex "[1:v]chromakey=0x00ff00:0.18:0.08,scale=420:-1[avatar];[0:v][avatar]overlay=W-w-60:H-h-40:format=auto[v]" \
  -map "[v]" -map 0:a? -map 1:a? \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 192k \
  avatar_over_screen.mp4
```

## Picture-in-picture b-roll

```bash
ffmpeg -y \
  -i main.mp4 \
  -i broll.mp4 \
  -filter_complex "[1:v]scale=520:-1,setpts=PTS-STARTPTS+5/TB[pip];[0:v][pip]overlay=W-w-48:48:enable='between(t,5,12)'[v]" \
  -map "[v]" -map 0:a? \
  -c:v libx264 -preset medium -crf 18 \
  -c:a copy \
  pip.mp4
```

## Burn ASS captions

```bash
ffmpeg -y -i input.mp4 \
  -vf "subtitles='captions.ass'" \
  -c:v libx264 -preset medium -crf 18 \
  -c:a copy \
  captioned.mp4
```

Use ASS for karaoke captions because it gives better control over font size,
outline, position, and active-word colors.

## Mix voiceover and music

```bash
ffmpeg -y \
  -i video_no_audio.mp4 \
  -i voiceover.mp3 \
  -i music.mp3 \
  -filter_complex "[2:a]volume=0.12,apad[music];[1:a][music]amix=inputs=2:duration=first:dropout_transition=2[a]" \
  -map 0:v -map "[a]" \
  -c:v copy \
  -c:a aac -b:a 192k \
  video_with_audio.mp4
```

## Loudness normalize final audio

```bash
ffmpeg -y -i input.mp4 \
  -af "loudnorm=I=-16:TP=-1.5:LRA=11" \
  -c:v copy \
  -c:a aac -b:a 192k \
  normalized_audio.mp4
```

Targets:

- `-16 LUFS` for web/social general use,
- `-14 LUFS` if the platform strongly normalizes music-forward content.

## Concat clips safely

Create `clips.txt`:

```text
file 'clip_001.mp4'
file 'clip_002.mp4'
file 'clip_003.mp4'
```

Then:

```bash
ffmpeg -y -f concat -safe 0 -i clips.txt \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 192k \
  final_concat.mp4
```

If concat fails, normalize every clip first to the same fps, dimensions, video
codec, audio codec, and sample rate.

## Horizontal to vertical social export

Center-crop:

```bash
ffmpeg -y -i master_16x9.mp4 \
  -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 192k \
  vertical_9x16.mp4
```

Letterbox:

```bash
ffmpeg -y -i master_16x9.mp4 \
  -vf "scale=1080:-1,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black" \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 192k \
  vertical_letterbox.mp4
```

## Add top title plus captions area

```bash
ffmpeg -y -i input.mp4 \
  -vf "scale=1080:-1,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,drawtext=textfile='title.txt':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=72" \
  -c:v libx264 -preset medium -crf 18 \
  -c:a aac -b:a 192k \
  titled_vertical.mp4
```

## Extract a thumbnail

```bash
ffmpeg -y -ss 3 -i input.mp4 -frames:v 1 thumbnail.png
```

## Detect black frames

```bash
ffmpeg -i input.mp4 -vf "blackdetect=d=0.5:pix_th=0.10" -an -f null -
```

## Final export defaults

Use these unless a platform requires otherwise:

- video codec: `libx264`,
- pixel format: `yuv420p`,
- audio codec: `aac`,
- audio bitrate: `192k`,
- fps: `30`,
- CRF: `18` for high quality, `20-23` for smaller files.

## Source receipt card overlay

Use this when showing proof screenshots. A source shot should say exactly what
it proves: source name, date, and claim. Prefer a Pillow-rendered transparent
PNG receipt card for typography, then overlay it:

```bash
ffmpeg -y -i proof_clip.mp4 -i receipt_google_keyword.png \
  -filter_complex "[0:v][1:v]overlay=48:48:enable='between(t,0,3.2)'[v]" \
  -map "[v]" -map 0:a? \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a copy proof_with_receipt.mp4
```

Receipt card copy examples:

```text
Google Keyword · May 12, 2026
Official announcement
```

```text
Techmeme · Coverage cluster
40+ outlets picked it up
```

## Thin callout box around exact proof

Use a rounded PNG overlay if you need polished corners. For a quick FFmpeg-only
callout, draw a thin box around the exact phrase or UI area:

```bash
ffmpeg -y -i source_crop.mp4 \
  -vf "drawbox=x=120:y=420:w=980:h=96:color=0xFF6B2C@0.92:t=4" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a copy source_callout.mp4
```

Do not highlight whole pages. The box should surround one exact phrase,
headline, byline, number, feature name, or UI element.

## Split-screen proof-to-meaning layout

Use split screens when the narration connects a source claim to the implication
or action step. Example: official paragraph on the left, action checklist on
the right.

```bash
ffmpeg -y -i official_paragraph.mp4 -i action_card.mp4 \
  -filter_complex "\
[0:v]scale=960:1080:force_original_aspect_ratio=increase,crop=960:1080[left];\
[1:v]scale=960:1080:force_original_aspect_ratio=increase,crop=960:1080[right];\
[left][right]hstack=inputs=2[v]" \
  -map "[v]" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  split_proof_action.mp4
```

Use split screen sparingly. It is strong when the viewer needs to see "source
claim" and "why it matters" at the same time.

## Headline montage

Use this for "everyone covered it" beats instead of returning to the official
source page again. Prepare 4-6 headline crops, each 0.4-0.7 seconds. Add a
fast slide/scale in Remotion/HyperFrames when possible; in FFmpeg, short clips
and hard cuts are enough.

```bash
ffmpeg -y -loop 1 -t 0.55 -i verge_headline.png \
  -vf "scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,format=yuv420p" \
  -c:v libx264 -preset medium -crf 18 verge_headline.mp4

ffmpeg -y -f concat -safe 0 -i headline_clips.txt \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  headline_montage.mp4
```

`headline_clips.txt`:

```text
file 'verge_headline.mp4'
file 'wired_headline.mp4'
file 'engadget_headline.mp4'
file 'techcrunch_headline.mp4'
```

## Reuse one screenshot only with different jobs

If the same source page appears more than once, render separate clips with
different crops and labels. Do not use "same page, slightly different zoom" as
filler.

```bash
# Establishing receipt: headline + source/date.
ffmpeg -y -loop 1 -i google_keyword_full.png -t 1.8 \
  -vf "scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,zoompan=z='min(zoom+0.0012,1.08)':x='iw/2-(iw/zoom/2)':y='ih*0.12':d=1:s=1920x1080:fps=30,trim=duration=1.8,setpts=PTS-STARTPTS,format=yuv420p" \
  -an -c:v libx264 -preset medium -crf 18 establish_google_keyword.mp4

# Precision proof: exact paragraph crop.
ffmpeg -y -loop 1 -i google_keyword_full.png -t 2.4 \
  -vf "scale=3840:2160:force_original_aspect_ratio=increase,crop=3840:2160,zoompan=z='min(zoom+0.0014,1.16)':x='iw*0.05':y='ih*0.45':d=1:s=1920x1080:fps=30,trim=duration=2.4,setpts=PTS-STARTPTS,format=yuv420p" \
  -an -c:v libx264 -preset medium -crf 18 paragraph_proof_google_keyword.mp4
```

The two clips have different jobs: establish source, then prove exact claim.

## Disclosure badge PNG overlay (top-left, hook only)

Replace `drawbox` lower-thirds with a Pillow-rendered transparent PNG. The
badge is `assets/disclosure_badge.png` (~420x80 transparent RGBA). Overlay
top-left during the hook only and fade out before the PiP appears:

```bash
ffmpeg -y -i body.mp4 -i assets/disclosure_badge.png \
  -filter_complex "[0:v][1:v]overlay=50:50:enable='between(t,0.5,4.5)'[v]" \
  -map "[v]" -map 0:a? \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a copy with_badge.mp4
```

Why PNG instead of `drawbox`: anti-aliased rounded corners, proper alpha,
and clean professional look next to the captions.

## Avatar PiP — borderless, rounded corners, soft drop shadow (default)

The default PiP style is borderless with a 24px rounded crop and a soft drop
shadow underneath. Pre-render two reusable PNGs once per job
(see `REFERENCE.md` → Avatar PiP styling for the Pillow snippet that creates
`assets/pip_mask.png` and `assets/pip_shadow.png`).

Top-right placement on a 1920x1080 master at `PX=1378, PY=50`, shadow offset
`+4 / +16`:

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

Adjust the `enable=` window so the PiP appears only during non-fullscreen
beats and is hidden during the outro CTA tail (so the recap card owns the
frame). Do NOT add a `pad` color border — the rounded crop + shadow alone is
the modern card look.

## Centered karaoke captions (default ASS style)

This is the default style used for all current masters. Save as a `.ass`
header before generating dialogue lines from Whisper words:

```text
[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial Black,64,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,5,2,2,80,80,90,1
Style: Active,Arial Black,64,&H0000FFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,5,2,2,80,80,90,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
```

Key fields:

- `Alignment=2` → bottom-center.
- `MarginL=MarginR=80, MarginV=90` → balanced bottom band.
- `Fontsize=64, Bold=-1` → punchy Hormozi-style.
- `OutlineColour=&H00000000, Outline=5, Shadow=2` → readable on any
  background.
- Active word: same style with `PrimaryColour=&H0000FFFF` (yellow).

Burn:

```bash
ffmpeg -y -i body.mp4 -vf "subtitles='captions.ass'" \
  -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a copy captioned.mp4
```

## Hold the outro card under a spoken CTA tail (no silent end)

After the action close, extend the outro recap card so it stays on screen
for the spoken CTA tail. `outro_duration = avatar_total - body_end_seconds`.
For a 96.86s avatar with a body that ends at 89.80s, the outro card runs
for 7.06s under the CTA audio:

```bash
ffmpeg -y -loop 1 -i outro_card.png -t 7.06 -r 30 \
  -vf "scale=1920:1080,format=yuv420p" \
  -c:v libx264 -preset medium -crf 18 outro_card_clip.mp4
```

Then concat `body_with_pip.mp4` + `outro_card_clip.mp4` and mux the full
avatar audio (which contains the CTA tail) on top — the audio plays right
through the outro card so the video has a natural sign-off instead of dead
air.

## Common failure fixes

| Problem | Fix |
|---|---|
| Captions path fails | Escape absolute path or move `.ass` beside the video. |
| MP4 has no audio | Check `-map` arguments and optional audio streams. |
| Social upload rejects file | Re-encode with `yuv420p`, H.264, AAC. |
| Concat fails | Normalize all clips first. |
| Avatar has green edge | Lower similarity or blend values in `chromakey`. |
| Audio too loud under voice | Lower music volume or use sidechain compression. |
| Captions overlap lower-third | Move disclosure to a top-left PNG badge; keep captions `Alignment=2` and reserve only the bottom band for them. |
| PiP overlaps captions | Move PiP to top-right (`x=W-pip_w-50, y=50`). |
| Video ends abruptly | Add a 6-8s spoken CTA tail and extend the outro card to its duration. |
| `drawbox` lower-third looks cheap | Render a transparent rounded-pill PNG with Pillow and overlay it. |
