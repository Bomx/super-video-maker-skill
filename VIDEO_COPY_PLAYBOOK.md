# VIDEO COPY PLAYBOOK: writing the words before building the frames

The copy layer for every recipe in this skill. Adapted from the `copywriting-skill`
(conversational, analogy-led, benefit-first, credibility-protected) to the one thing
prose copy never has to solve: **two tracks running at once.**

> **Read order.** This file = what the words SAY and which track owns them.
> `SPOKEN_VO_HUMANIZER.md` = how a spoken line SOUNDS (12 rules, banned AI tells).
> `HOOK_PLAYBOOK_ARTICLE_SPRINT.md` = hook families and the angle-before-copy rule.
> `LIVING_CANVAS_PLAYBOOK.md` §4 = story cold-open structure and announcer cadence.
> This file governs; those three specialize. When they disagree, the more specific file wins.

**Copy is a production gate, not a garnish.** Nothing gets generated (no TTS call, no
Seedance clip, no Remotion timeline) until the spine below is written down. In the
living-canvas pipeline the VO literally becomes the timeline, so a script rewrite after
the build re-locks every frame number. Copy first is not a style preference, it is the
cheapest ordering.

---

## 1. The spine (write these four lines before anything else)

Straight from the copywriting skill, unchanged, because they survive the medium:

- **One viewer.** Who should feel recognized in the first two seconds?
- **One promise.** What useful result should they want by the end?
- **One mechanism.** Why does this actually work? Name it in plain language.
- **One next step.** What single thing should they do?

If you cannot write these four lines from the source material, you do not have a video
yet. You have footage.

**The angle gate (from the hook playbook, and it overrides everything here):** copy
mechanics cannot rescue a boring topic. "SEO tools average $137" is mechanically fine and
culturally dead. "I asked Claude to audit my SEO" is a famous character doing something
with an unknown result. Pick the angle first, then apply the craft.

---

## 2. Two tracks, one argument

The single biggest difference between page copy and video copy: **a viewer cannot read
and listen to the same sentence.** Whatever the screen already says, the voice must not
repeat. Redundancy across tracks is the most common reason a technically clean video
feels flat.

| Track | Owns | Never does |
|---|---|---|
| **Voice** | The argument, the reversal, the mechanism, the emotional stance, the next step | Read the on-screen headline aloud. Recite numbers the screen is already showing in full |
| **Screen** | The evidence, the numbers, the proof surface, the punchline, the name of the thing | Carry a full sentence the voice is also speaking. Explain a mechanism in paragraph form |

Working example from the Copilot-playbook build. The screen holds the article title at
frame one, so the voice never says the title. The screen shows the dashboard reading
14.7K, so the voice says the number once, as a claim, while the camera punches into the
badge that proves it. The screen delivers the joke ("IDENTICAL · MONTH 6") in near
silence, because a punchline the voice explains is a punchline that died.

**The division test:** mute the video. If the story still roughly tracks, the screen is
carrying its weight. Now blank the screen. If the argument still lands, the voice is
carrying its weight. If either test fails, one track is decorating rather than working.

---

## 3. Spoken copy

Everything in the copywriting skill's voice and rhythm sections applies, with these
video-specific overrides:

- **Word budget is time.** About 150 wpm. 25s is 60 to 65 words, 30s is 75 to 85, 60s is
  roughly 150. Cut a beat before you compress sentences into fragments. Squeezing four
  items into telegraphic stubs is how scripts get rejected.
- **Clipped clauses in the pitch half, full sentences in the story half.** The announcer
  register runs 2-second clauses, second person, present tense, zero hedging. The story
  register is first person and conversational. Keep the step between them deliberate.
- **Never write a colon.** Nobody speaks "Tool: what it does." Rewrite as a sentence with
  a verb and a "you."
- **One emotion drives the whole script.** Neutral fact recitation is the loudest AI tell.
- **Numbers get spoken, not printed.** Write "fourteen thousand" for the TTS and let the
  screen render "14,000". Never put two similar-sounding numbers in one spoken line.
- **Read it aloud at performance pace before generating audio.** Anything you stumble on
  gets rewritten. This is the same "read the draft aloud" gate from the copywriting skill,
  and in video it is not optional because the audio costs money to regenerate.

See `SPOKEN_VO_HUMANIZER.md` for the full 12 rules and the banned-tells list.

---

## 4. On-screen copy (the gap prose copywriting does not cover)

The living-canvas playbook specifies how words move. This section specifies what they say.

**Kinetic headlines.** Three to nine words. One idea. Built as a contrast when possible,
because contrast is what survives being read in under two seconds:

> You do not [common ineffective approach].
> You [better approach] by [simple mechanism].

The shipped example: "Copilot doesn't count your posts. It counts your proof." Same
noun repeated, verb flipped, mechanism named. Exactly one accent-colored phrase per
headline, and it lands on the word that carries the argument, never on a decorative one.

**Data badges are evidence, not adjectives.** A badge says `POSITION 11`, not
`Great ranking`. If a number is on screen, it must be traceable to a real artifact.
Screenshot numbers are the strongest form: they are the receipt.

**Ghost chapter titles** name the beat in one word (QUESTIONS, ANSWER, CLUSTER, LINKS,
PITCH, UPDATE, RERUN, PROOF). One word, always a noun, never a sentence. They replace
title cards, so they must be legible as a table of contents if you paused the whole video.

**Microcopy and asides** are where personality lives, because the headline has no room
for it. One per video, maximum, and it must be true: "(sorry, Competitor A.)" works.
A second aside reads as a tic.

**The end card carries the offer**, and it obeys the copywriting skill's offer rules
exactly: what happens, what they receive, how much effort. Statement pills, three
maximum, each a concrete deliverable ("Free 90 day tracker", "31 dated tasks",
"Runs on autopilot"), never an adjective pile.

**The typographic strike** is the on-screen version of the contrast pattern: the corrected
word lands, a bar draws through the old word, and the old word dims. "Get ~~read.~~
cited." It compresses a whole reframe into one line, which is the only kind of reframe
that fits on an end card.

---

## 5. Hooks

A hook is a fight, not a fact. The screen usually already states the WHAT, so the voice's
only job is the tension the title does not contain.

- Eight to eleven words if spoken over a lip-synced clip.
- The stakes word comes first, never the brand or entity name.
- Open with a desirable result, an honest surprise, or a familiar truth (the copywriting
  skill's three openers, all of which survive the jump to video).
- Write at least five variants across different families before producing any paid asset:
  confession, contrarian, problem-callout, receipt, demo-first, curiosity gap, speedrun,
  before-and-after, viral-entity delegation.
- Litmus: would you send this hook as a text to a friend?

Full families, templates, and the loop-accounting method live in
`HOOK_PLAYBOOK_ARTICLE_SPRINT.md`.

---

## 6. Format arcs

Each recipe compresses the spine differently. Omit beats that do not fit rather than
padding to hit the shape.

| Format | Arc |
|---|---|
| **Living-canvas explainer (60 to 80s)** | Story cold-open with a visual punchline → dark-turn thesis → reveal → 4 to 6 mechanism chapters, one per feature → payoff beat → proof → CTA end card |
| **Avatar explainer** | Hook → spoken avatar disclosure → news or claim beat → concrete story → source receipt on screen → action step → spoken CTA tail |
| **UGC ad** | Pattern-interrupt hook → painfully specific problem → personal discovery or demo → mechanism → believable proof → objection handled → one CTA. One ad, one angle, one promise |
| **Article sprint short (26s)** | Spoken hook ≤11 words → 3 to 4 beats of 10 to 14 words, each anchored to one provable article fact → CTA that cashes a hole the script dug on purpose |
| **Explainer or teaching reel** | Familiar example → question → insight → mechanism → evidence → practical takeaway. Teach first, and do not force a CTA the piece does not need |

**The withhold.** In short formats the CTA should cash a curiosity gap the script opened
deliberately and did not close. That is different from withholding the payoff, which just
annoys people. Open a second loop, then point at where it gets closed.

---

## 7. Credibility (non-negotiable, and stricter than prose)

Every rule in the copywriting skill's credibility section applies, and video adds teeth:
**a claim on screen is a claim with a receipt attached.** The format implies proof, which
means a fabricated number is worse here than in prose.

- Never invent a statistic, customer result, price, deadline, ranking, or endorsement.
- If a video claims an AI picked something, actually run the call and save the artifact.
  Never fabricate an entity's endorsement, never mock up a fake product UI for a real
  company.
- Prefer real screenshots over redrawn mockups when the number is the point. A real
  dashboard reading 14.7K is proof. A skeleton card reading 14.7K is set dressing.
- Preserve qualifiers ("typically", "can", "may"). Distinguish an example from a
  documented result.
- Use placeholders (`[customer result]`, `[price]`) rather than plausible inventions, and
  surface them to the user before render.
- Competitor footage is analysis-only. Never composite competitor pixels or ask a model to
  match a competitor frame.

---

## 8. House copy rules

- **No em dashes** in any deliverable copy. Rewrite with a period, comma, colon,
  parentheses, or a conjunction. In a VO script a dash used as pause notation for the
  performer is fine, since it never reaches the viewer. The banned thing is the written
  contrast-pivot cadence.
- **No emoji as icons** in on-screen copy or end cards.
- **No corporate filler**: game-changing, revolutionary, unlock, leverage, seamless,
  robust, elevate, supercharge, delve, dive in.
- **No forced rule-of-three.** The "fast, simple, and free" comma-list rhythm is the
  single loudest slop tell, and it sounds worse spoken than written.
- **No synonym cycling.** Pick one term for the thing and repeat it. The tool stays the
  tool, not the platform, then the solution.
- **Approved copy ships verbatim.** If the user has signed off on a line, do not
  "improve" it during assembly.

---

## 9. Copy gate (run before the first paid generation call)

- [ ] The four spine lines are written down
- [ ] The angle would survive being texted to a friend
- [ ] Voice and screen never carry the same sentence
- [ ] Mute test and blank-screen test both pass
- [ ] Word count matches the runtime at 150 wpm
- [ ] Every number and claim traces to a real artifact, with placeholders for the rest
- [ ] Exactly one accent phrase per on-screen headline
- [ ] The end card states what happens, what they receive, and the effort involved
- [ ] One call to action, singular and concrete
- [ ] Script read aloud at performance pace with no stumbles
- [ ] No em dashes, no filler, no forced triads, no synonym cycling

---

## 10. Worked example (25s vertical short, 63 words)

Source: the "14K AI Mentions in Microsoft Copilot" article and the 77s living-canvas
master built from it. Shows the two-track split, the word budget, and the credibility
mechanic in one page.

**Spine.** One viewer: a founder publishing constantly whose company never appears in AI
answers. One promise: get cited by Copilot. One mechanism: AI counts proof, not volume.
One next step: take the free 90 day tracker.

| Beat | VOICE (argument) | SCREEN (evidence) |
|---|---|---|
| hook 0-2.5s | "We published for six months. Copilot still never mentioned us." | Calendar filling with posts, counter climbing |
| b1 2.5-7s | "Turns out it doesn't count how much you publish. It counts proof." | The Copilot answer, same three brands, badge `IDENTICAL` |
| b2 7-15s | "So we stopped writing more posts, and started writing pages it could actually quote, with the sources right there." | Real page, quote block outlined, SOURCES chips landing |
| b3 15-20s | "Then we earned links to them. Fourteen thousand citations later." | Real dashboard, camera punch into `14.7K Total Citations` |
| cta 20-25s | "Ninety day plan's free, thirty one dated tasks. Link's in my bio." | End card: `Get [struck]read.[/struck] cited.` + tracker pills |

**Why it passes the gate.**

- **Two tracks never overlap.** The voice never reads a badge aloud. The screen never
  spells out the mechanism. Mute it and the story still tracks from full calendar to
  climbing dashboard. Blank it and the argument still lands.
- **Rhythm is varied on purpose.** Line lengths run 10, 12, 19, 10, 12 words, with a
  three-word punch ("It counts proof.") against a nineteen-word explanation. Uniform
  clipped lines read as robotic no matter how short they are.
- **Connective tissue in every beat**: "Turns out", "So", "Then". No zero-connector
  islands.
- **Numbers are written as spoken** for the TTS ("Fourteen thousand", "Ninety day",
  "thirty one") while the screen renders the numerals.
- **The credibility split.** The voice says "fourteen thousand" and the screen carries the
  precise attribution (14.7K, from Copilot and its partners, six months). Splitting the
  claim across tracks is how you stay honest and still land a round number out loud.
- **The CTA folds into the final thought.** One payoff and one action in a single breath,
  never an appended telegraphic fragment.
- **Anything unverified stays a placeholder.** If a specific post count or customer result
  is not confirmed, write `[N]` and surface it before render rather than picking a
  plausible number.
