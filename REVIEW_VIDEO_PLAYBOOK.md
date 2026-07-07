# Review-Conquest Compilation Playbook (`/review-video`)

Turn the keyword **"<Competitor> reviews"** into a fast, faceless voiceover montage of
**real, verified** competitor reviews that names the recurring complaints and positions
**the user's own business** as the alternative that fixes them — then hands the mic to the
user's own customer testimonials and ends on the user's CTA.

This is honest comparative/conquest marketing. It ranks for a high-intent keyword (people
searching "<competitor> reviews" are mid-decision) and converts by pairing the competitor's
*own customers' words* with a truthful "here's the tool that closes exactly these gaps."

**The business at the end is a variable, not a constant.** Everywhere this playbook says
"the user's business," it means whatever business the operator supplies (or, when driven from
the Distribb skill, the connected project's `business-context`). Do not hardcode any specific
company. The example that seeded this playbook happened to push Distribb; the workflow itself
pushes *whoever is running it*.

## When to use / not use
- **Use** when a named competitor has a real, findable body of reviews (Trustpilot, G2,
  Capterra, an app store, Reddit, review blogs, YouTube) and the user has a genuinely
  differentiated product that addresses the recurring complaints.
- **Do not use** if the competitor has little or no genuine critical-review volume — you would
  have to manufacture negatives, which is out of bounds. Tell the user and stop.
- **Do not use** to attack a person, or to make claims the user's product can't truthfully back.

## The guardrail (this is what keeps the video legal and effective)
1. **Only real, verified, attributable reviews go on screen.** Never invent, embellish,
   paraphrase-and-quote-mark, or doctor a screenshot. The on-screen negative is the
   competitor's *own customer's* words, with the source visible.
2. **Be honest about the overall picture.** If the competitor is 4.8★, say so — the angle is
   "look at the *pattern* inside the 1–2★ tail; that pattern is the exact thing we fix," not
   "everyone hates them." A false "universally hated" impression is both untrue and legally
   exposed (defamation / false advertising / comparative-ad rules).
3. **The alternative must be real too.** Every strength you claim for the user's business has to
   be true and, ideally, provable on screen (product screenshots, the user's own testimonials).
   Never fabricate the user's testimonials — append the user's *real* reel or cut that beat.
4. **Truth + sourced opinion is the safe zone.** Verbatim customer reviews (fact: they said it,
   with a link) plus the user's honest product claims (fact: the feature exists) = defensible.

## Inputs (intake)
- **Competitor:** name and/or a review-page URL.
- **The user's business + its real strengths** mapped to the competitor's weak spots (from the
  Distribb skill: `GET /api/v1/business-context`).
- **Optional: the user's own testimonial reel** (an MP4 with its own audio) to append.
- **Platform / ratio / length:** default YouTube long-form **16:9, ~2–4 min** — long-form ranks
  for the "<competitor> reviews" search intent better than a Short. A 9:16 cut-down is optional.
- **Keys:** `ELEVENLABS_API_KEY` for VO (required). Captions can come from ElevenLabs
  timestamps, a local whisper, or `OPENAI_API_KEY`. No HeyGen/Seedance — this is real footage,
  and generated b-roll would undercut the "these are real reviews" premise.

## Phase 1 — Recon
One WebSearch pass to confirm the competitor exists and has findable reviews, and to learn
*where* the reviews live (which app store, whether it's on Trustpilot/G2, active subreddits).
If there's no genuine critical volume, stop here.

## Phase 2 — Research + verification (the heart of it)
This is a multi-modal sweep followed by an adversarial verify. It parallelizes extremely well —
run it as a Workflow (fan-out finders → verify each critical quote → synthesize).

**Finders (one per surface, in parallel):** Trustpilot, G2/Capterra/GetApp/TrustRadius, the
relevant app store (Shopify / WordPress.org / Chrome Web Store), Reddit + Facebook groups +
Quora + forums, third-party review blogs (extract their stated cons), YouTube video reviews
(for spoken criticisms + attributed b-roll), X/LinkedIn. Each returns verbatim quotes with
**author, date, rating, sentiment, theme, and exact source URL**. Prioritize 1–3★ and neutral;
keep 1–2 representative positives per surface for balance.

**Browser, not just fetch.** Many review sites return **403 to automated fetchers** (Trustpilot
especially) or render reviews client-side. Drive a real Chrome session (the Chrome MCP tools) to
open the **star-filtered** views (`?stars=1`, `?stars=2`, `?stars=3`) and read/scroll them. This
is also where you capture the screenshots you'll use as proof later, so do both in one pass.

**Adversarial verification.** For every critical quote, re-open the cited source and confirm the
wording appears **verbatim** and is attributable; **default to reject** if you can't corroborate
it. Mark each `exact` / `close-paraphrase` / `theme-only` / `unconfirmed`. Only `exact`
(and clearly attributable) quotes may appear on screen as quotes; themes-only material can inform
narration but not be shown as a quotation. (In the seeding run this turned 127 "critical" hits
into 31 confirmed, verbatim, sourced quotes — that filter is the product.)

## Phase 3 — Synthesize
- Cluster confirmed reviews into **4–6 themes** (typical: content/output quality, results/ROI,
  support responsiveness, setup/onboarding, billing/trials, missing features).
- **Map each theme to a TRUE strength of the user's business.** This mapping is the spine of the
  script. Only include a mapping the user can defend.
- Pick the **featured on-screen quotes** (verified only), shortest punchiest first.
- Write an **honest sentiment breakdown** (overall rating + the shape of the tail).

## Phase 4 — Script (VO)
Shape:
1. **Hook:** the rating vs. the tail ("4.8 stars… so I read every 1- and 2-star review").
2. **Setup:** what you did (read them all) and what kept coming up.
3. **Gap beats (4–6):** name each recurring gap; put a **real, verified quote on screen**;
   keep the VO one clause per quote — do not linger.
4. **Turn:** "these gaps are the hardest parts of `<category>`."
5. **The alternative = the user's business,** closing each gap in the same order (truthfully).
6. **Handoff to the user's customers:** end the VO on
   *"But don't take my word for it — let's hear from some actual `<Business>` users."*
7. Then the user's testimonial reel plays with its own audio. **End card = the user's CTA/site.**

Keep it fast. No em dashes in the spoken text (they make TTS stumble). **Show the user the
verified reviews + the script before any paid generation.**

## Phase 5 — Produce (faceless VO montage)
- **Screenshots are the proof.** Screenshot the **real** review pages (browser). Never generate
  or edit a review screenshot. Brand lightly: a kicker chip (theme), a small "VERIFIED" tag, and
  the on-screen source (site + author) so the viewer sees it's real. Text cards (hook, turn,
  the alternative, the handoff, the end card) are Pillow/`drawtext` — keep one visual language.
- **VO:** `tools/elevenlabs_voice.py` (reads `ELEVENLABS_API_KEY`). If quota is out, fall back
  to `OPENAI` TTS or, last resort, a local voice for a rough cut.
- **Caption timing:** Whisper the VO for word timestamps (or use ElevenLabs' with-timestamps
  endpoint / a local aligner). Burn beat-locked karaoke captions (bottom-center; see the caption
  rules in `SKILL.md`).
- **Motion:** Ken Burns (fit-to-fill + centre-crop, never pad bars) on screenshots; a gentle zoom
  on text cards. **Cut every 3–6s on screenshots, 2–4s on cards.** Never hold one review long.

## Phase 6 — Assemble in three parts, then concat
The append-the-user's-reel structure is the signature of this format. Build three self-contained
MP4s with **identical codec params** so they concat by copy:

- **Part A — Teardown + VO.** Concat the teardown clips, burn the captions, **fade in ~0.6s at
  the start, NO fade-out at the end** (it flows into B), mux the VO (loudnorm `I=-16:TP=-1.5:LRA=11`,
  to stereo 48k).
- **Part B — The user's testimonial reel.** Scale to 1920×1080 (fit-to-fill), keep **its own
  audio** (loudnorm to the same target so there's no volume jump), and brand *lightly*: a thin
  top accent bar + a small `yoursite.com` watermark **placed to avoid the reel's own
  lower-thirds** (if the reel names people bottom-left, watermark bottom-right). No karaoke
  captions over it — it has its own.
- **Part C — End card.** The user's CTA/site card, ~4s, **silent** (anullsrc stereo), fade to
  black at the end.

Normalize all three to the same target and concat with the demuxer:
`-c:v libx264 -pix_fmt yuv420p -r 30 -s 1920x1080 -c:a aac -ar 48000 -ac 2` on each, then
`ffmpeg -f concat -safe 0 -i list.txt -c copy final.mp4`. If `-c copy` complains about mismatched
params, re-encode the concat once. (Full recipes in `FFMPEG_PLAYBOOK.md`.) If the user has **no
reel**, drop Part B and the handoff line and end on Part C.

## Phase 7 — QC + package
- **QC:** audio present in **every** segment (spot-check mean volume in A, B, and — expect near
  silence — C), seam frames correct (handoff card → reel intro → end card), ~−16 LUFS, no black
  frames, `tools/ffmpeg_qc.py`.
- **Package for the keyword:** title led by **"<Competitor> Reviews"** + the honest angle;
  description first line restates the keyword and states **every review shown is real and
  sourced** (link the sources); chapter timestamps (include the "Real `<Business>` customers"
  testimonial chapter); tags = the keyword + related terms; a hook thumbnail (the rating + "I
  read every 1★ review"); the user's site linked.

## Deliverables
`final/<competitor>_reviews_<business>.mp4`, `captions.ass`, the verified-review inventory (with
source URLs) for the description/pinned comment, and the title/description/tags/chapters.
