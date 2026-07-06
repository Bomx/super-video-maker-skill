# Video Recipes

Machine-readable production recipes for Super Video Maker. Each recipe defines
stages, tools, routing keywords, deliverables, and QC checks so agents pick the
right pipeline before spending credits.

## Commands

```bash
python3 .agents/skills/super-video-maker/tools/video_recipes.py list
python3 .agents/skills/super-video-maker/tools/video_recipes.py show avatar-explainer
python3 .agents/skills/super-video-maker/tools/video_recipes.py match --goal "TikTok ad for waitlist"
python3 .agents/skills/super-video-maker/tools/video_recipes.py plan --recipe ugc-ai-ad --goal "Waitlist ad"
python3 .agents/skills/super-video-maker/tools/video_recipes.py validate
python3 .agents/skills/super-video-maker/tools/video_recipes.py test
```

## Recipe index

| ID | Best for |
|---|---|
| `avatar-explainer` | News/tutorial masters with HeyGen, source deck, spoken CTA |
| `avatar-hook-broll` | 9:16 trend-hook shorts: Seedance avatar hook + fast beat-locked b-roll + comment-gated CTA (DFY `hook_v3` candidate) |
| `misotts-article-sprint` | ~30s 9:16 article-promo short: 5s Seedance avatar hook (MisoTTS-cloned voice) + whip-scroll article runthrough with proof receipt cards; ~$0.6-1.1/video (DFY scale candidate) |
| `ugc-ai-ad` | Paid-social fictional creator ads with hook variants |
| `screencast-demo` | Polished SaaS screen recordings with click zooms |
| `faceless-broll-ad` | Hook-driven ads without a presenter |
| `longform-repurpose` | Podcast/webinar → vertical shorts |
| `motion-graphics` | Remotion or HyperFrames launch/explainer motion |
| `motion-collage-explainer` | Faceless one-idea explainer short: bold screen-print cutout collage still (gpt-image-2) animated with Seedance, calm "In a Nutshell" docu voiceover. See `MOTION_COLLAGE_STYLE.md` |
| `captioned-talking-head` | Captions + b-roll on existing footage |
| `avatar-product-walkthrough` | HeyGen presenter over product demo |
| `agent-browser-proof` | Short source-investigation proof clips |

## Adding a recipe

1. Copy an existing `recipes/*.json` file and change `id`, routing keywords, and stages.
2. Run `python3 tools/video_recipes.py validate`.
3. Add a matcher case in `tools/video_recipes.py` `cmd_test` if the recipe needs a dedicated routing test.
4. Document the workflow in `WORKFLOW_EXAMPLES.md`.

Schema: `recipes/schema.json`.
