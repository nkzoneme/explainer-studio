---
name: explainer-flow
description: The daily rolling production flow for the cartoon-explainer channels (one folder per channel in explainer/channels/) — one long video a day per channel in a 2-day lane, remake pick, research and script, voice and chapters, assembly, QA gates, one Short, upload template, and the 48 h / 7 day data loop that feeds LEARNINGS.md. Orchestrates explainer-research, explainer-direct, explainer-shorts and explainer-channel-style; it does not repeat them. Use when the user asks to plan or run the next video of a channel, for the production schedule, a video's status, the upload template, or the post-publish review.
---

# Explainer flow: one long video a day per channel, without skipped gates

This skill is the order of work and the gates. How to do each step lives in the linked skill; read that skill when you reach the step. All paths are under `explainer/` unless they start with `.claude/`. Default cadence: **1 long video per day per channel** (lower it in the channel's `style.json` → `cadence` if one operator cannot hold it).

| Step | Skill / tool | Output |
|---|---|---|
| Pick, remake map, packaging | `explainer-research` Stage 2R (radar only for hot-lane) | `research/remake/<slug>/REMAKE_MAP.md`, `TITLES.md` |
| Sources, fact-check, treatments, script | `explainer-research` Stage 3; `research_flow/STORY_SHAPES.md` | `research/<video>/SOURCES.md`, `CLAIMS.md`, `FACTCHECK.md`, three treatments in `BRIEF.md`, `SCRIPT.md` with its Story card, `qa_script.py` exit 0, cold-read notes, G2 risk sheet |
| Voice, ch1, chapters, picture review, master | `explainer-direct`; `kit/REVIEW_PASS.md`, `kit/VISUAL_SOURCES.md` | `film/<video>/`, `REVIEW.md`, `final.mp4` |
| Thumbnails | `explainer-direct` "Thumbnails" | 3 variants |
| Short | `explainer-shorts` | 1 hook Short in `shorts/` |
| Style targets | `channels/<slug>/style.json` | pace, host, sound, hook, packaging, `publish_slot` |
| Tracker | template below | `channels/<slug>/videos/<video>/STATUS.md` |
| What we learned | data loop below | `channels/<slug>/LEARNINGS.md` |

The topic and title decide the breakout, not upload pace, so day -2 gets the most care and nothing downstream may weaken the click promise.

## The daily rolling pipeline

Each video has a 2-day lane. Both channels start one new lane every day, so about 4 videos are in flight (two per channel: one on day -2, one on day -1), plus one scheduled for day 0.

| Lane day | Work | Gate |
|---|---|---|
| **Day -2** | Pick from the remake shortlist; `REMAKE_MAP.md`; sources; `CLAIMS.md`; independent `FACTCHECK.md`; three treatments; `SCRIPT.md` with its Story card; `qa_script.py`; `qa_hook.py --script`; the cold read; `remake_diff.py`; G2 risk sheet; real-media fetch. **Voice for the whole film is generated and post-processed right after G1+G2, the same evening.** | **G1+G2** (evening) |
| **Day -1** | Beat plan (every shot's why, one hero shot per chapter); ch1 (writer); `qa_hook.py` on ch1; chapters 2+ in parallel, each ending with its picture review; thumbnails and 160 px test; assemble, master, `qa_film` exit 0; picture review of the joined film with the fresh-eyes agent; upload pack; hook Short | **G3** only if the hook failed `qa_hook` or its voice changed; **G4+G5** (evening) |
| **Day 0** | Nothing to build. Pinned comment at publish; the hook Short goes out the same day; the video of lane day -2 is already in progress | scheduled at `publish_slot` |
| +48 h, +7 d | Data loop below | `LEARNINGS.md` row |

Publish slots come from each channel's `style.json` → `publish_slot`; two channels never share an hour. Shorts: at most 1 per day per channel (the hook Short of that day's long video; more only for a video at 5 % CTR).

### What runs in parallel, and the daily budget

- **Per day, 2 videos reach day -1 and 2 reach day -2**, so up to ~12 agents are live at peak: per video in day -1, 1 writer (ch1) then 3 chapter workers, plus 1 thumbnail/Short worker; per video in day -2, 1 research and 1 fact-check worker, then 1 writer.
- **Agents per video:** Opus (`explainer-writer`) 3 sessions: script + risk sheet, hook + ch1, G4 review. Sonnet (`explainer-worker`) about 10: research/map, fact-check, the cold read, 3 chapter workers, thumbnails, assembly/QA/upload pack, the fresh-eyes review, Short (the cold read and the fresh-eyes review are short, read-only sessions). **Per day (2 videos): 6 Opus + about 20 Sonnet sessions and at most 20 USD of paid media** (10 per video, Shorts included).
- **Render cap:** at most 4 HyperFrames renders at once across all videos; the coordinator gives each video 2 slots. Measured: one 90 s chapter captured in 1 min 26 s for a 90 s chapter (about real time) with one render alone. 2 films a day of 10-12 chapters is about 25 render-minutes per film per pass, 3 passes with reworks, so about 150 slot-minutes, about 40 minutes of wall clock on 4 slots (about 80 with contention; unmeasured at 4 at once). **It fits; rendering is not the bottleneck, direction and QA loops are.** If a day still slips: (1) films at the low end of `length_min`  rather than 15 min; (2) reusable set templates and footage instead of a new build for every beat; (3) a render queue scheduler that hands out the 4 slots (not built; ask for it if the cap starts to stall).
- **Operator time: at most 20 min per video, 40 min a day.** G1+G2 about 7 min (title and concept pick plus the one-page risk sheet), G3 about 3 min when needed, G4+G5 about 10 min (final cut, contact sheet, 3 thumbnails at 160 px, listening sheet). Log it in `STATUS.md`.

### Starting a new channel

The lane needs 2 days of lead. Day 1: channel style (skill `explainer-channel-style`) and a shortlist of 4 topics. Day 2: day -2 of video 1. Day 3: day -1 of video 1, day -2 of video 2. Day 4: video 1 publishes; steady state from here. If a lane cannot pass `qa_film` on day -1, the video moves one day and the next lane keeps its own date. Gates are never skipped to hold a date.

## Human gates (five, batched; answerable in about 10 minutes together)

Stop and wait at each. Present the decision as a short choice, with your recommendation first.

| # | Gate | What the operator sees | Answer |
|---|---|---|---|
| G1 | Topic + packaging | The remake pick with its angle line "They asked X. We ask Y.", 3 titles, 3 thumbnail concepts (the other 3 of the 6 already struck), the three treatments in five lines each with the writer's pick first | pick + title + concept + treatment |
| G2 | Script | `SCRIPT.md`, the one-page **risk sheet** (the Story card, hook text, the ten riskiest claims, named people, what differs from the source, `remake_diff`, `qa_hook` and `qa_script` results, the cold read's three stop points and what was done about each) and the FACTCHECK verdict | OK / line edits / switch treatment |
| G3 (optional) | Chapter 1 | Skipped when ch1 passes `qa_hook.py` and the voice did not change; otherwise ch1 render, its QA numbers and the five-question listening sheet | OK / fixes |
| G4 | Final cut | `final.mp4`, the `qa_film` table (exit 0), the first phone-width review sheet and the fresh-eyes answers (`REVIEW.md`), the three thumbnails at 160 px beside competitors, the hook takes (the operator can swap a take for about 0.10 USD) | OK / fixes (at most 3 notes) |
| G5 | Publish | The filled upload template and the scheduled time | "publish" |

**Batches:** G1+G2 together (one evening); G3 only on a hook failure; G4+G5 together. `explainer-direct`'s other approvals (new images within budget, host poses) need no extra stop; list them in the G4 report. Never upload, schedule or make public anything without G5 for that exact item (Shorts included).

## Model routing for subagents (user decision 16/11/2026)

Save usage: Sonnet does most of the work, Opus only where it decides retention.

| Work | Model |
|---|---|
| Script writing (SCRIPT.md), hook + chapter-1 beat plan and direction, final-cut review (G4) | opus |
| Trend radar, competitor scans, research and source gathering, independent fact-check, chapters 2+ direction/render/QA (from the approved beat plans), Shorts, thumbnails, media fetch, translation/dubbing, upload packs | sonnet |
| Pure data pulls (yt-dlp listings, feed scraping) | sonnet or haiku |

Spawn with the project agent types (`.claude/agents/`), not general-purpose: `explainer-writer` (opus), `explainer-worker` (sonnet, the default), `explainer-scout` (haiku). They carry only Bash/files/web tools, so no MCP tool lists load into their context. Briefs: goal, decisions already made, file paths and the skill sections to read; never paste file contents. If a worker chapter fails QA twice, hand that chapter to `explainer-writer`.

### Prompt-cache rules (user, 16/11/2026: cache misses cost a lot of usage)

The cache is a prefix: system + tools + agent definition + the start of the first message. Anything that changes earlier text forces a full re-read of everything after it.

1. **Keep the prefix frozen during production.** Edit `.claude/agents/*`, skills, CLAUDE.md and style.json in one batch between videos (not while a lane is running), not while agents are running or about to be spawned.
2. **Continue, don't respawn.** Follow-ups to an agent that already holds the context (gate decisions, fixes, the next stage of the same video) go through SendMessage to that agent. A fresh agent re-reads everything.
3. **One agent per video stage, not per tiny step.** Fewer, longer agents reuse their cached history; but stop before the context is near full, because compaction rewrites history and misses the cache.
4. **Fixed brief header first, variables last.** Start every brief with the same template text (role, rules, files to read) and put the topic, decisions and dates at the end. No timestamps, run IDs or "today is…" at the top.
5. **Spawn same-type agents in one burst.** Parallel work (e.g. two videos' research) goes out in the same message with the same agent type and model, so the shared prefix is written once and read by the others.
6. **No long idle gaps inside a cached conversation.** Waiting longer than the cache lifetime (minutes to an hour) means the next turn re-reads the whole history. Prefer finishing a stage in one run; let the harness notify on background jobs instead of sleeping inside an agent.
7. **Don't switch models mid-task.** Opus and Sonnet caches are separate; a model switch re-reads everything.
8. **Append, don't rewrite.** Inside an agent, read files by section and re-read only what changed; never re-dump a large file to "refresh" it.

### Running agents and renders (lessons 17/11/2026)

- **At most 4 HyperFrames renders at once** on this 16-core machine. More renders overload it, and then they time out, duplicate or render an old build. Use one render queue per video. Before you re-render a chapter, check that nobody else is rendering it.
- **Never use an open-ended wait loop.** `while pgrep -f X` matches its own command line, and `until grep …` waits forever on text that never appears; both leave zombie shells behind for days. Wait with `run_in_background` and let the harness notify you. If you must poll, use `timeout 1800 sh -c 'until [ -f out/.done ]; do sleep 10; done'` and check a file's mtime or existence, never the process list. Before an agent reports done, it kills its own pollers.
- **The coordinator does not idle-wait on a worker that is already finished.** When the files are on disk with fresh mtimes, assemble. If unsure, check `ls -la --time-style=+%H:%M chNN/out/` instead of waiting for a report.
- **Fixing one sentence of voice after G4** costs about 0.01 USD and needs no full re-voice. Generate that sentence with the neighbouring text as context, splice it at the pauses with 30 ms crossfades, keep later word times, rebuild words/levels, then re-render only that chapter and re-join.

### Hot lane (event under 10 days old)

Same gates and same 2-day lane, with a 72-hour ceiling from pick to publish. Primary sources only (filings, regulator statements, company posts, court documents); a fact-check agent with claims only; reuse existing sets and props first; length at the low end of `length_min`; every dated claim says "as of <date>"; an open investigation is described only by what official sources say; a fact that changes after publish goes in the pinned comment and, if material, the description (never silently).

## QA gates (all must pass before G4)

| Gate | Tool | Pass threshold |
|---|---|---|
| Fact-check | `FACTCHECK.md` from an independent agent; `CLAIMS.md` rows | every spoken claim VERIFIED or PARTLY-with-the-corrected-wording; 0 UNVERIFIED in the script; each top claim has 2 independent sources, one primary |
| Policy | read the script | no victim-blaming, no attribution beyond what officials state, no advice on money/law/health, no "how to" for an attack |
| Script | `kit/tools/qa_script.py <SCRIPT.md> --channel <slug>` + `explainer-research` quality bar | exit 0 before G2: Story card complete, contrast ≥ style `script.contrast_per_min_min`, ≤ style `questions_per_chapter_max`, no sentence over 30 words; every warning fixed or answered on the risk sheet |
| Cold read | fresh agent, narration only, fixed brief (`research_flow/STORY_SHAPES.md` §8) | it names the person, the goal and the obstacle from the text alone; its three stop points are fixed or answered |
| Pace | `kit/tools/qa_pace.py <mp4> --channel <slug>` | inside style `pace.shot_changes_per_min` min–max; ch1 first 60 s ≥ `first_60s_per_min_min`; median gap ≤ `median_gap_max_s`; every gap > `long_gap_s` has a reason; none > `max_gap_s` |
| Audio | `kit/tools/qa_audio.py <mp4> <vo>` | SFX bus 12–18 dB under voice; loudest SFX below loudest voice; sync −33 to 0 ms; hits/min inside style `sound.sfx_hits_per_min` |
| Freeze | `sh kit/tools/qa_freeze.sh <mp4> 1.0` | no freeze listed |
| Silence | `ffmpeg -i final.mp4 -af silencedetect=noise=-45dB:d=0.9 -f null -` | nothing except the end-screen tail or a named deliberate pause |
| Loudness | `TP=-2.0 sh kit/tools/master.sh` then measure | −14 LUFS ±0.5 integrated, true peak ≤ −1.5 dBTP after AAC encode |
| Format | `ffprobe` | 1920×1080, 30 fps, AAC; duration = sum of trimmed chapters |
| Contact sheet | ffmpeg 2 fps sheet vs beat plan | every sentence has its picture on its word; host-visible and presenter shares inside style `host`; media mix inside style `media_mix`; joins clean |
| Picture review | `kit/tools/qa_review.py` + `kit/REVIEW_PASS.md`, per chapter and on the joined film | no P0 open; `unanswered` empty or explained; at most 1 frame in 4 a card with words; the fresh-eyes agent says the first three tiles show the title's promise |
| Packaging | `thumb_sheet.py` 160 px test (3 ours among 6 competitors, OCR at 320 px); titles vs style `packaging` | each reads in < 1 s; title ≤ `title_max_chars`; frame 0 shows the thumbnail's object; promise spoken by `hook.promise_by_s` |
| Hook | `kit/tools/qa_hook.py <ch01_raw.mp4> <ch01_w.words.json> --title "..." --channel <slug>` (also inside `qa_film.py`; `--script` before voice) | exit 0: sentence 1 by `first_sentence_by_s`, promise by `promise_by_s`, stakes by 30 s, story by `story_by_s`, 8 changes in 30 s, no banned words, frame 0 = thumbnail object |
| Remake | `kit/tools/remake_diff.py` | exit 0 before G2 (limits in `explainer-research` Stage 2R) |
| Film gate | `kit/tools/qa_film.py <final.mp4> <film dir> --channel <slug>` | exit 0 on the file that is uploaded: format, duration against the trimmed chapters, black flashes, freeze, silence, loudness and true peak, pace, SFX per chapter, SRT against the spoken words, render freshness, the fact-check file, the hook. Thresholds come from `style.json`; the fixed limits are the constants at the top of `qa_film.py`. Media mix and licences are checked by eye on the contact sheets and in `CREDITS.json` (rows above and below) |
| Short | `explainer-shorts` QA checklist | the Short passes its own list; length inside style `shorts.length_s` |
| Credits | `CREDITS.json` | every real item has a tier A–C licence line; no tier D |

Record every number in the video's `STATUS.md`.

## Upload template (one template for both channels; prepared before G4, executed only after G5)

Both `STYLE.md` §11a sections point here and keep only channel specifics.

- [ ] **Title**: the G1 winner, at most `title_max_chars`, entity in the first 30 characters.
- [ ] **Description**: 1-2 sentences restating the promise (150-300 characters, date and stake for news topics); chapters list from `0:00` (at least 3, each at least 10 s, names that **state a fact**; read each one alone: a name that is only a label, like "Background", fails); one "Based on <2-3 primary documents named>" line **without links**; the facts line written from the real claim counts in `FACTCHECK.md` (never "the team"); credits line per `CREDITS.json` (every row has a licence tier; no GFDL); music credit line; one line on how the channel works. Optional, only if the operator says yes for that video: `Further viewing: <source title>, <channel>`, no link. 3 hashtags at the end. No links of any kind (a single sources-page link may come later).
- [ ] **Tags**: 8 or fewer, entity names and the radar's search phrasings; never copied from the other channel.
- [ ] **Thumbnail + Test & Compare**: 3 concept-different variants (explainer-direct "Thumbnails"); read at 48 h.
- [ ] **Subtitles**: English SRT from the word timestamps; names and numbers checked against the spoken words.
- [ ] **End screen**: the pitched video + subscribe (first video of a channel: subscribe + best for viewer), boxes in the plate's clear half, last 10-12 s.
- [ ] **Playlist**: the channel's series playlist.
- [ ] **Visibility**: scheduled at `publish_slot`; altered-content switch only if a real photo was AI-edited; made-for-kids = no.
- [ ] **Pinned comment** (at publish): ONE short question, no links. A material caveat goes in the description. Full sources stay in `final/sources_full.txt` for replies.
- [ ] **Short**: one hook Short, Related video = the long video, a spoken and visual pointer in the last 5 s; at most 1 per day per channel.

## Data loop (48 h and 7 days)

The operator pastes the numbers into `STATUS.md` with the retention curve (an export, or the three dip times typed by hand). `python3 kit/tools/retention_map.py` maps each dip to its beat, sentence and picture type. Competitor Studio numbers are private; the thresholds below are working targets until our own medians exist (five uploads per channel).

| When | Read | Threshold | Decision |
|---|---|---|---|
| 48 h | Impressions | under 500 | The package was never tested. Do not tune the film. |
| 48 h | CTR, Home and Suggested | under 3 % after 1,000 impressions; 5 % | Switch to the next thumbnail variant. At 5 %, reuse that concept family. |
| 48 h | Still watching at 0:30 | under 60 %; 70 % | Hook failed: compare its promise time and frame 0 with our best video. At 70 %, keep the hook form. |
| 48 h | Three largest dips | over 5 points in 15 s | Tag the cause: list, card-only, number chain, host. |
| 7 d | Average percentage viewed | under 30 %; 40 % | Cut the next script by 15 % and remove the tagged dip types. At 40 %, length is fine. |
| 7 d | CTR against view duration | one high, one low | High CTR, low duration: fix the title and first 30 s. Low CTR, high duration: re-package this video now. Both high: make the adjacent topic next. |
| 7 d | Subscribers per 1,000 views | under 2; 4 | The end pitch is weak or the next video does not exist. At 4, keep. |
| 7 d | Comments | 5 % about the voice; any factual dispute | Voice trigger (designed voice stays postponed until then). Check a dispute within 24 h and correct it in the description. |
| 7 d | Shorts "stayed to watch" | under 60 %; 70 % | Rewrite the hook Short's first clause. |

Write one `LEARNINGS.md` row per video (date, title, lane, story shape and hook mechanism, views 48 h and 7 d, CTR, 0:30 %, average % viewed, top dip and its beat, Short verdict, decision). The rules taken from other people's repos on 18/11/2026 (E1–E10 in `STORY_SHAPES.md`, the `[hf]` rules in `CRAFT_RULES.md` §15–16) are **experiments**: none came with retention data. At each 7-day review mark in the file's "Experiments" table whether the video's curve agrees with each rule it used; a rule stays after three videos agree and goes after three disagree. **Change a rule only when three videos point the same way** and log it; errors are fixed at once. Use engaged views, not public views. Stage 2R and `explainer-channel-style` read the file (our own data wins at 5 uploads).

## Stop doing

1. Second-accurate skeleton copying and cut-by-cut source beat tables (angle line and `remake_diff` replace them).
2. Three to five native Shorts per video: one hook Short; more only at 5 % CTR.
3. Rewriting skills or re-measuring competitors mid-week: edit skills in one batch between videos; no new competitor study until five uploads have data.
4. Host craft: new poses, mouth patches and lip-sync checks (the host is on screen 11-19 % of the time).
5. Vietnamese dubs and other side versions: paused until an English video passes 10,000 views, unless the operator asks.

(A designed voice is postponed, not dropped: the trigger is in the data loop.)

## Budget and cost log

At most 10 USD per long video, Shorts included (research, voice, images, thumbnails 0.50, re-takes). Log every paid call in `STATUS.md`; ask before going over. The radar is free.

## STATUS.md template (`channels/<slug>/videos/<video>/STATUS.md`)

Create it at G1. One page; tick as you go; links instead of copies.

```markdown
# <video slug> — <channel>   lane: hot | remake | evergreen   publish: <YYYY-MM-DD HH:MM UTC>

Title: <chosen>    Thumbnail: <concept>    Click promise: <one sentence>    Angle: They asked X. We ask Y.
Shape: <T1–T5>    Hook mechanism: <# and name>    Peak: <m:ss, the picture>    Person: <who wants what, blocked by what>
Brief: research/<video>/BRIEF.md    Film: film/<video>/

## Gates (each ticked gate links to its evidence file)
- [ ] G1+G2 (<date>) risk sheet: <path>    - [ ] G3 (<date>) or "skipped: qa_hook pass"
- [ ] G4+G5 (<date>)

## Stage time log (agent hours / operator minutes; targets 6 h and 20 min)
| Stage | Agent h | Operator min |
|---|---|---|
| Day -2 pick to G2 | | |
| Day -1 voice to G4 | | |
| Total | | |

## QA (numbers, not ticks)
| Check | Target (style.json) | Result | Pass |
|---|---|---|---|
| qa_film exit code | 0 | | |
| qa_hook / remake_diff / qa_script | exit 0 | | |
| Cold read: person named / stop points fixed | yes / 3 of 3 | | |
| Picture review: P0 open / unanswered / card frames | 0 / 0 / ≤ 1 in 4 | | |
| Fact-check: claims / verified / partly / cut | 0 unverified | | |
| Pace film / ch1 first 60 s / median gap | | | |
| SFX under voice / hits per min | 12-18 dB / | | |
| Freeze / silence / black | none / tail only | | |
| Loudness / true peak | -14 LUFS / <= -1.5 dBTP | | |
| Host visible / presenter share | | | |
| Footage share / real items / chapters with footage | | | |
| Thumbnails at 160 px vs competitors | reads < 1 s | | |

## Upload pack
- [ ] template items above, all ticked    - [ ] 3 thumbnails in Test & Compare    - [ ] Short

## Costs (USD, budget 10.00)
| Date | Item | USD |
|---|---|---|
| | **Total** | 0.00 |

## Reviews
- 48 h: impressions __ | CTR __ % | 0:30 __ % | dips: __ | decision __
- 7 d: AVD __ % | subs/1,000 __ | comments __ | verdict -> LEARNINGS.md
```
