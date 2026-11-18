---
name: explainer-shorts
description: "Make YouTube Shorts (1080x1920, length per channel style, default 30–50 s) for the cartoon-explainer channels (one folder per channel in explainer/channels/) from a finished long video. Default is NATIVE vertical Shorts: a fresh short script from the long video's fact-checked lines, new channel voice, a HyperFrames 1080x1920 composition with the kit (talking host, SFX, real media, burned word captions, hook title, progress bar, end card), render, master, QA. Fallback is a cheap cut from the 16:9 film with captions and a punch-in. Use when the user asks for Shorts, vertical clips, teasers or promos of an explainer video, or to pick the best moments of a video for Shorts."
---

# Explainer Shorts

A finished long video goes in. Three to five Shorts come out, each one idea with its own hook, plus titles, descriptions and the upload notes. Everything lives in `explainer/`:

| Path | What it is |
|---|---|
| `shorts/pick_segments.py` | Ranks self-contained 20–55 s stretches of the long video (sentence-bounded, scored for a strong opener and a payoff) |
| `shorts/styles/<channel>.json` | Channel **brand** for Shorts: colours, font, voice, avatar, host poses, mouth-patch folder, end-card line (read by `new_short.py`) |
| `channels/<slug>/STYLE.md`, `style.json` | Channel **style** from its competitors (skill `explainer-channel-style`). Its `shorts` block sets this channel's Shorts length, host use, caption look and hook pattern; its `brand.shorts_style` points back at the brand json above |
| `shorts/native/new_short.py` | Scaffolds a native vertical composition (kit, `shorts.js/.css`, style, font, avatar, host, mouths, voice, media + credits, template) |
| `shorts/native/shorts.js`, `shorts.css` | Vertical layer on top of `kit.js`: hook title, progress bar, word captions, end card, safe zones, `sfxGain` |
| `shorts/native/finish_short.sh` | check → render → master −14 LUFS → `qa_audio` → freeze → silence → ffprobe → contact sheet |
| `shorts/native/contact_sheet.sh` | 1 fps sheet with the Shorts UI zones outlined |
| `shorts/make_short.py` | **Fallback**: cut a Short out of the 16:9 film (film on top, punch-in crop or host panel, ASS captions with digits from the SRT, end card, master) |
| `shorts/common.py` | Film-time words (chapter offsets = cumulative `trim_v2.json`), sentences, script beats |

Worked example: none ships with the repo; your first Short becomes the example (keep its `SHORTS.md` and beat plan).

Read `explainer-direct` (and `kit/CRAFT_RULES.md`) first: every composition rule there applies here too. Then read the channel's `STYLE.md` (section "Shorts") and the `shorts` block of its `style.json`. This skill only adds what is different for vertical. Numbers below marked **default** apply only when the channel style does not set them; the platform facts in the research table are universal.

## What the human approves

When the Shorts are made and which days they go out (first one within 3 days of the long video, then the style's `publish_slot.shorts`) is set in the skill `explainer-flow`.

1. **The pick and the scripts** (step 2). Make ONE hook Short per long video (more only for a video at 5 % CTR). Show its script with its source lines before paying for voice. If the user has already said "go" for a batch with a budget, stay inside it and say what you spent.
2. **Cost**: Shorts come out of the long video's 10 USD budget (voice ≈0.06 USD per Short; new kie images allowed, 0.03 USD each, when they make the Short clearer). Real media follow the tiers in explainer-direct "Real media". Never read `.env`; never print keys.
3. **Publishing**: never upload, schedule or make public without the user's explicit OK for that Short.

## Research basis (checked 15/11/2026)

Full findings, sample sizes and what could not be verified: kept out of this repo; the table is the summary. "YouTube" below means a Help page or YouTube's own blog.

| Topic | Takeaway | Source |
|---|---|---|
| Max length | 3 min for square or vertical uploads (since 15 Oct 2024); no `#Shorts` needed. A Short over 1 min with any Content ID claim is blocked | YouTube |
| Best length | **No official number, and the data disagree.** A 2023 study (5,400 Shorts) found longer did better; two 2026 datasets (16,537 and 108,138 Shorts) put the peak of median views at 11–30 s. Nothing is specific to explainers. House range stays **30–50 s**, one idea, plus one 20–30 s variant per batch so we learn our own answer | Todd Sherman (YouTube, 2023); Galloway/Gileta 2023; OverseerOS, quso.ai 2026 |
| Hook | "You have one second to hook someone" (Jenny Hoyos on YouTube's blog). Visual hook on frame 0 and a spoken hook in the first clause. No intro, no logo sting | YouTube blog, 28 Jan 2025 |
| Hook metric | Studio's **Stayed to watch** (viewed against swiped away). Under 60 % rarely performed; the best Shorts sat at 70–90 % | YouTube; Galloway/Gileta 2023 |
| Captions | Burned-in word captions stay, for style and accessibility: big, high contrast, 2–4 words per line, active word highlighted. No sourced data shows they lift retention, and Google's Shorts ads guide assumes sound on | playbook §8 |
| Safe zones | No official spec. Bottom 15–20 % (title, channel, music, **related-video pill**), right ~120 px action column, top ~120–210 px icons. HyperFrames' own Shorts band is stricter: y 288–1248, x 48–888 | reap.video, clipspeed, aicarousels, HyperFrames `safeAreas.js` |
| Loop | Replays add public views but **not** engaged views, and we found no YouTube statement that loops raise recommendations. Do not trade the payoff or the pointer for a loop | YouTube |
| View counting | Since 31 Mar 2025 every start or replay counts as a view. **Engaged views** (stayed past the first seconds, loops excluded) is what Studio analytics and the Partner Program count | YouTube; YouTube blog, 19 Aug 2026 |
| Link to long video | Studio → Content → the Short → **Related video**: a tappable pill on the Short, pointing to a video, Short or live on the same channel. Needs **advanced feature access** on the channel. The flow is small: only 2 % of channels got 2 % or more of their long-form traffic from it | YouTube; Spotter 2024 (5,000+ channels) |
| Conversion | YouTube's own advice: a verbal and a visual cue in the final 5 s ("Explicitly tell them what to do"); the Short must be "a standalone piece of value"; the long video's first 5–10 s "should directly address the topic" | YouTube blog, 14 Jul 2026 |
| Subscribers | Per 10,000 views: long-form 22.7, Shorts 16.9. Shorts buy reach; the long video converts | Galloway/Gileta 2023 |
| Cadence | Our cadence (17/11/2026): one hook Short per long video, at most 1 per day per channel. Research: about 5 Shorts a month goes with more views per long video (8,789 against 4,364 for channels with none; a correlation), and the gain is gone past ~35 a month. Shorts published within 3 days of the long video sent it more viewers (case level). House rule: **max 1 Short per day per channel**. Never delete and repost | Metricool 2026 (800k videos); Spotter 2024; Todd Sherman 2023 |
| Hashtags | Not required. 0–3 topic tags (three show by the title) | YouTube |

Treat every number here as a starting point: after 2–3 weeks read the channel's own Studio data (last section) and adjust.

## Steps (native, the default)

### 1. Pick the moments
```
python3 shorts/pick_segments.py --words vo/<slug> --trim film/<slug>/final/work/trim_v2.json \
    --script research/<slug>/SCRIPT.md --out film/<slug>/shorts/candidates.json
```
Read the top 12 and choose 1 (3 only for a video at 5 % CTR) by judgement: one idea each, a number or question that hooks, a payoff inside 45 s, little overlap. A low score caused only by a context-leaning opener ("For that, we…") does not matter in native mode: you rewrite the opener. Write down why you chose each one (`SHORTS.md`).

### 2. Write each script (length from the style's `shorts.length_s`; **default** 30–50 s, 90–125 words at ~165 wpm, plus one Short per batch at 20–30 s, 55–80 words)
- **Sentence 1 is the hook**: the most surprising number, or a statement that sounds wrong; a question only when it is the long video's title. Its first clause (6 words or fewer, done by 2 s) already names the subject. No "In this video", no greeting.
- **One idea**, one payoff (the number lands, the answer is given). **The Short stands alone**: a viewer who never taps through still got a complete answer.
- **The last sentence is the pointer** (8–14 words): it says what the full video answers and that it is linked. "How that deal began in 1962 is the full video, linked below." It opens a question this Short did not answer; it does not repeat the payoff. The end card is on screen while it is spoken (step 5). Nothing comes after it: no loop-back line, no silent tail.
- **Short 1 is the long video's hook**, so a viewer who taps through hears the same promise paid in the long video's first 5–10 s.
- **No new claims.** Use only lines from the long video's SCRIPT/FACTCHECK, with their caveats (dates, "about", who said it, the other side's reply). Numbers spelled as spoken ("twenty twenty-six").
- Save as `film/<slug>/shorts/sN/vo/sN.txt`.

### 3. Voice
```
python3 fal_tts.py film/<slug>/shorts/sN/vo/sN.txt film/<slug>/shorts/sN/vo/sN.mp3 <voice>   # the brand json's "voice" (an ElevenLabs voice name or ID)
python3 kit/tools/vo_build.py film/<slug>/shorts/sN/vo/sN_w film/<slug>/shorts/sN/vo/sN.mp3
```
One call per Short. Check the words list against the text. Pace about 145–175 wpm.

### 4. Scaffold
```
python3 shorts/native/new_short.py --style <slug> --dir film/<slug>/shorts/sN --vo film/<slug>/shorts/sN/vo/sN_w \
    --img prop_jet_engine prop_printer film/<slug>/ch01/assets/img/scale_beam.webp ... \
    --media film/<slug>/ch01/assets/media/logo_brand.png ...
```
`--img` names come from `film/assets/img` (or give a path); `--media` copies the file and its `CREDITS.json` row. The template's END is the last word + 2.3 s; step 5 shortens it (end card over the pointer).

### 5. Direct the composition (by hand, as in explainer-direct)
Write the beat plan comment first. Vertical layout (1080×1920):

| y (px) | What |
|---|---|
| 0–160 | nothing to read (Shorts icons) |
| 168 | progress bar (`shorts.js`) |
| 196–432 | **hook title**, on screen from frame 0. ≤ 6 words, 2 lines, one `<em>` accent word |
| 440–900 | MAIN zone: the one big object of the beat (photo, scale, chart, number). Below y 600 keep it right of x ≈ 280 (the host's head) |
| 600–1235 | **host**, bottom-left, mirrored so `point_left` points at the objects, feet on the floor at 1235. Labels, stamps, counters at x 440–890, y 900–1230 |
| 1240–1390 | **word captions** (`shorts.js`), centred on x 470, inside x 50–890 |
| 1400–1920 | nothing to read: Shorts title, channel name, related-video pill, music line. `.sh-floor` paints a calm floor here |
| x > 950, y > 960 | nothing to read or important (like/comment/share column) |

Rules:
- **Frame 0 is the hook picture**: the main object is already on stage at t = 0 (no fade-in). A re-entrance of a frame-0 object later must use `immediateRender: false` (`K.pop` renders immediately and blanks frame 0; see `s2/index.html` `popBack`).
- Big things: one main object at a time, readable on a phone (numbers ≥ 120 px, labels ≥ 40 px). At most 2 labels on screen.
- **The host is a tool here too** (see `explainer-direct`; the user rejected "host on screen the whole time", confirmed for Shorts 15/11/2026, for every channel). Frame 0 belongs to the hook object. How much host a channel's Shorts use is its style's `shorts.host` (**default**: he may stand in his zone, come in on the second sentence, shrink to a corner, or stay out for the whole Short when the object needs the width; then MAIN may use x 60–890 below y 600). Change his state at least once in any Short he appears in. Whenever he is on screen: `talk`, `blinks`, `breathe` for that range, pose change every 3–6 s, nods on stressed words. Poses with mouth patches only (the ones in your `window.KIT_FACES`). Not yet test-rendered without the host: check the first such Short's contact sheet for an empty bottom-left.
- Wrap the host as `Shorts.snapPose(K, K.host(...))`: pose swaps become hard cuts. The kit's 0.06 s crossfade shows two ghost hosts on one frame, which is visible in a 1 fps contact sheet and on a paused phone.
- Real media as stickers/taped photos with on-screen credit; CC BY/BY-SA credits go in the description.
- Do not use `K.whip` (it assumes 1920 px width). Change MAIN objects with pop-outs and drops on the same set; a Short is one set.
- `Shorts.create(K, { end, hook, merge, card })`: `merge` turns spoken numbers into digits for captions (`["twenty twenty-six,", "2026,"]`, `["M B A", "MBA"]`). Keep the `merge` keys exactly as the words appear in `words.json`.
- Call `S.finish({ sfxGain })` before `K.finish()`; use `sfxGain` (+1…+3 dB) if `qa_audio` says the SFX bus sits more than 18 dB under the voice.
- **End card over the spoken pointer, no silent tail.** Pass `card: { at: <start of the pointer sentence>, line: "FULL STORY:<br>LINK BELOW", sub: "<Channel> · <3–4 words on what it answers>" }` and set END to the last word + 0.6 s in three places (root `data-duration`, scene `data-duration`, `const END`). The card must be on screen for at least 2.1 s (HyperFrames fails a closing line under 2 s), so the pointer sentence has to run 1.6 s or longer. The stage fades, captions keep running, the host stays. This replaces the silent 2.15 s card after the last word: YouTube asks for a spoken and a visual cue in the final 5 s, and a dead second at the end lowers average percentage viewed. Checked with `check` and `snapshot` on a test Short (card at 34.5, END 37.4, 0 errors); not yet rendered and mastered, so look at the last 3 s of the first contact sheet.

### 6. QA loop (at least two snapshot rounds)
```
cd film/<slug>/shorts/sN && npx -y hyperframes@0.9.46 check
npx -y hyperframes@0.9.46 snapshot --at <12–14 times incl. 0> --no-end -o snaps
cd - && sh shorts/native/finish_short.sh film/<slug>/shorts/sN film/<slug>/shorts/short_N.mp4
```
Expected warnings, not errors: `outside_safe_zone` for the title band and captions (HyperFrames' Shorts band is stricter than ours), `line_unread` for caption chunks (they follow speech), `nested_structure_needs_subcomposition`, `duplicate_media_discovery_risk`. Fix every other finding.

### QA checklist (each Short)
- [ ] Frame 0 shows the title and the hook picture (look at `snapshot --at 0`).
- [ ] The hook's first clause ends by ~2 s and names the subject; the payoff lands before the pointer sentence.
- [ ] The Short gives its own answer with no outside context.
- [ ] The last sentence is the pointer; the end card is up for at least 2.1 s while it is spoken; the video ends 0.6 s after the last word.
- [ ] Captions follow the style's `shorts.captions` (**default**: one line, 2–4 words, active word highlighted); always readable, digits not spelled numbers, never behind the host.
- [ ] Contact sheet (`short_N_contact.jpg`): nothing to read inside the outlined zones (bottom, right column, top); nothing important hidden behind the host.
- [ ] No overlap, clipping or text wrapping badly; no stray glyphs (e.g. `*`); no ghosted double host.
- [ ] `finish_short.sh`: check passed, `audioCount` = 1 + cues, −14 LUFS ±0.5, true peak ≤ −1.5 dBTP, SFX bus 12–18 dB under voice, no freeze > 1 s, no silence over 0.9 s anywhere, 1080×1920 30 fps AAC, 20–60 s.
- [ ] Every claim is in the long video's fact-checked script, with its caveat.
- [ ] Credits for CC BY/BY-SA media are in the description.
- [ ] Say what you could not check (you cannot listen).

## Fallback: cut from the film

Cheap and fast, but it looks like a cropped TV, and the 16:9 picture is small on a phone. Use it to test a moment, or when a native Short is not worth it.
```
python3 shorts/make_short.py --film film/<slug>/final/<final>.mp4 --start <s> --end <s> --words vo/<slug> \
    --trim film/<slug>/final/work/trim_v2.json --srt film/<slug>/final/<final>.en.srt --style <slug> \
    --hook "WHY IS THIS *SO EXPENSIVE*?" --zoom "1.2-18.8:820,330,1100,330;19.3-32.5:600,380,1300,390" \
    --out film/<slug>/shorts/cut_N.mp4 [--loop]
```
Take `--start/--end` from `candidates.json`. Choose the zoom boxes (film pixels, Short-relative times, ~10:3) from a 1 fps sheet of the segment; outside them the panel shows the host bust and the channel name. Audio gets a 0.1 s fade in and out and is mastered with `kit/tools/master.sh`. `--loop` drops the card and dissolves the last 0.3 s back to the first frame.

## Style config

The brand json and the channel style split the work: `shorts/styles/<slug>.json` holds what `new_short.py` needs to scaffold (palette, fonts, voice, avatar, poses); `channels/<slug>/style.json` → `shorts` holds the editing choices (length, host, captions, hook, pace). Do not copy one into the other.

`shorts/styles/_example.json` is the template: palette, `font_display` (fontconfig name; `font_display_file: "auto"` resolves it with `fc-match`), `voice`, optional `avatar`, optional host (`host_dir`, `mouth_dir`, `host_poses`; leave `host_poses` empty for a channel without a host, then delete the host lines from the scaffolded `index.html`), `thumb_look` (`outline` for a light ground, `halftone` for a dark one).
A new channel = a new brand JSON with the same keys, plus a channel style (`explainer-channel-style`) before its first Short.

## Upload and scheduling notes (only with the user's OK)

- Before a channel's first Short: get **advanced feature access** (Studio → Settings → Channel → Feature eligibility: ID or video verification, or enough channel history). Without it the Related video option does not exist.
- One Short per day per channel, at most, and normally just the hook Short of that day's long video (it goes out the same day as the long video). Extra Shorts only for a video at 5 % CTR, in story order within 10 days. Never delete and repost a Short.
- In Studio: **Details → Related video = the long video**. This is the link that sends viewers on; do not rely on description links (not clickable on Shorts).
- Title ≤ 60 characters, a question or hook, matching the on-screen hook but not identical. No `#Shorts` needed.
- Description: 2 lines + `Full video: <link>`, then sources and media credits.
- Pin a comment pointing to the full video.
- After ~7 days read in Studio, per Short: **Stayed to watch** (under 60 % means the hook failed; aim for 70 % or more), engaged views (not public views, which count every replay), average percentage viewed, and in the long video's traffic sources how many views came from Shorts. Compare the 20–30 s variant with the 30–50 s ones. Write what you learn into this skill and into the playbook.
