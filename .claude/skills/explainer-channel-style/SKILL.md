---
name: explainer-channel-style
description: Build or refresh one cartoon-explainer channel's OWN editing style from its competitors — measure 5–12 competitor channels (shot changes per minute, presenter share, media mix, typography, music and SFX, hook, chapters, ending, titles, thumbnails, length, cadence), then write explainer/channels/<slug>/STYLE.md and style.json that research, direct, shorts and qa_pace.py read. Use when a new channel is created, when the user asks for a channel's style or look, to compare a channel against its competitors, or when a style's refresh is due (3 months or 10 uploads).
---

# Channel style: each channel gets its own

The user's rule (15/11/2026): no fixed editing style for every channel. Each channel's style comes from its own competitors, keeps what their winners share, and deliberately differs where copying would make us a clone or look like AI slop. The production skills only keep what is universal (HyperFrames rules, audio QA, licensing, fact-check, approvals, publishing); everything about pace, host, media mix, type, sound, hook, ending and packaging comes from `explainer/channels/<slug>/style.json`.

Layout, the `style.json` schema, what stays universal and the labelled defaults: `explainer/channels/README.md`. Empty template: `explainer/channels/_template/` (copy it to `channels/<slug>/`).

Tools (run from `explainer/`):

| Tool | What it does | Cost |
|---|---|---|
| `research_flow/channel_style_scan.py competitors.json OUT/ [--per 2] [--list-only] [--only name]` | Per competitor: last 30 long uploads with views, title families, cadence (RSS), six-thumbnail montage; per picked video: 240p download, `qa_pace.py` numbers, captions (words per minute, contrast turns, words in the first 30 s, hook and last-30-s text), music-bed level, 30-frame contact sheet, thumbnail. Deletes the video and captions after measuring. Resumable. System `python3` | free, ~3–4 min per video |
| `research_flow/gemini_video.py <url> OUT.md google/gemini-3.5-flash-lite research_flow/channel_style_prompt.md` | Gemini watches the video and estimates presenter share and modes, picture mix, visual system, typography, music and SFX, hook, chapters, ending | 0.02–0.05 USD per 10–25 min video |
| `kit/tools/qa_pace.py <video> --json` | The shot-rate measure the QA uses on our renders, so competitor and own numbers are comparable | free |

Never read `.env`, never print keys, send nothing but public video URLs to outside services. Gemini spend for one channel style: at most 0.60 USD (both channels together at most 1 USD); it counts as research spend, outside any single video's 10 USD budget.

## When to run

- A new channel: after the user picks the niche (explainer-research stage 1), before the first brief.
- Refresh: every 3 months or after the channel's 10th long upload, whichever comes first (`refresh_due` in style.json). From the refresh on, our own Studio data is an input (step 6).
- On request: "make the style for X", "how should X look", "compare X with its competitors".

## Step 1. Pick the competitors (5–12)

1. Start from outlier data: `research/niches/scan/<niche>/videos.csv` and `channels.csv` (from `yt_scan.py`), the BACKLOG's competitor notes, and names the user gives. Add a few channels by search (`yt-dlp "ytsearch10:<niche query>"`).
2. Mix sizes on purpose: 2–4 large (over 500k subscribers), 2–4 mid, **at least 2 small** (under 100k) that broke out. Small channels show what a new channel can do; large ones show what the audience is used to.
3. Include at least one channel in our format family (2D drawn or cartoon, faceless) if any exists in or next to the niche, and one presenter-led channel if the niche has them.
4. Write `channels/<slug>/research/competitors.json` (format in the scan tool's header). Use `filter` (a title regex) for channels that cover several niches, `videos` to pin exact videos, `skip` + `note` for channels you dropped. Every drop gets a reason (inactive since …, no videos tab, affiliate reviews, wrong niche).
5. Run `--list-only` first. Check for each: active (a long upload in the last 90 days, or say why an inactive one stays), relevant (its top videos are in our niche), and which 2–3 recent strong videos to measure. Prefer the most-viewed of the last 30 long uploads that are in our niche; pin ids where the automatic pick drifts off-niche.

## Step 2. Measure

1. `python3 research_flow/channel_style_scan.py channels/<slug>/research/competitors.json channels/<slug>/research/scan` (background; YouTube rate-limits captions after a dozen in a row, the tool sleeps between videos). A failed video is retried on the next run.
2. Gemini on one video per competitor (the most typical of the picks, under 30 min). Write to `channels/<slug>/research/gemini/<competitor>__<id>.md`. Tally the cost line each run prints; stop at the cap.
3. Look at every contact sheet (`<id>_sheet.jpg`, 30 evenly spaced frames) and every `thumbs.jpg`. Count frames with a presenter (talking to camera), with a host inside a scene, with real media (footage, photo, document, screenshot), with maps, with drawn scenes. Contact-sheet counts are your measurement; Gemini's percentages are estimates and were up to 3× off on shot counts in our own check. Where the two disagree, say so.
4. Measure our own last film(s) the same way: `python3 kit/tools/qa_pace.py film/<slug>/final/<final>.mp4` and a contact sheet.

## Step 3. Tabulate (`channels/<slug>/research/EVIDENCE.md`)

One row per measured video, one block per competitor:

| Group | Columns |
|---|---|
| Channel | subscribers, median views of last 30, long uploads per 30 days, median length, newest upload |
| Pace [M] | full-frame changes per minute, first 60 s, median and 90th percentile gap, near-still share |
| Host [M + G] | presenter share, modes (talking head / in scene / corner / none), longest stretch |
| Picture mix [M + G] | drawn scenes, diagrams/charts, maps, real footage, photos, documents/screenshots, 3D, text cards |
| Type [G] | captions on or off, labels and lower-thirds, chapter cards, text style |
| Sound [M + G] | music-bed level (dB under speech in pauses: −30 or lower = no bed, −20 to −10 = a bed), SFX density |
| Script [M] | words per minute, contrast turns per minute, words in the first 30 s, first sentence |
| Hook and ending [G + M] | first sentence end, promise, story start, frame 0; last 30 s: callback, pitch, subscribe ask, end-screen length |
| Packaging [M] | title families of the last 30, title length, thumbnail layouts from `thumbs.jpg`, words on thumbnails |

Then three lines per group: what the winners share (the range across competitors whose top videos beat their channel median), where the niche splits (two or more clear camps), and what no one does.

## Step 4. Synthesise the style

Decide, for every group in the table, one of three things and write the reason next to it:

- **Adopt** what the winners share when it serves the viewer, not the look: hook timing, promise early, real evidence on screen, chapter rhythm, endings. Set the target inside the competitors' range.
- **Differ on purpose** where copying would make us a clone: palette, background treatment, typography, recurring device, metaphor family, thumbnail layout. If three competitors share a dark blue blueprint look, ours is not dark blue. Name the competitor each choice avoids looking like.
- **Keep our format's own identity** where the niche has no cartoon channel: our drawn world and host are the difference. Do not import a footage channel's numbers that only make sense for footage (a hard cut every 2 s of stock clips is not the same work as re-framing a drawn set).

Rules for the numbers:

- Every target is a **range** (`min`, `target`, `max`) taken from the measured competitors, with the source in STYLE.md. Never a single number without its spread.
- **Pace**: `min` at or a little under the slowest winner in our format family; `max` at the busiest competitor's level. Add `still_share_max` only if the niche is clearly lively or clearly calm.
- **Host**: from what the niche's audience accepts. A niche with expert presenters tolerates more host; a niche where every winner is faceless gets a lower ceiling and more evidence on screen. Presenter-mode limits stay tighter than visible-share limits.
- **Media mix**: name the 2 dominant picture types for the channel and their shares. Our real-media tiers and budget still apply; a style that needs licensed stock footage we cannot afford is not a style.
- **Sound**: SFX density and music are style choices; SFX-vs-voice level, loudness and peaks are universal QA. A music bed needs a licensed or CC0 track in `kit/` and the user's OK before the first film that uses it.

### The visual-system menu (pick per channel, write the picks in STYLE.md)

These are options, not rules. Several come from MoSidd's "I Made Vox-Style Motion Graphics Using Only Claude Code & Remotion" (https://www.youtube.com/watch?v=7wuYBfE131U), which the user likes:

| Option | What it means in a composition | Fits when |
|---|---|---|
| **Script-as-timeline table** | The beat plan is a table: one row per voice-over line with its background, midground and foreground asset (and the image prompt for each new one). Write it before any markup | Always useful; a style may make it the required plan format |
| **Locked visual system** | One shared background per chapter (or per film), fixed fonts and accent palette; only midground and foreground change, so cuts read as "one continuous shot" | Calm, documentary styles; channels with a strong recurring world |
| **Three layers** | Background (set or texture) / midground (characters, cut-outs, the object) / foreground (structures, frames, labels) with their own parallax push | Any 2.5D look; gives punch-ins depth |
| **Paper / halftone cut-outs** | Real photos turned into black-and-white halftone cut-outs with an offset coloured stroke, on a paper texture ("magazine" feel) | Story and politics channels; real people or places in the story (faces only per the media rules) |
| **Two motion types, staggered** | Only a spring pop (entrances) and a smooth interpolation (moves), offset so things never move all at once | A restrained, premium look; pairs with a locked system |
| **Scene starts and ends on its own narration** | Each scene's in and out sit on the first and last word of its own line; transitions live in the pauses | Always (it is our beat-change rule) |
| **Hand-drawn build-ups** | SVG drawn on line by line (blueprints, arrows, circuits) | Engineering mechanisms |
| **Evidence board** | Documents, headlines, code, court filings, phone screens as props with a highlighter swipe | Investigations, true crime, anything with a paper trail |
| **Map system** | One drawn map style for the channel (route arcs, pins, borders) reused every film | Geography-heavy niches (trade, history, travel) |
| **Recurring device** | One channel-owned bit (timer cards, a tracker of reasons, a flashlight trail) | Every channel needs at least one |
| **Chapter cards** | Numbered full-frame cards (0.8–1.5 s) at each chapter | Long, segmented films; engineering explainers |
| **Corner host / narrator-only** | The host reacts small in a corner, or is absent except hook and ending | Niches where no winner shows a presenter |

## Step 5. Write the outputs

1. `channels/<slug>/STYLE.md`, in this order: identity in three sentences (who the channel is for, the one thing it is recognised by with the sound off, the one thing it never does); the visual system (menu picks, palette and fonts by pointer to the brand files, layers, recurring device, map and evidence style); pacing targets with ranges and the competitor numbers behind them; host usage (modes, shares, where he/she appears); media mix; typography; sound; hook pattern; chapter pattern; ending and end screen; packaging (title families and their order of preference, thumbnail layouts); Shorts differences; **what we never do** (each with the competitor it would copy); how this changes our first film (measured); sources (competitors, videos, dates, Gemini spend); refresh date.
2. `channels/<slug>/style.json` with the keys in `channels/README.md`. Point at `shorts/styles/<slug>.json` for palette, fonts, voice and avatar; do not copy them.
3. If the channel already has finished films, add one line to their CONVENTIONS or README docs pointing at the style. Do not edit finished films.
4. Show the user the side-by-side of the channel's key numbers against its competitors and against the other channels. **Human gate: the user approves the style before the next brief uses it.**

## Step 6. Refresh with our own data

At `refresh_due`: re-run steps 1–3 (drop dead competitors, add new outliers), then add a block to EVIDENCE.md with our own uploads: Intro (still watching at 0:30), average percentage viewed, typical retention against our previous videos, the three biggest dips mapped to the beat plan (what was on screen: host, diagram, map, real media), Home and Suggested click-through rate, and `qa_pace.py` on each upload. Change a target when our own data over 5 or more uploads points one way, even against the competitor range; note the change and the date in STYLE.md's changelog.

## Quality bar: a style is not done until every line is true

- [ ] 5–12 competitors, at least 2 small ones, every drop has a reason, every kept channel is active or has a stated reason.
- [ ] At least 1 measured video per competitor (2 for the 4 closest), every number in STYLE.md traced to EVIDENCE.md with [M] or [G].
- [ ] Every pace and host number is a range, with the competitor spread beside it.
- [ ] At least 3 "differ on purpose" decisions, each naming the competitor it avoids copying.
- [ ] At least one recurring device the channel owns.
- [ ] The style differs from every other channel of ours in palette, type, recurring device, host use and title families (channel hygiene).
- [ ] style.json parses, and `python3 kit/tools/qa_pace.py <our last film> --channel <slug>` runs and prints the channel's targets.
- [ ] Gemini spend stated; unverified items listed (Gemini estimates, contact-sheet sample size, captions that failed).
