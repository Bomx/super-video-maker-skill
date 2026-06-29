---
description: Build a 9:16 split-screen avatar reel — screen-recording b-roll on top, AI avatar talking head on bottom, seam captions, hook badge, typing SFX + click-on-cut.
argument-hint: <b-roll screen-recording path> + topic/script (and optional reference reel URL)
---

Build an **avatar-insta-split** reel with the `super-video-maker` skill.

User inputs: $ARGUMENTS

Run the skill's `avatar-insta-split` recipe end to end. Source of truth:
`recipes/avatar-insta-split.json` and `workflows/avatar-insta-split/README.md`.

Pipeline:
1. **Intake.** Confirm the HeyGen avatar id + voice id (from `HEYGEN_AVATAR_ID` /
   `HEYGEN_VOICE_ID` in `.env`, or ask), the screen recording to use as b-roll, and
   the script/topic. If a reference reel URL is given, transcribe it (Groq) and copy
   its beat structure. **Confirm the paid HeyGen render before generating.**
2. **Script.** Hook → mechanism beats (one b-roll surface per beat) → comment-gated
   CTA. Avatars speak slower than people, so a ~33s human script lands near ~40s.
3. **Avatar.** `python3 workflows/avatar-insta-split/gen_avatar.py --script-file script.txt --out job/avatar.mp4`
   (9:16, normalized to 30fps). Recover a timed-out poll by `video_id`; if you hit
   `MOVIO_PAYMENT_INSUFFICIENT_CREDIT`, ask the user to top up HeyGen **API** credits.
4. **Beat map.** Transcribe the avatar audio (Groq Whisper), catalog the b-roll
   scenes (contact sheets), then author `plan.json` (copy `plan.example.json`): one
   beat per b-roll cut with `t0`/`t1` on phrase breaks, a `broll_in` in-point, and a
   `crop` zoomed into the readable content of that scene. Set the hook `badge_png`.
5. **Build.** `python3 workflows/avatar-insta-split/build_reel.py plan.json out.mp4`
   — split body + seam karaoke captions + hook badge + typing bed (first ~2s, very
   low) + a click on each cut + loudnorm export.
6. **QC + deliver.** Sample one frame per beat: no letterbox bars in the avatar
   region, captions on the seam, badge only on the hook, readable b-roll per beat,
   clicks on cuts, loudness ~-16 LUFS, no clipping/black frames. Then hand over the MP4.

Only use an avatar of a real person with permission / a licensed or own likeness,
and add an AI-content label where the platform requires it.
