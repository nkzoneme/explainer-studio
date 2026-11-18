# Channel styles

Each channel has its own style, built from its own competitors by the skill `explainer-channel-style`. The production skills (`explainer-research` stage 3, `explainer-direct`, `explainer-shorts`) read it before they plan anything. Nothing about pacing, host use, media mix, typography, sound, hook, ending or packaging is a house rule any more unless the table at the bottom calls it universal.

```
channels/<slug>/
  STYLE.md          the style bible a human reads: identity, visual system, targets with ranges, what we never do,
                    the competitor evidence and the date
  style.json        the same targets for tools and skills (schema below)
  research/
    competitors.json  the competitor list (input of channel_style_scan.py), with notes on who was dropped and why
    scan/             per competitor: channel.json, <id>.json metrics, <id>_sheet.jpg contact sheets, thumbs.jpg
    gemini/           Gemini style reads (prompt: research_flow/channel_style_prompt.md)
    EVIDENCE.md       the tabulated measurements behind every number in STYLE.md
  trend_sources.json  news queries, feeds, subreddits, YouTube queries, suggest seeds and the familiar-entity list
                      read by research_flow/trend_radar.py
  trends/             YYYY-MM-DD.md + .json radar runs; YYYY-MM-DD_SHORTLIST.md topic picks (remake shortlist is the default source)
  videos/<video>/STATUS.md  one-page tracker per video (gates, QA numbers, costs); template in skill explainer-flow
  LEARNINGS.md        what our own 48 h and 7 day reviews taught (feeds the next pick and the style refresh)
```

Slugs match the Shorts style files (`shorts/styles/<slug>.json`). Brand files (palette, fonts, voice, avatar, host poses) stay where they are, in `shorts/styles/<slug>.json` and the brand folder; `style.json` points at them under `brand` and does not copy them.

## style.json schema

Every key is optional. A skill or tool that needs a key the channel does not set falls back to the **default** in the last table and says so in its report.

| Key | Meaning | Read by |
|---|---|---|
| `channel`, `slug`, `version`, `refresh_due` | Name, folder, date built, when to rebuild | all |
| `brand.shorts_style`, `brand.brand_doc`, `brand.host`, `brand.voice` | Pointers to the existing brand files | direct, shorts |
| `pace.shot_changes_per_min` `{min, target, max}` | Full-frame changes per minute on the render (`qa_pace.py`). `max` flags a film busier than the style | direct QA, `qa_pace.py --channel` |
| `pace.first_60s_per_min_min` | Same, first 60 s of a film | direct QA |
| `pace.median_gap_max_s`, `pace.long_gap_s`, `pace.max_gap_s` | Median gap ceiling; a gap over `long_gap_s` needs a reason in the plan; nothing over `max_gap_s` | direct QA |
| `pace.still_share_max` | Share of runtime near-still for 1 s or more (`qa_pace.py`). A style measure, not the freeze test | direct QA |
| `host.visible_share` `{min, max}` | Share of the film with the host on screen | direct plan and QA |
| `host.presenter_share_max`, `host.presenter_max_s` | Presenter mode (talking to camera): share of film, longest stretch | direct |
| `host.modes` | Which modes this channel uses (presenter, actor, corner, absent) and where | direct, shorts |
| `host.in_frame0`, `host.on_thumbnail` | Allowed or not | direct, research |
| `mode_change_s` `{min, max}` | Seconds between changes of picture type (scene, diagram, map, real media, number, text card) | direct |
| `media_mix` | Target shares of runtime by picture type | direct plan |
| `real_media.items_per_chapter_min`, `real_media.items_per_film` | Real logos, photos, footage, documents, real-data charts | research brief, direct |
| `visual_system` | Layers, background treatment, texture, recurring sets, motion vocabulary, transitions | direct |
| `typography` | Badge rules, text cards per chapter, chapter cards, burned captions in long form | direct |
| `sound` | SFX hits per minute, music bed and its level | direct QA (`qa_audio.py`) |
| `hook` | First sentence by, promise by, story by, max length, allowed openings | research script rules, direct ch1 |
| `chapters` | Chapter length, chapter-card style, how a chapter opens | research, direct |
| `ending` | Tail after the last payoff, end-screen plate length and layout, pitch | research, direct |
| `script` | Words per minute, contrast turns per minute, questions per chapter | research quality bar |
| `packaging` | Title families, title length, thumbnail layouts, words, host on thumbnail | research packaging |
| `length_min`, `cadence`, `publish_slot` | Target film length, upload rhythm, and the daily publish hour (UTC) for long video and Shorts | research, explainer-flow |
| `shorts` | Shorts-only overrides (length, host, captions); the brand part stays in `shorts/styles/<slug>.json` | shorts |

## What stays universal (in the skills and `kit/CRAFT_RULES.md`, never per channel)

- HyperFrames and kit technical rules and gotchas (root/clip structure, paused timeline, determinism, the REQUIRED MARKER comment, nested `<video>`, external `kit.js`, punch-in and insert recipes).
- Audio QA: SFX bus 12–18 dB under the voice, loudest SFX below loudest voice, sync −33 to 0 ms, master −14 LUFS and −1.5 dBTP after encode, the silence check, `qa_freeze.sh` (no dead picture over 1 s).
- Chapter length = last word + 0.6 s; joins 0.5–0.8 s; frame-snapped trims.
- Real-media licensing tiers A–D, `CREDITS.json`, no news photos or broadcast, real faces rules.
- Fact-check gates, the approval gates, the 10 USD budget, publishing only with the user's OK.
- Script truths that come from the platform or apply to any story: click promise paid early, BUT/THEREFORE between beats, no channel intro before the story, ending hands the viewer on.
- Channel hygiene: two channels never share titles, descriptions, upload times or scene grammar.

## Defaults (used only when a channel style does not set the key)

These are the numbers the skills used for every channel until 15/11/2026. They came from a mix of 21 competitor videos in several niches, not from one channel's competitors. Each is labelled **default** wherever a skill quotes it.

| Key | Default |
|---|---|
| `pace.shot_changes_per_min.min` | 10 |
| `pace.first_60s_per_min_min` | 14 |
| `pace.median_gap_max_s` | 6 |
| `pace.long_gap_s` / `pace.max_gap_s` | 12 / 20 |
| `host.visible_share` | 0.40–0.60 for a film (plan the lower half); a chapter up to 0.70 |
| `host.presenter_share_max` / `presenter_max_s` | 0.25 / 12 |
| `mode_change_s` | 30–45 |
| `real_media.items_per_chapter_min` / `items_per_film` | 3 / 25–60 |
| `hook` | first sentence by 5 s, promise by 20 s, story by 35 s, never past 45 s |
| `ending` | 30 s or less after the last payoff; end-screen plate 8–12 s |
| `script.wpm` / `contrast_per_min_min` / `questions_per_chapter_max` | 150–175 / 1.0 / 1 |
| `sound.sfx_hits_per_min` / music | 60–75 body, up to 120 in a hook / no music |
| `typography` | no burned captions in long form; badges 2–4 words, at most 2 on screen; one text card per chapter at most |
| `packaging` | 5 titles from 3 families, ≤ 55 characters; 3 thumbnail layouts, ≤ 4 words |

## Refresh rule

Rebuild a channel's style every 3 months, or after its 10th long upload, whichever comes first (`refresh_due` in style.json). The refresh re-runs the competitor scan and adds our own Studio data: for each of our uploads, Intro (still watching at 0:30), average percentage viewed, the three biggest dips mapped to the beat plan, and click-through rate on Home and Suggested. Where our own data and the competitor data disagree, our own data wins once it covers 5 or more uploads.
