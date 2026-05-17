# Remotion Template

This template renders captioned talking-head videos with optional picture-in-
picture b-roll. It is packaged inside the skill so agents can use it without the
original project repo.

## Setup

```bash
npm install
```

## Inputs

- `public/source/main.mp4`: the main talking-head or screen video.
- `public/broll/*.mp4`: optional b-roll clips.
- `public/render-props.json`: timing, captions, and b-roll manifest.

## Preview

```bash
npx remotion studio
```

## Render

```bash
npx remotion render src/index.ts CaptionedTalkingHead out/captioned.mp4 --props=public/render-props.json
```

## Build props from transcript JSON

Use `build_caption_props.py` if you have a timestamped word JSON.

```bash
CAPTION_WORDS_JSON=words.json CAPTION_MAIN_VIDEO_PUBLIC_PATH=source/main.mp4 python3 build_caption_props.py
```

See `../REMOTION_VIDEO_GUIDE.md` for design rules and production patterns.
