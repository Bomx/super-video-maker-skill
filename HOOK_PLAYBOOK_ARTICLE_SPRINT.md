# HOOK & SCRIPT PLAYBOOK — misotts-article-sprint v3

The canonical writing guide for the 26s avatar-hook + article-whip-scroll short. A writer (or LLM prompt) should be able to follow this mechanically.

**Format recap:** 5s spoken HOOK (AI floating head over the article title view) → head vanishes → whip-scroll through the REAL published article, one proof "receipt" card (pricing-page crop) per beat → CTA card ("link in bio"). Speaker is a **third-party creator reacting to an article**, never the author.

**Hard constraints (never violate):**
- Hook: spoken, ≤11 words (target 8–10), fits a 5s lip-synced clip
- Body: 3–4 beats × 10–14 words; CTA 10–12 words; **total script ≤70 words** (150 wpm ceiling for 26s)
- TTS safety: Ahrefs is BANNED; SEMrush is always written "Sem-rush"; numbers written phonetically in VO ("one thirty nine") but rendered as numerals on screen ("$139")
- Every body beat anchors to ONE concrete article fact that a single screenshot can prove
- One number per spoken line; **never two similar-sounding numbers in one line** (validated runbook rule — the old b3 "a hundred forty… one thirty nine" violated it)

**The core thesis (from all three inputs):** the screen already says WHAT (the article title is on screen at frame 1) — the voice's only job is the FIGHT the title doesn't contain. A hook is a fight, not a fact. Beats are an argument with a reversal, not a list. The CTA cashes a hole the script dug on purpose.

---

---

## 0. TOPIC ANGLE BEFORE COPY (owner rule, 2026-06-11 — overrides everything below)

Copy mechanics cannot rescue a boring topic. The v3→v4 lesson: the price-fight script was mechanically perfect and still dull, because **"pricing" is not a topic people feel**. Before picking a hook family, pick an ANGLE that injects cultural heat into the article:

- **Viral-entity delegation (F9, the house default):** hand the article's job to a culturally hot entity (Claude, ChatGPT) and report what IT chose. "I asked Claude to audit my SEO. Here's what it picked."
- **Trend-jack:** tie the article to something currently exploding in the niche.
- **Named-character stakes:** a real persona doing something with consequences (the original "My Chief of SEO, Claude Fable 5" energy).

Litmus: would the hook work as a text to a friend? "SEO tools average $137" — no. "I asked Claude to audit my SEO" — yes, because a famous character did something and the result is unknown. THEN apply the families and rules below to the chosen angle.

**MANDATORY for first/welcome videos of ANY business:** the hook MUST be the Claude-delegation opener "So I asked Claude for the best <X>..." — make it literally true with a real grounded Claude call (welcome_pipeline.py claude_pick stage). Below is the general family.

### F9 — Viral-Entity Delegation (added 2026-06-11, validated in v4)
**Mechanism:** borrowed cultural salience (the entity is already in the viewer's feed) × outsourced authority (an AI has no sales agenda) × curiosity gap (what did it pick?). The list-body format is native: each beat = one of the entity's picks WITH ITS REASON ("X, because it does Y for you" — outcome, not spec).
**Templates:**
- "I asked Claude to [do the article's job]. Here's what it picked."
- "Claude read this [ranking/guide]. Its picks surprised me."
- "[Hot entity] just chose my [category] for me."
**Hard rules:**
1. **The claim must be LITERALLY TRUE.** Actually run the delegation — one Claude API call per article (give it the article facts, ask for ranked picks + reasons + a start-today choice) and SAVE the artifact (see claude_picks.json in the pilot job; includes model + request_id provenance). In DFY this is one cheap structured-output call in the pipeline. Never fabricate an entity's endorsement; never show a fake entity UI (rule 46).
2. Feature only the entity's TTS-safe picks (it returns 5 ranked; pick 3 pronounceable ones — still genuinely its picks).
3. Entity name is never spoken word 1 (stakes word first: "I asked Claude…").
4. The reversal beat writes itself: what the entity SKIPPED (the expensive incumbent) — receipt: the incumbent's price tag.
**Suits:** any article whose job an AI could plausibly be asked to do (tool roundups, how-tos, strategy guides) — which is most DFY articles.

### Worked example C — the v4 production script (F9, 63 words)
| Beat | Line | Receipt |
|---|---|---|
| hook (11w) | "I asked Claude to audit my SEO. Here's what it picked." | article title view + floating head |
| b1 (12w) | "It read this ranking of ten tools. Its top three are all free." | ranked list pan |
| b2 (10w) | "Google Search Console first: indexing data straight from Google itself." | GSC official page card |
| b3 (10w) | "Then Screaming Frog, which crawls your whole site for free." | SF free-tier pricing card |
| b4 (10w) | "The one-forty-a-month favorite? Claude didn't even rank it." | SEMrush $139.95 card (the spurned incumbent) |
| cta (11w) | "Number one on the actual ranking? That's in the article. Bio." | "THE ACTUAL #1 / is in the article / LINK IN BIO" card |
Loop accounting: hook opens "what did Claude pick?" → b2-b3 pay it → b4 reversal (incumbent snubbed) → CTA opens "what's the article's #1?" (≠ Claude's pick — true withhold) → article cashes it.

## 1. Hook Families (8 + F9 above)

Source tags: **[HB]** = owner's 1000-hook bank (viral-hooks.txt distillation), **[WR]** = web research (vidIQ/Buffer/OpusClip/SEJ/Shortimize), **[SD]** = script-doctor autopsy.

### F1 — Two-Number Collision *(the default; strongest fit for the receipts format)*
**Mechanism:** one number is information; two dissimilar numbers in tension is a story — and one of them implicates the viewer's wallet. Both numbers get their own receipt on screen, so the hook is natively provable. [SD Rule 1, HB #11/#12, WR "specific numbers beat adjectives"]
**Templates:**
- "They want [big price] a month. You need [small price]." [SD]
- "One month of [pricey tool] buys [N] months of [cheap tool]." [HB #12] *(verify the math: N × cheap < pricey)*
- "This [thing] costs [big price]. This one, [small price]." [HB #11]
**Suits:** pricing roundups, "best X tools," alternatives/cost-comparison articles — anything with two real prices.

### F2 — Myth-Bust / De-influence
**Mechanism:** contradiction creates cognitive dissonance the brain must resolve; strongest pattern interrupt for business content. [HB #16/#17/#18, WR OpusClip+Buffer]
**Templates:**
- "They say good [X] is expensive. That's a lie."
- "Let me de-influence you from overpaying for [X]."
- "It might be time to cancel your expensive [X] subscription."
**Suits:** any listicle where cheap/free options rank high; "alternatives to X"; mistake/myth articles.

### F3 — Receipts Witness
**Mechanism:** announces the format's own proof mechanic; the third-party presenter's version of transgression is *catching something* and verifying it out loud. Builds trust + curiosity simultaneously. [HB #21, SD Rule 2 + §3.6]
**Templates:**
- "A [cheap thing] beats the big names. I have receipts."
- "This article just made [N] expensive [things] look stupid."
- "[Bold article claim]. I checked. It's all right there."
**Suits:** data-driven rankings, "we tested N" articles, stat roundups.

### F4 — Gatekeeper Command
**Mechanism:** loss aversion + direct command; the whip-scroll literally IS the promised object, so the payoff is structural. [HB #20, WR SEJ "direct stake"]
**Templates:**
- "Don't buy [category] until you've seen this ranking."
- "Stop paying for [X] before you read this article."
**Suits:** buyer-guide listicles, comparisons, pricing guides. Cleanest hook→scroll handoff in the bank.

### F5 — Underdog Reveal
**Mechanism:** insider-gift status + a *named withhold* (you know a sleeper exists but not which one) — the textbook "tease the best item" micro-loop. [HB #9, WR Shortimize, SD b4 "the one good instinct"]
**Templates:**
- "Putting you on a [category] most people have never heard of."
- "The cheapest [thing] in this ranking embarrassed the famous ones."
**Suits:** sleeper-pick listicles, hidden-gem roundups, niche-tool articles.

### F6 — Shock-Stat with a Stake
**Mechanism:** the surprising-stat formula — but ONLY with immediate self-relevance attached. A bare stat (the old control hook) is banned; the stat must point at the viewer or a victim. [HB #22/#5, WR SEJ "direct stake" formula]
**Templates:**
- "I was shocked when I saw what [X] costs now."
- "Why does nobody talk about the cost of [X]?"
- "If you pay for [X], check your invoice after this."
**Suits:** pricing studies, industry benchmarks, original-data articles. Use only when the stat is screenshot-provable (an *average* is not).

### F7 — Zero-Dollar Possibility
**Mechanism:** a dream-result question opens a yes/no loop the free-tier receipt answers; "free" is the one price every niche's audience feels. [HB #2/#3/#23]
**Templates:**
- "Is it possible to [outcome] without spending a dollar?"
- "What if you could [outcome] for [tiny price]?"
- "This is what zero dollars gets you in [category]."
**Suits:** free-tools roundups, budget guides, articles with a free tier or free winner.

### F8 — Not-Sponsored Independence
**Mechanism:** implied independence = trust + conflict with a brand; the soft version of "they don't want you to see this," kept receipt-true (no defamation). [HB #25, SD §3 frame-1 rules]
**Templates:**
- "Nobody sponsored this. Let's talk about [brand]'s real pricing."
- "This article won't make [brand] happy. Here's the receipt."
**Suits:** incumbent-vs-challenger comparisons, "alternatives to [big brand]" articles. **Caution:** never a brand as the first spoken word (highest-attention syllable + highest TTS risk); only claims a pricing screenshot can back.

---

## 2. Script Formula — the 6-beat arc

The arc is **setup → escalation → reversal**, never a flat list. Run the **shuffle test**: if b2–b4 can be reordered without breaking, rewrite — order must be load-bearing.

| Beat | Time | Words | Job | Receipt on screen |
|---|---|---|---|---|
| **HOOK** | 0–5s | ≤11 (aim 8–10) | Open the fight. Two channels: title view shows WHAT, voice carries WHY IT MATTERS. Ends owing the viewer something (which tool? what upset?). | Article title view + conflict badge (numerals, top third) |
| **b1** | ~5–10s | 10–14 | Name the artifact + state the RESULT (thesis), not the methodology. Broad→narrow here, not in the hook. Plant the withhold tease. | Article list/rank view, relevant rows highlighted |
| **b2** | ~10–14s | 10–14 | The floor: free/cheapest baseline. One number + its enemy. | Pricing crop proving that exact number |
| **b3** | ~14–19s | 10–14 | The incumbent set-up: give a verdict ("the gold standard") and point at the evidence OUT LOUD ("pricing page, right there"). This beat exists to be upset. | Incumbent pricing-page crop |
| **b4** | ~19–23s | 10–14 | The REVERSAL — the payoff of the hook's loop. Best fact of the article lives here. Strongest verb of the script lives here. | Underdog pricing crop (cropped to ONLY the proven number) |
| **CTA** | ~23–26s | 10–12 | Cash the withhold. Point at a specific named hole, not "read more." | CTA card; echo the hook's numeral for loop-back |

**Writing rules (apply mechanically):**
1. **Screenshot-provable rule:** the central claim of every beat must be provable by ONE screenshot crop. If no crop can prove it, cut the claim. (The old "$137 average" hook failed this — an average is the one number no pricing page shows.)
2. **One number per line.** Every number needs an enemy: another number, "free," or "your invoice." A number without a referent is noise. Never two similar-sounding numbers in one line (hard rule).
3. **Numbers:** phonetic in VO, numerals on screen. Burn the hook as bold on-screen text (3–7 words, top third, numerals) — 60–75% watch muted; if the hook isn't on screen, it doesn't exist. [WR]
4. **Verbs:** use *beats, undercuts, charges, caught, cancels, embarrassed, out-crawls, won, shows up*. Ban *averages, tested, held up, has*; *is* only for a verdict ("is the gold standard").
5. **No "And"/"So" beat openers** — connective openers signal list-reading mode. (CTA may open with "And" as a deliberate escalation riding b4's reversal.)
6. **Witness out loud, once or twice:** the VO must acknowledge the receipt ("pricing page, right there") — the format's premise is verification, and it must exist in the audio track.
7. **Micro open loop every beat** (~every 5–8s): tease the sleeper early, escalate prices/value beat to beat, hold the best for b4. [WR Shortimize]
8. **Hook-delivery check:** after writing the body, reread the hook and verify every beat services its promise. The #1 script-level retention killer is the hook-delivery gap. [WR SEJ]
9. **Vary sentence shape** — question, fragment, long-short. Three identically shaped beats is a lullaby. [SD]
10. **Withhold verification:** the CTA's withheld claim must be TRUE against the actual article (check the real #1 before locking the CTA) — or the receipts format eats itself.

**Frame-1 / visual rules (brief to the editor alongside the script):**
- First spoken word = a **stakes word** ("They," "Stop," "Don't," "This," "Nobody") — never the category noun, never a brand. First karaoke caption word = that same stakes word.
- Head already mid-speech at frame 1; first syllable lands within ~0.3s. A mouth-closed floating head is a swipe.
- Badge carries **conflict, not category**: "$139 vs $18", not "SEO TOOLS · 2026 PRICING."
- 3 visual events per beat (scroll motion + receipt punch-in + price highlight) to hit the 1–2s change cadence. [WR]
- Mute test / blind test: muted, the title tells you the topic; blind, the voice tells you the fight. If both channels say the same thing, the brain files it as an ad in ~0.4s.

**Benchmarks:** ≥70% viewed-vs-swiped; ≥60% retention at 3s or the hook gets rewritten; test 3–5 hook variants changing ONLY the hook. [WR]

---

## 3. Banned Moves

Each with the crime scene from the current control script:

1. **The bare average / stat-with-no-victim.** "SEO audit tools now average $137 a month" — nobody pays the average, no card gets charged $137, and no screenshot can prove it. If the hook is a stat, it needs a victim or a "you."
2. **Topic label as word 1 / voice duplicating the screen.** "SEO audit tools…" while the title view already says "Best SEO Audit Tools." Viewer has categorized and skipped by word three.
3. **Closed-sentence hooks.** The control hook is grammatically and informationally complete — nothing promised, no reason for second 6 to exist. The hook must end in debt.
4. **"So"/"And" beat openers.** Three of four control beats ("So this new ranking…", "And Sem-rush…", "And Sitebulb…").
5. **Methodology as content.** "So this new ranking tested ten of them" — describes the article's *existence*; nobody doubts a listicle exists.
6. **Spec reads with no verdict.** "Screaming Frog still crawls five hundred URLs for free" — is 500 a lot? Against what? The presenter's one job is to have an opinion.
7. **Two similar numbers in one line.** "checks 140 issue types, at one thirty nine" — TTS hazard + comprehension hazard. Hard violation.
8. **Number soup.** 137, 10, 500, 140, 139 in 15 seconds with no referents — numbers decay into static.
9. **Shuffle-proof beats.** Control b2/b3/b4 reorder freely = brochure, not story.
10. **Wasting the upset.** "Sitebulb is the sleeper" used as garnish on beat 4 instead of being the spine of the video.
11. **Closed-loop, brand-first CTA.** "The full top ten is on the Distrib blog" — the video already crowned its winner, so there is nothing left to cash; and it sells the publisher, not the payoff.
12. **Receipt-contradicting claims.** Saying "250K URLs" over a Sitebulb Lite crop that reads "10,000 URLs/audit." Crop to the price only, or rephrase.
13. **Greetings, slow builds, buried ledes, two-idea hooks, clickbait mismatch, self-falsifying promises** ("in 60 seconds" on a 26s video). [WR]
14. **TTS landmines:** Ahrefs anywhere; brand as the first spoken word; unspelled "SEMrush."

---

## 4. CTA Patterns (ranked)

All: last ~4s, one explicit action, 10–12 words, withhold verified true against the article.

1. **The Withheld Crown** *(default — link in bio)*: "And number one beats all three of these. Article's in the bio."
   The script deliberately reveals 3 of 10 and crowns none of them as #1. Cashes the hole exactly. **Rule:** if the article's actual #1 IS a tool named in the body, pick a different withhold (see #2).
2. **The Negative Withhold** *(link in bio, when the winner was already revealed)*: "The article names the one tool to cancel first. Link in bio."
   Loss-framed withhold; works when b4 already crowned the winner. Verify the article actually makes that call.
3. **Comment-Gated** *(only when fulfillable)*: "Comment AUDIT and I'll send you the full ranking."
   Comments boost distribution, but ONLY use when an auto-DM or a human will actually fulfill — unfulfilled comment gates are bait-and-switch and decay the account. Ranked last because this is a DFY format across customer niches and fulfillment is per-account.

**Anti-pattern:** "Full list on the [brand] blog" homework CTAs — see Banned Move #11.
**Optional polish:** echo the hook's numeral on the CTA card ("$139 vs $18") so the last frame loops conceptually into the first (unconscious-replay trigger). Low priority vs. the conversion CTA. [WR]

---

## 5. Worked Example — "Best SEO Audit Tools: 10 Top Picks for 2026"

Facts available: avg $137/mo · Screaming Frog free for 500 URLs · SEMrush $139.95/mo + 140 issue types · Sitebulb $18/mo + 250K-URL cloud crawl · 10 tools ranked.

### 10 hook candidates (all ≤11 words, TTS-safe, word counts verified)

| # | Family | Hook | Words |
|---|---|---|---|
| 1 | F1 Collision | "They want one thirty nine a month. You need eighteen." | 10 |
| 2 | F1 Collision | "One month of Sem-rush buys you seven months of Sitebulb." | 10 |
| 3 | F2 Myth-Bust | "They say good SEO tools are expensive. That's a lie." | 10 |
| 4 | F2 Myth-Bust | "Let me de-influence you from overpaying for SEO audit tools." | 10 |
| 5 | F3 Witness | "An eighteen-dollar tool beats the big names. I have receipts." | 10 |
| 6 | F3 Witness | "This article just made three expensive tools look stupid." | 9 |
| 7 | F4 Gatekeeper | "Don't buy an SEO tool until you've seen this ranking." | 10 |
| 8 | F5 Underdog | "Putting you on an SEO tool you've never heard of." | 10 |
| 9 | F6 Shock+Stake | "I was shocked when I saw what audit tools cost now." | 11 |
| 10 | F7 Zero-Dollar | "Is it possible to audit your whole site for zero dollars?" | 11 |

(Candidate #2 math verified: 7 × $18 = $126 < $139.95.)

### Winner A — Two-Number Collision (the price-fight upset arc)

Frame-1 badge: **"$139 vs $18"** · first karaoke word: **THEY** · 67 words total.

| Beat | Line | Receipt |
|---|---|---|
| **hook** (10w) | "They want one thirty nine a month. You need eighteen." | Article title view + "$139 vs $18" badge |
| **b1** (11w) | "This ranking put ten audit tools head-to-head. The cheap ones won." | Pan down the article's ranked list, low-price tools highlighted |
| **b2** (10w) | "Screaming Frog crawls five hundred URLs and charges you nothing." | Screaming Frog free-tier crop ($0 line) |
| **b3** (12w) | "Sem-rush is the gold standard. Pricing page, right there: one thirty nine." | SEMrush $139.95/mo pricing crop |
| **b4** (12w) | "Then Sitebulb shows up at eighteen and out-crawls it. That's the upset." | Sitebulb $18 crop — **price only, exclude the Lite 10K-URLs line** |
| **cta** (12w) | "And number one beats all three of these. Article's in the bio." | CTA card echoing "$139 vs $18" + link-in-bio |

Loop accounting: hook opens "which $18 tool?" → b4 pays it → CTA opens "what's #1?" → article cashes it. Order is load-bearing (b4 only makes sense after b3 crowns the gold standard). **Pre-flight: verify the article's actual #1 is not Screaming Frog, Sem-rush, or Sitebulb; if it is, switch to the Negative Withhold CTA.**

### Winner B — Zero-Dollar Possibility (the free-first optimism arc)

Frame-1 badge: **"$0 AUDIT?!"** (the badge carries the mute-viewer hook since "Is" is a soft stakes word) · 69 words total.

| Beat | Line | Receipt |
|---|---|---|
| **hook** (11w) | "Is it possible to audit your whole site for zero dollars?" | Article title view + "$0 AUDIT?!" badge |
| **b1** (12w) | "This ranking put ten tools head-to-head. A free one made the cut." | Article list view, Screaming Frog's row highlighted |
| **b2** (10w) | "Screaming Frog crawls five hundred URLs. The price? Literally nothing." | Screaming Frog free-tier crop |
| **b3** (12w) | "Paying gets you deeper checks. Sem-rush charges one thirty nine for those." | SEMrush $139.95/mo pricing crop |
| **b4** (13w) | "But the loophole is Sitebulb: eighteen a month for a full deep crawler." | Sitebulb $18 crop — price only |
| **cta** (11w) | "The article shows exactly where free stops working. Link in bio." | CTA card + link-in-bio |

Arc: question (free?) → yes, proof → the catch (what money buys) → the loophole (cheap middle path) → withhold = the free-tier ceiling (true per the article's 500-URL cap). Different family, different emotional angle from A: optimism-with-a-catch vs. accusation-and-upset.

**Why these two:** A is the autopsy's validated spine (the $139-vs-$18 collision IS the article's story) and the strongest receipt-native hook; B opens on the broadest possible pain (money/free) per the lead-broad-then-narrow rule, generalizes best as a template across customer niches, and shares zero hook DNA with A — ideal for the change-only-the-hook A/B test.

---

## Pre-flight checklist (run on every script before render)

- [ ] Hook ≤11 words; word 1 is a stakes word, not a category noun or brand
- [ ] Total ≤70 words; beats 10–14; CTA 10–12
- [ ] No Ahrefs; "Sem-rush" spelled; all VO numbers phonetic; on-screen numbers numerals
- [ ] One number per line; no two similar-sounding numbers anywhere
- [ ] Every beat's claim provable by one screenshot; crops exclude contradicting lines
- [ ] No "And"/"So" beat openers; shuffle test fails (good); reversal lives in b4
- [ ] VO points at a receipt at least once ("right there")
- [ ] Hook promise paid off by the beats (reread hook last)
- [ ] CTA withhold verified TRUE against the published article
- [ ] Frame 1: head mid-speech (<0.3s to first syllable), conflict badge top third, mute test + blind test both pass