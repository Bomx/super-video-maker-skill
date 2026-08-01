---
description: Build a 9:16 split-screen avatar reel — article-scroll (or screen-recording) b-roll on top, AI avatar talking head on bottom, seam captions, hook badge, typing SFX + click-on-cut. Localizes to the project language.
argument-hint: <article URL or b-roll path> + topic/script + project language (and optional reference reel URL)
---

Build an **avatar-insta-split** reel with the `super-video-maker` skill.

User inputs: $ARGUMENTS

Run the skill's `avatar-insta-split` recipe end to end. Source of truth:
`recipes/avatar-insta-split.json` and `workflows/avatar-insta-split/README.md`.

Pipeline:
1. **Intake.** Confirm: the HeyGen avatar id (`HEYGEN_AVATAR_ID` / `--avatar-id`), the
   **project language** and target **platform** (YouTube vs Instagram), the b-roll source
   (a tall article screenshot for a scroll reel, or a screen recording), and the
   script/topic. If a reference reel URL is given, transcribe it (Groq) and copy its beat
   structure. **Confirm the paid HeyGen render before generating.**
2. **Script.** Hook → mechanism/listicle beats → CTA. Write the script **in the project
   language** (accents preserved; never em-dashes/smart-quotes/ellipsis). Avatars speak
   slower than people, so a ~33s human script lands near ~40s. Whisper-verify any brand
   name pronounces correctly (name-safety).
3. **Avatar (language-aware).**
   `python3 workflows/avatar-insta-split/gen_avatar.py --script-file script.txt --out job/avatar.mp4 --language <Lang> [--gender female] --avatar-id <ID>`
   - **English** → HeyGen text voice (`HEYGEN_VOICE_ID`), unchanged.
   - **Non-English** → a dynamically-picked **ElevenLabs** voice (eleven_v3) for that
     language drives a HeyGen audio-lip-synced render. Bundled model voice, never a cloned
     personal voice. Recover a timed-out poll by `video_id`; `MOVIO_PAYMENT_INSUFFICIENT_CREDIT`
     = top up HeyGen **API** credits.
4. **B-roll + beat map.**
   - *Article-scroll reel (recommended):* capture a tall article screenshot
     (`capture_article.py <url> <out.png>`), then author `plan.json` (copy
     `plan.example.json`) with per-beat `scroll_from`/`scroll_to` (pixels in the article at
     canvas width) so the scroll has an explicit, tunable **speed**. Include a **headline
     beat** (`scroll_from: 0`) so the H1 is on screen. Aspect is preserved automatically.
   - *Screen-recording reel (legacy):* one beat per cut with `t0`/`t1` on phrase breaks,
     a `broll_in` in-point, and a `crop` (now aspect-preserved — no squash).
5. **Badge + CTA.** Generate the hook badge in-pipeline so it is correctly shaped and
   localized: `python3 make_badge.py --brand "<Brand>" --language <Lang> --out badge.png`,
   set `badge_png` + `badge_w` in the plan. CTA split: **Instagram** → comment-DM
   (`cta_word`/`cta_text`); **YouTube** → brand callout (`cta_anchor: "tail"`,
   `cta_text: "Zoek <Brand>"`, `cta_word: null`) — never "comment"/"link in bio".
6. **Build.** `python3 workflows/avatar-insta-split/build_reel.py plan.json out.mp4` —
   split body + scroll/cuts + seam karaoke captions (auto-follow the VO language) + hook
   badge + typing bed + click-on-cut + loudnorm export.
7. **QC + deliver.** Sample frames: headline visible early, article pans at a readable
   speed and isn't squashed, captions on the seam in the right language, badge correctly
   shaped on the hook, CTA pill correct for the platform, loudness ~-16 LUFS, no
   clipping/black frames. Then hand over the MP4.

Only use an avatar of a real person with permission / a licensed or own likeness, and add
an AI-content label where the platform requires it.
