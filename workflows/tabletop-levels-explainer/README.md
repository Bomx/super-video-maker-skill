# tabletop-levels-explainer — workflow scripts

Reusable engine for the `tabletop-levels-explainer` recipe: a from-scratch 9:16 reel that
builds a tiered concept one physical layer at a time (calm talking head + overhead handcraft
b-roll + receipts + flow diagram + orchestral bed + word-locked captions).

## Setup
```bash
export SVM_JOB=/abs/path/to/job_dir         # all assets/outputs land here
export SVM_ENV_DIR=/abs/path/to/keys_dir    # dir holding the .env (FALAI_API_KEY, OPENAI_API_KEY)
```

## Per-video inputs you author (from the storyboard)
- `chunks.json` — presenter script split into <=~12s chunks: `{character_preamble, style_suffix, seed,
  chunks:[{id,dur,dialogue}]}` (character_preamble ends with "...She says: ").
- `overlay_schedule.json` — `{master_dur, canvas:{w,h,fps}, presenter_concat:[ids],
  broll:[{asset,t0,t1,type:clip|still,dir?,kb?}], keyword_captions_color?, phrase_captions?}`.
- `receipts.json` — `[{name,url,scroll}]` real source pages to screenshot.
- `assets/character/character_hero.png` — the fictional presenter (gpt-image-2 from a royalty-free
  staging photo; see playbook).
- a diagram `*.html` (paused CSS keyframes) for any animated flow beat.

## Run order
```bash
# 1. presenter chunks (chunk A first to set the voice, then lock it)
python3 gen_presenter.py --chunk A
ffmpeg -y -ss 1 -t 4 -i $SVM_JOB/assets/presenter/presenter_A.mp4 -vn -ac 1 -ar 44100 $SVM_JOB/assets/voice_ref.wav
for c in B C D ...; do python3 gen_presenter.py --chunk $c --ref-audio $SVM_JOB/assets/voice_ref.wav; done
python3 whisper_timeline.py                         # -> analysis/presenter_timing.json (global word times)

# 2. craft b-roll (gpt-image-2 first/last pairs you generate -> Seedance image-to-video)
python3 gen_craft_clip.py --name pyramid_draw --first P0_blank.png --last P1_llm.png --dur 4 --prompt "a hand draws the pyramid and places the yellow LLM sticky"
# ...one per craft beat...
python3 capture_anim.py --html diagram.html --out $SVM_JOB/assets/diagram/flow_diagram.mp4 --dur 5.6
python3 capture_receipts.py                          # real screenshots

# 3. assemble + caption + music
python3 build_captions.py
python3 assemble.py                                  # switched video + continuous VO bed
# drop a soft orchestral track at assets/music/orchestral_bed.wav (generated or royalty-free)
python3 finalize.py                                  # -> exports/master.mp4
```

See `../../TABLETOP_EXPLAINER_PLAYBOOK.md` for the full method, prompts, and gotchas.
