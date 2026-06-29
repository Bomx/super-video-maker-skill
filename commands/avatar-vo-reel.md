---
description: Build a fullscreen voiceover-over-b-roll reel — talking-head avatar hook, then fullscreen screen-capture b-roll while the VO continues, lower-third captions, badge swap, SFX.
argument-hint: <b-roll clip(s) or library dir> + topic/script (and optional reference reel URL)
---

Build an **avatar-vo-broll** reel with the `super-video-maker` skill (fullscreen
hook + voiceover-over-b-roll, the "film my screen with my phone and talk over it" style).

User inputs: $ARGUMENTS

Source of truth: `recipes/avatar-vo-broll.json` and
`workflows/avatar-vo-broll/README.md`. Use **avatar-vo-broll** (not avatar-insta-split)
when the talking head should disappear during the b-roll.

Pipeline:
1. **Intake.** Confirm the HeyGen avatar id (`HEYGEN_AVATAR_ID` / `--avatar-id`), the b-roll
   clips to use (a library dir or specific clips), and the script/topic. If a reference
   reel URL is given, download + transcribe it (Groq) and copy its beat structure and
   badge/CTA pattern. **Confirm the paid HeyGen render before generating.**
2. **Script.** Hook (one line) -> one mechanism beat per b-roll surface -> comment- or
   share-gated CTA. Avatars speak slower, so a ~33s human script lands near ~40s.
3. **Avatar.** `python3 workflows/avatar-insta-split/gen_avatar.py --script-file script.txt --out job/avatar.mp4 --avatar-id <ID>`
   (its audio is the continuous voiceover). Recover a timed-out poll by `video_id`;
   `MOVIO_PAYMENT_INSUFFICIENT_CREDIT` = top up HeyGen **API** credits.
4. **Beat map.** Transcribe the avatar audio (Groq). Mark the hook (and optional close)
   beats `type:"avatar"` and each middle beat `type:"broll"` with the matching library
   clip, cutting on phrase breaks. Beats must cover the whole VO. Author `plan.json`
   (copy `plan.example.json`). Make the badges with `make_badge.py` (topic on the hook,
   "Comment SKILL"/CTA over the b-roll).
5. **Build.** `python3 workflows/avatar-vo-broll/build_vo_broll.py plan.json out.mp4` —
   fullscreen avatar hook/close (blurred-fill) + fullscreen b-roll cuts + lower-third
   captions + badge sequence + typing bed + click-on-cut + loudnorm.
6. **QC + deliver.** Sample a frame per beat: avatar fills the frame on hook/close, b-roll
   fills the frame and is the right clip per line, captions in the lower third, badge
   swaps on cue, loudness ~-16 LUFS, no clipping/black frames. Then hand over the MP4.

Only use an avatar of a real person with permission / a licensed or own likeness, and add
an AI-content label where the platform requires it.
