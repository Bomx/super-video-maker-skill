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
| `tabletop-levels-explainer` | 9:16 "levels-of-X" explainer: fictional presenter + first/last-frame handcraft b-roll (building pyramid, paper cutouts, models) + receipts + flow diagram, beat-locked. See `TABLETOP_EXPLAINER_PLAYBOOK.md` |
| `ugc-ai-ad` | Paid-social fictional creator ads with hook variants |
| `screencast-demo` | Polished SaaS screen recordings with click zooms |
| `faceless-broll-ad` | Hook-driven ads without a presenter |
| `longform-repurpose` | Podcast/webinar → vertical shorts |
| `motion-graphics` | Remotion or HyperFrames launch/explainer motion |
| `captioned-talking-head` | Captions + b-roll on existing footage |
| `avatar-product-walkthrough` | HeyGen presenter over product demo |
| `agent-browser-proof` | Short source-investigation proof clips |

## Adding a recipe

1. Copy an existing `recipes/*.json` file and change `id`, routing keywords, and stages.
2. Run `python3 tools/video_recipes.py validate`.
3. Add a matcher case in `tools/video_recipes.py` `cmd_test` if the recipe needs a dedicated routing test.
4. Document the workflow in `WORKFLOW_EXAMPLES.md`.

Schema: `recipes/schema.json`.
