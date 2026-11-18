---
name: explainer-research
description: Research flow for the cartoon-explainer YouTube channels (explainer/channels/<slug>) — find a niche, run the trend radar and pick a topic (hot lane or evergreen-with-a-hook, with gates and a 100-point score), and lock one topic into a production-ready brief. Use when the user asks to find/compare niches, find trending video ideas/topics, run the trend radar, check if a topic is already covered, analyze competitor videos, or prepare research/brief for the next video. The daily rolling schedule and gates around it are in explainer-flow.
---

# Explainer research flow

Tools live in `explainer/research_flow/` (run Python with `explainer/research_flow/.venv/bin/python`):
- `trend_radar.py <slug>` — radar from free sources (no keys): clustered stories with momentum, YouTube coverage and velocity, search-suggest phrasing. Config `channels/<slug>/trend_sources.json`; output `channels/<slug>/trends/<date>.md/.json`. Stage 2.
- `yt_scan.py niches.json OUT/` — per niche: long-form search results, channel medians, outlier scores, `summary.md`. No API key (yt-dlp). Slow (~10–20 s per channel); run in background.
- `topic_gap.py candidates.json OUT.csv` — for candidate topics: strongest existing long-form videos and a gap score.
- `gemini_video.py <youtube_url> OUT.md [model]` — Gemini watches a video via OpenRouter (key in `../.env` as OPENROUTER_API_KEY). Default `google/gemini-3.5-flash-lite` (~0.03 USD per 17-min video). Prompt: `video_analysis_prompt.md`.

Background context: `explainer/RESEARCH_REPORT.md` (market, RPM, YouTube policy, pipeline), `explainer/research_flow/analysis_tradeoff_arm.md` (example analysis), and (what gets views and retention in this format, with sources and our own measurements of 21 competitor videos). The gates, packaging rules and script rules below come from that playbook; it holds the reasoning, so do not paste research into briefs.

**Each channel has its own style** (`explainer/channels/<slug>/STYLE.md` + `style.json`, built by the skill `explainer-channel-style` from that channel's competitors). Stage 3 reads it: its `hook`, `script`, `ending`, `chapters`, `real_media`, `packaging` and `length_min` keys replace the numbers below, which are marked **default** and apply only when the style does not set a key. The topic gates, the click promise, the fact-check and the channel-hygiene rules are universal.

Never paste or log API keys. Research spend counts inside the 10 USD per-video budget (see explainer-direct); Gemini/OpenRouter up to about 1 USD per video needs no extra approval.

**Data-rich by default.** Every brief lists, per chapter, the real data and media it will show: numbers with sources that can become charts (prices, counts, timelines, maps, rankings), and the media table split into the tiers of explainer-direct "Real media" (A free, B press kit, C headline screenshots; never D news photos/broadcast). How many real items per chapter and which kinds (maps, documents, photos, screens) is the channel style's `real_media` and `media_mix` (**default**: at least one real chart or map and 3+ real items per chapter). Prefer primary data (regulator filings, government datasets, company reports, court documents) over articles about them.

## Stage 1 — Niche (one-time, revisit monthly)
1. Brainstorm 12–20 niches that fit the format (2D cartoon explainer, business/tech/history/science stories with a clear "why/how" question, English, US/UK audience). For each, 3–5 search queries a viewer would type. Write `research/niches/niches.json`.
2. Run `yt_scan.py` on it (background). Read `summary.md` + `videos.csv`.
3. Pick the 2–3 strongest small-channel outliers per promising niche and run `gemini_video.py` on each (≈0.03 USD each).
4. Score every niche 1–5 on: demand (videos ≥100k, outliers), small-channel breakout (proof a new channel can win), saturation by AI clones (share of <1k-view videos), RPM tier (from RESEARCH_REPORT.md §2.2–2.3), sponsor fit, evergreen share, research difficulty, fit with our visual format, policy risk (finance/medical/legal advice = risk). Show evidence per score.
5. Write `research/niches/NICHE_REPORT.md` (written on the first niche run): ranked table, top 3 with reasoning, and the main risks. **Stop for the human gate: the user picks the niche.**
6. **Stage 1b — channel style.** Once the niche is picked (and again every 3 months or 10 uploads), run the skill `explainer-channel-style`: 5–12 competitors from the outliers above, measured, then `channels/<slug>/STYLE.md` + `style.json`. No brief for a new channel before its style is approved.

## Stage 2 — Trend radar → topic pick (per video, per channel)

The pick combines what is moving now with the breakout formula: a familiar entity plus a money, failure or scandal superlative, often riding a current event ("How Binance Lost $6.3B in One Night", "Why the World's Biggest Plane Failed in America"; `research/viral/NEW_CHANNEL_BREAKOUTS.md`). The day it runs and the gate that follows are in the skill `explainer-flow`.

1. **Radar.** `cd explainer/research_flow && .venv/bin/python trend_radar.py <slug>` (3–6 min, free, no keys). It reads `channels/<slug>/trend_sources.json` and writes `channels/<slug>/trends/<date>.md` + `.json`: stories clustered across Google News, trade and official feeds (CISA KEV for security niches), Google Trends, Reddit, Hacker News, YouTube search (this month, views per day, who already covered the story and how well) and YouTube search-suggest. Read its "Sources" table first: a failed source is a blind spot, say so in the shortlist. Momentum is relative inside one run.
2. **Candidates.** From the radar's top 25, plus `channels/<slug>/LEARNINGS.md` and the channel's evergreen backlog (`channels/<slug>/BACKLOG.md`; create it on the first research run), write 8–12 candidates. A radar story is raw material, not a topic: re-frame it into the channel's question (the event is the "why now"; the mechanism, money or people are the video). Each candidate: lane, working title and one-sentence thumbnail first, thesis in 2 sentences, why now with a dated URL, key entities.
3. **Lanes.**
   - **Hot**: the event is under 10 days old and the topic only works now. Must publish within 3–5 days of the pick (the 72 h flow in `explainer-flow`). At most 1 pick in 2 per channel, never two hot picks in a row.
   - **Evergreen-with-a-hook**: an older story or mechanism re-opened by a current event (a new filing, an anniversary, a sequel incident, a verdict). The title must still make sense in two years. This is the default lane.
   - **Evergreen** (fallback): the best backlog item when no radar story passes the gates.
4. **Hard gates** (fail one = drop or re-frame): the seven in "Topic gates" below — familiar entity in the title; one tension; fits the channel; enough primary sources to fact-check; policy-safe; not already covered well by a big channel in the last 14 days unless our angle is clearly different; not our own formula. List what was dropped and why in the shortlist.
5. **Score the survivors** (0–5 each, weights in brackets, max 100):

   | Criterion | 5 means | 1 means | Evidence |
   |---|---|---|---|
   | Trend momentum (×4) | top-5 radar story, 10+ outlets this week, Reddit/HN/suggest signals | no fresh coverage | radar momentum, outlets 7d/30d, suggest hits |
   | Gap (×4) | no long video on the angle, or only weak/old ones | a strong video (≥ 100k) from the last 14 days on the same angle | radar YouTube coverage, `topic_gap.py`, a manual search |
   | Packaging strength (×5) | 5 title drafts from the breakout families all clickable and true; one-object thumbnail obvious | the title needs a niche name or a second sentence | the 5 drafts + thumbnail line |
   | Evergreen tail (×3) | will still be searched in 6 months (entity + mechanism people keep asking about) | dead once the news cycle ends | search-suggest presence, backlog evidence, `yt_scan` outliers |
   | Production fit (×4) | tier A–B real media for the main entity (Commons, agency, press kit), a map or chart in every chapter | only tier C/D media, nothing drawable | quick `fetch_media.py` check or Commons search |

   Score = 4·momentum + 4·gap + 5·packaging + 3·evergreen + 4·production (each 0–5) → 0–100. Ties go to packaging, then gap. In the hot lane, momentum below 3 is a drop; in the evergreen-with-a-hook lane, evergreen below 3 is a drop.
6. **Packaging drafts for the top 5.** 5 title drafts each from the channel's `packaging.title_families` and the breakout families (How [entity] lost $N in [time]; Why the world's [superlative] [thing] failed; the hidden thing inside [familiar thing]; [entity] vs [entity]; the people: The [person] who …), ≤ the style's `title_max_chars`, literally true; one one-object thumbnail idea. Rotate families against the channel's last two titles (gate 7).
7. **Verify the top pick's core facts** against at least two independent sources, at least one primary (filing, agency, company statement, court record); check every date against today's date. Note what is still unconfirmed.
8. Write `channels/<slug>/trends/<date>_SHORTLIST.md`: the 5 best with score breakdown, lane, 3 titles, thumbnail idea, key primary sources, main risk; the recommended pick and a reserve (different lane if possible). **Human gate G1: the user picks topic, title and thumbnail concept.** Then create `channels/<slug>/videos/<video>/STATUS.md` (template in `explainer-flow`).
9. Keep the evergreen backlog alive: once a month, or when the shortlist has no evergreen-with-a-hook candidate, refresh it with the old method (outlier titles in the niche, 15–25 candidates, `topic_gap.py`, Gemini on the strongest existing video for the top 5, ranked `BACKLOG.md`).

## Stage 2R — Remake mode (DEFAULT; user decision 17/11/2026, rules tightened the same day)

Topics are **remakes of proven outliers**. Keep what made the source work: topic, central tension, hook type, a front-loaded pace, a new open loop every 2.5–3 minutes. Change the structure and the angle. Second-accurate skeleton copying and cut-by-cut source beat tables are retired; the angle line and `remake_diff.py` replace them. The first two pilot films were made under the old rules and are not redone.

1. **Pick.** Outliers at least 3x the channel's median and 300k views. Topic proof: two outliers on the topic from different channels; the source is at least 12 months old or from a channel over 500k; no two remakes of one channel within six uploads. The shortlist goes to `research/remake/SHORTLIST.md` (8 per channel: views, ratio, length, why it worked, what we add, working title). Check the hard gates (policy, primary sources available). Picked at **G1** (batched with G2, see `explainer-flow`).
2. **REMAKE_MAP.md** in `research/remake/<slug>/`, for analysis only (the download is never re-uploaded or shown): `yt-dlp` video and subs into `transcript.txt`; scene-detect cuts/min (overall, first 60 s, per chapter); 1 frame per 10 s contact sheet; their chapter starts as % of runtime; their title and thumbnail (object, conflict, words, colour field); their visual mix. Plus one angle line: **"They asked X. We ask Y."** Y must be in our title.
3. **Our own research and script.** `SOURCES.md` from primary sources, then the independent fact-check (hard gate below). Upgrades are why the remake exists; aim for 3-5 (newer facts, court outcomes, the money trail, a myth the original got wrong, real maps and documents where they used stock). `explainer-writer` writes `SCRIPT.md` from SOURCES, never from the transcript, with each section tagged by topic and `new: yes/no`.
4. **Deviation limits, enforced by `python3 explainer/kit/tools/remake_diff.py` (reads REMAKE_MAP, SCRIPT, transcript, both titles and thumbnails). Any failure blocks G2:**
   - at most 30 % of our chapter starts within +-1.5 % of runtime of a source chapter start;
   - longest in-order common run of topic tags covers at most 60 % of our sections;
   - our first 30 s shares at most 25 % of content words with their first 60 s, and frame 0 shows a different object;
   - at least 30 % of spoken words in `new` sections, including one chapter of 12 % of runtime or more;
   - 0 shared 6-word runs (`overlap_check.py --n 6`, `--allow` for proper nouns) and at most 3 shared 4-word runs per 1,000 words;
   - packaging: title shares at most one content word beyond the entity; the thumbnail differs in two or more of object pose, conflict, words and colour field, with difference-hash distance at least 20 of 64 bits.
5. **Naming the source.** The description may carry `Further viewing: <their title>, <channel>` with no link. It costs nothing and defuses a clone callout. Do not use it unless the operator agrees for that video.
6. **FACTCHECK.md is a hard gate.** A separate agent that receives only the claims (never the research notes or the script's sources) writes `FACTCHECK.md`. `CLAIMS.md` has `tier` and `role` columns (role: thesis, person, supporting). Every thesis claim and every claim about a named person needs a primary source (not tier S); `qa_film.py` fails with a missing `FACTCHECK.md` or a tier-S thesis or person row. G2 shows the verdict column.
7. Then the normal flow (voice, ch1, chapters, G4). A pace above the style's range is fine when the operator approves it at G3; record it in STATUS.

Worked examples (old rules): `research/remake/<slug>/` (made on your first remake).

## Stage 3 — Topic brief (per video, feeds production)
1. Deep research with web search (Sonnet subagent): timeline, numbers, quotes, each with source URL; 3–5 "shock facts" for the hook; known counter-arguments.
2. Independent fact-check: a separate subagent that receives only the claims, not the research notes, writes `FACTCHECK.md` (hard gate, Stage 2R item 6).
3. Read the channel's `STYLE.md`. Write the packaging first (section "Packaging" below), then the outline with the 5-stage arc (hook paradox → assumption → hidden mechanism → core truth → open question), one recurring physical metaphor + matching SFX (plus the channel's recurring device from its style), open loops and callbacks placed by minute, target length from the style's `length_min` (**default** 9–12 min). The outline and the script that follows obey the "Script rules" below.
4. Real media list: every named company, product, place or historic moment in the outline gets a row (entity, where it appears, media type logo/photo/footage). Fetch candidates with `explainer/kit/tools/fetch_media.py` (logo / image / commons / archive) into `research/<slug>/media/`, look at `contact_sheet.png`, and record the chosen file + license. Mark any `non-free (fair use)` file for the human; prefer a free alternative. Also list the footage per chapter (target `real_media.footage_share`, default 5–15 %): 1+ clip per chapter as era/atmosphere B-roll, found with `commons-video`, `nasa-video`, `archive --vetted`, `pexels --video`; note licence, risk and Content ID note, and never plan footage of an event that has none (see `research/upgrade/footage/FOOTAGE_REPORT.md`).
5. Write `research/<slug>/BRIEF.md` (click promise, thesis, outline with BUT/THEREFORE between beats, claims table with URLs, competitor notes, **5 titles from 3 families + 3 thumbnail concepts in 3 layouts**, the next video to pitch at the end, required new assets, **real media table with chosen files and licenses**). Run the "Quality bar" at the end of this file before showing it. **Human gate 1 of the production pipeline.**

## Topic gates (stage 2, before scoring)

Why: views are decided mostly by the subject and its packaging. In a 38-million-video cohort the top 1 % took 54 % of first-week views. Tradeoff Layer's nine videos in one style run from 2k to 1.7M, and the split follows the title's subject: famous companies 167k–1.7M, a single hack or a narrow mechanism 2k–9k, two others at 40k and 107k (playbook §2, §7). New animated channels broke out at a median of video 3–4, on titles that pair a familiar entity with money, failure or a hack superlative (NEW_CHANNEL_BREAKOUTS.md).

Hard gates (all must pass):

1. **Familiar entity in the title.** A name, product or everyday object that a US/UK viewer outside the niche already knows: Nike, an iPhone, IKEA, Times Square. An incident name, a CVE, a regulator, a gang name or a niche vendor does not count (the radar marks familiar entities from `trend_sources.json`).  Anchor the story to something the viewer owns or a name they know, and to the people in it.
2. **One tension in one line.** A statement that sounds wrong, a versus, an impossibility, a hidden thing inside a familiar thing, a loss with a number, or a bill nobody pays. If the line needs a second sentence to surprise, the topic fails.
3. **Fits the channel.** It matches the niche line and the "what we never do" list in `channels/<slug>/STYLE.md`.
4. **Enough primary sources to fact-check.** At least two independent sources for the core facts, one primary (filing, regulator/agency, court, company statement). An event known only from one outlet or from attackers' own claims waits.
5. **Policy-safe.** No victim-blaming (a breached company or a crash crew is not the joke or the villain without an official finding); no attribution beyond what officials or courts state ("France blamed…", not "Iran did…"); no named suspect who has not been charged; no step-by-step attack method; no advice on money, law or health; crash topics only through the investigation's published facts.
6. **Not already covered well in the last 14 days** by a big channel (a long video ≥ 100k views, or ≥ 3× its channel median, on the same angle) unless our angle is clearly different and the difference fits in the title. Check the radar's YouTube coverage and search by hand.
7. **Not our own formula.** Different metaphor, chapter structure and title family from the channel's last two videos.

Soft checks (lower the score, do not drop): outlier proof (two existing videos on the subject or its nearest sibling at ≥ 3× their channel median, one from a channel under 100k subscribers); evergreen tail (the title still makes sense in two years — a hot-lane title may break this, an evergreen-with-a-hook title may not).

Expect most videos to miss: the median new channel's best of its first ten long videos reached 1,948 views in 30 days, and 31 % got one over 10,000. Judge the picks on their best one in ten, and keep the gates even when a hot story tempts.

## Packaging (in every BRIEF, written before the outline)

1. **Click promise.** One sentence: "The viewer clicks because they expect to learn ___." Title, thumbnail, frame 0 and the first spoken sentence all serve it. YouTube picks A/B winners by watch time share, not click-through rate, and reads a good first 30 s as having "matched the viewer's expectation of the video's thumbnail and title". A promise the video does not pay loses.
2. **Five titles from at least three families.** Each ≤ 55 characters (or the style's `packaging.title_max_chars`), entity in the first 30, literally true, answered in the video. The channel style ranks the families for its niche (`packaging.title_families`); lead with its first family, but still use three.
   - Why/How + a statement that sounds wrong: "Why IKEA Wants You to Get Lost", "How a Vending Machine Knows Your Coin Is Fake".
   - Story promise or hidden thing: "Apple Had No Idea This Was Inside 174 Million iPhones", "We Should Be Flying Like This".
   - Versus or impossibility: "Can Google Beat Nvidia?", "Why No One Can Copy ASML?".
   - A number and a thing the viewer owns or knows: "$600 Million Warship VS $5 Tracker", "200 Million User Records... Breached".
   - At most two of the five end in a question mark. Large samples disagree on whether question titles lose views, and a channel of only "Why would...?" titles reads as a template.
   - No more than 2 of a channel's last 5 published titles from one family.
3. **Thumbnails: three concepts, then three variants.** The method, the layout rules and the 160 px test live in one place, `explainer-direct` section "Thumbnails". The BRIEF carries only the reference table and six concepts from three families (object damaged or in conflict; a number that looks wrong on the object; a versus split), of which the operator strikes three at G1. Real logos follow the channel style (`packaging.real_logo_ok`).
4. **Test.** In Studio's A/B test (desktop, needs advanced features, up to 3 variants of title, thumbnail or both, up to 2 weeks) upload variants that are clearly different. On a small channel the result is often "Inconclusive"; then keep the variant with the best Home and Suggested click-through rate together with average view duration. Never judge on click-through rate alone: high CTR with low view duration is YouTube's own definition of clickbait.

## Script rules (stage 3 outline, and the SCRIPT written from it)

(P) = YouTube statement, (M) = our measurement of competitor scripts, (O) = practitioner opinion. Details: playbook §3, §5, §6. Timing and count numbers here are **defaults**; the channel style's `hook`, `script`, `chapters` and `ending` keys override them (its competitors' own measurements are in `channels/<slug>/research/EVIDENCE.md`). The rules without numbers (no intro before the story, BUT/THEREFORE, a turn at each chapter start, no summary ending) hold for every channel.

**Hook (default: 0:00–0:35, never past 0:45, at most 95 words; the style's `hook` sets its own)**
- Sentence 1 ends by 0:05 (15 words or fewer). It is a concrete scene, number or claim about the thumbnail's object. Not a question, not context. (M: ten of ten competitor videos.)
- The title's promise is spoken by the style's `hook.promise_by_s` (default 20 s), in words close to the title; `qa_hook.py --script SCRIPT.md` checks it from word counts before any voice is paid for. (P; O: "the first seven seconds of a video is about confirming the click".)
- One tease line of 20 words or fewer that raises the stakes above the title ("Here's the strange part: what makes it impossible to copy is the thing that almost killed it"). Not a list of what the video covers.
- Then cut into the story with a date or a place ("It's 2013.").
- Not in the first 60 s: the host's name, the channel's name, "in this video", "welcome", subscribe, sponsor. (M: none of 13 competitor videos in one check; 2 of 10 in another, both a one-line brand tag on a long-established channel.) If the host names herself at all, it is one clause in the sign-off.
- Short 1 reuses this hook and links back, so the first 5–10 s must work on their own. (P)

**Body**
- Write BUT or THEREFORE between every two beats of the outline. "And then" means cut one beat or reorder. (O: Parker and Stone.)
- Every chapter (60–90 s) opens with a turn in its first sentence: a new problem, a reversal, a raised stake. Never with its own conclusion. (O)
- One planned re-engagement at 40–50 % of the runtime: the most surprising fact, or a reversal the hook did not promise. (O)
- **One person with a decision.** The film follows one real named person (or one named body) who must choose; say who by the end of the hook's story start.
- No list over three items without a turn (a number that breaks the pattern, a reversal), and no stretch over 75 s without a turn.
- Contrast turns (but, except, until, instead, however, yet): at least 1.0 per minute of script. (M: competitors 1.0–2.6; our first two scripts 0.5–0.6.)
- Spoken questions: at most one per chapter, never two in a row. Prefer a statement that opens a gap. (M: competitors 0–0.6 per minute; our first two scripts 1.1–1.6.)
- No backstory before the hook's question. A history block runs 75 s at most, then back to the mechanism or the conflict. (O)
- At most 3 loops open at once. Each has a closing time in the outline. The last one to close is the film's last payoff (see Ending).
- Sentences: median 8–13 words, at least 15 % of them 6 words or fewer, none over 30 (the voice stumbles; universal). Pace from the style's `script.wpm` (**default** 150–175 wpm), the hook in the upper half.
- Every chapter has at least 2 concrete numbers, names or dates from the claims table, and the film has about one light line per 2 minutes (an analogy with a twist, an understatement). Never a joke about victims.

**Ending (default: 30 s or less from the last payoff to the last frame; the style's `ending` sets its own)**
- Last payoff → one callback line to the opening image → the open question (optional) → the **pitch**: one or two sentences that name one specific video on the channel and the question it answers. The pitch is spoken over the end-screen plate (8–12 s, see `explainer-direct`).
- No summary, no "in conclusion", no "thanks for watching", no bare "hit subscribe" as the last line. (O; P: end screens run in the last 5–20 s and should "feature elements that are relevant to the video".)
- A channel's first video has nothing to point at: pitch the next approved backlog topic by its question, and set the end screen to subscribe + "best for viewer".

Check the counts with the two `grep` lines in playbook §16.

## Quality bar: a script is not done until every line is true

- [ ] The title names a familiar entity and holds one tension; the click promise is written at the top of the BRIEF.
- [ ] 5 titles, 3 families, each ≤ 55 characters. 3 thumbnail layouts, each ≤ 4 words, none repeating the title, one without the host, all three checked at 160 px.
- [ ] Sentence 1 is about the thumbnail's object and ends, the promise is spoken, and the story starts by the style's `hook` times (defaults 0:05 / 0:20 / 0:35).
- [ ] No host name, channel name, "in this video", welcome, subscribe or sponsor line in the first 60 s.
- [ ] BUT or THEREFORE stands between all outline beats. Contrast turns ≥ 1.0 per minute. At most one question per chapter.
- [ ] Every chapter's first sentence is a turn, not a summary. A re-engagement sits at 40–50 %.
- [ ] Every open loop has a closing time; the last one closes as the film's last payoff.
- [ ] The ending is 30 s or less, names one next video, and contains no summary or thanks.
- [ ] Every spoken claim has a row in the claims table with a verdict from the independent fact-check.
- [ ] Metaphor, chapter structure and title family differ from the channel's last two videos.
- [ ] Pace estimate inside the style's `script.wpm`; no sentence over 30 words.
- [ ] Hook timings, chapter length, ending length, real items per chapter and title/thumbnail families match the channel's `style.json` (or the defaults, named as such in the BRIEF).

## Channel hygiene (YouTube's "inauthentic content" policy; playbook §9)

- One thesis and one public source list per video. Reviewers read titles, thumbnails, descriptions and the About section; the About section says who researches, writes and approves.
- All channels share a kit. Never copy a title, description, tag set, upload day and hour, or chapter structure from one to the other.
- The host explains mechanisms. No advice on money, law, health or politics.
- Disclosure: not required for our cartoon pictures or for AI help with scripts. Real photos and footage go in unaltered; an AI-edited real photo needs the "altered content" switch.

## After upload (feeds the next brief)

At 48 hours and at 7 days (schedule and checklist in `explainer-flow`) read in Studio: Intro (share still watching at 0:30), typical retention against our own last videos, top moments, dips, and click-through rate on Home and Suggested. Map each dip to the second in the beat plan, write down what that beat was, and add a row to `channels/<slug>/LEARNINGS.md` (rules that hold across several videos go into the playbook and, at refresh, the channel style). Use engaged views, not public views (since 24 Aug 2026 a public view counts from the first frame).
