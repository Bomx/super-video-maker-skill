# HyperFrames Template

HyperFrames turns HTML compositions into deterministic video renders. This
template gives agents a simple HTML-native starting point.

## Setup

```bash
npm install
```

## Preview

```bash
npx hyperframes preview compositions/demo.html
```

## Render

```bash
npx hyperframes render compositions/demo.html --output out/demo.mp4
```

## Authoring notes

- Use normal HTML/CSS for layout.
- Use `data-start`, `data-duration`, and `data-track-index` for timing.
- Add GSAP, Lottie, or CSS animation when the runtime can seek frame-by-frame.
- Finish audio, captions, and final platform exports with FFmpeg.
