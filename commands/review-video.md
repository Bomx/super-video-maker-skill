---
description: Make a "<Competitor> Reviews" video — a fast, faceless VO montage of REAL, verified competitor reviews that names the recurring complaints and positions YOUR business as the alternative, then hands off to your own customer testimonials.
argument-hint: <competitor name or review-page URL> + your business and its real strengths (+ optional path to your own testimonial reel)
---

Build a **review-conquest compilation** video with the `super-video-maker` skill for: $ARGUMENTS

This targets the search keyword **"<competitor> reviews"**. It is honest comparative
marketing: compile REAL, verified reviews of a competitor (mostly the critical and
neutral ones, plus a couple of positives for balance), surface the recurring gaps, and
position **the user's own business** as the alternative that closes them — ending by
handing the mic to the user's own customers.

Source of truth: **`REVIEW_VIDEO_PLAYBOOK.md`** (full method) and
`recipes/review-conquest-compilation.json`. Read the playbook before generating.

## Non-negotiable guardrail (read first)
Only put REAL, verified, attributable reviews on screen. Never invent, embellish,
paraphrase-as-a-quote, or doctor a review. Cherry-picking the honest negatives is fine;
fabricating or misrepresenting a competitor is false advertising + defamation. If the
competitor doesn't have enough genuine critical reviews, tell the user and stop — do not
manufacture them. The user's own strengths and testimonials must be real too.

## Pipeline (see the playbook for detail)
1. **Intake.** Competitor (name/URL); **the user's business + its real, defensible
   strengths** that map to the competitor's weak spots; optional path to the user's own
   testimonial reel to append; platform (default YouTube 16:9, ~2–4 min). Confirm
   `ELEVENLABS_API_KEY` (VO) exists; captions can come from ElevenLabs timestamps, a local
   whisper, or `OPENAI_API_KEY`. No HeyGen/Seedance needed — this is real footage.
2. **Recon.** WebSearch to confirm the competitor is real and has findable reviews. If
   there is no genuine critical-review volume, stop.
3. **Research + verify (the important part).** Fan out across every review surface —
   Trustpilot, G2/Capterra, the relevant app store (Shopify/WordPress/Chrome),
   Reddit/forums/FB groups, third-party review blogs, YouTube reviews, X/LinkedIn. Extract
   verbatim reviews with author, date, rating, sentiment, theme, and exact source URL. Many
   sites (Trustpilot) 403 automated fetches — drive a real browser (Chrome) to read the
   star-filtered pages. Then **adversarially verify every critical quote**: re-open the
   cited source, confirm it appears verbatim and is attributable, default to reject if
   unconfirmed. Keep only confirmed quotes.
4. **Synthesize.** Cluster confirmed reviews into 4–6 themes; map each to a TRUTHFUL
   strength of the user's business; pick the punchiest verified on-screen quotes; write an
   honest sentiment breakdown (if the competitor is 4.8★, the angle is "the pattern inside
   the 1–2★ tail is exactly what we fix," not "everyone hates them"); draft the script +
   shot list.
5. **Script.** Hook (rating vs. the tail) → "I read every 1- and 2-star review" → each gap
   with a real quote on screen → "these are the hardest parts of `<category>`" → the user's
   business closing each gap → handoff: "But don't take my word for it — let's hear from
   actual `<Business>` users." Show the user the reviews + script before any paid generation.
6. **Produce (faceless VO montage).** Screenshot the REAL review pages (browser; the review
   is the proof — never generate a fake review screenshot). Brand lightly (kicker chip,
   VERIFIED tag, on-screen source). ElevenLabs VO → beat-locked karaoke captions → Ken Burns
   on screenshots / gentle zoom on cards, cutting every 3–6s on screenshots and 2–4s on
   cards, never lingering.
7. **Assemble in three parts and concat.** Part A = teardown clips + captions + VO (fade in,
   NO fade out). Part B = the user's testimonial reel appended with ITS OWN audio, loudnorm'd
   to match, lightly branded (thin top bar + site watermark placed so it doesn't cover the
   reel's own lower-thirds). Part C = the user's end-card/CTA (silent, fade to black). Concat
   A+B+C with matched codec params (h264 yuv420p 1920×1080 30fps, aac 48k stereo). If the
   user has no reel, end on the CTA card and cut the handoff line.
8. **QC + package.** Audio present across all segments, seams correct, ~−16 LUFS, no black
   frames. Keyword-led title ("`<Competitor>` Reviews …"), description first line restates the
   keyword and says every review shown is real and sourced, chapters, tags, a hook thumbnail,
   and the user's site linked.

## Rules
- Real, verified, attributable reviews only. The on-screen negatives are the competitor's
  own customers' words, with the source visible.
- Be honest about the overall rating; win on the pattern in the complaints, not on a false
  "universally hated" impression.
- Real screenshots for the review proof — never generated or edited review UI.
- The "alternative" is the user's business and every claimed strength must be true; append
  the user's REAL testimonial reel or skip the beat. Never fabricate testimonials.
- Faceless VO montage: no avatar needed. Keep it fast; never hold one review more than a few
  seconds.
