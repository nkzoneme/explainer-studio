---
name: explainer-direct
description: Production flow for one cartoon-explainer video — voiceover first (ElevenLabs with word timestamps), beat plan, hand-directing each beat as a HyperFrames/GSAP composition with the craft kit (synced sound effects, secondary motion, talking and blinking host), QA loop, render and loudness master. Use when the user asks to produce, direct, animate, render or fix a chapter or a full explainer video from an approved script or brief, or to add sound effects / mouth movement / more motion to an existing composition.
---

# Explainer production: direct one video by hand

You are the director and animator. A script goes in; a 1920×1080 MP4 with voice, picture and sound effects comes out. Every beat is designed by hand. Nothing is templated: the look that the client approved came from a model writing each scene for its exact sentence, and that stays.

Everything lives in `explainer/`:

| Path | What it is |
|---|---|
| `kit/CRAFT_RULES.md` | The numbers: sound density, sync, loudness, mouth, blinks, timings. **Read it before directing.** |
| `kit/kit.js`, `kit/kit.css` | Helpers. The header comment of `kit.js` is the API reference. |
| `kit/sfx/` | CC0 sound library (legacy mode). An optional role-levelled library in `kit/sfx_v2/` (format in `kit.js`) enables `sound: "edit"`; music beds go in `kit/music/<channel>/`. |
| `kit/tools/` | `vo_post.sh`, `vo_build.py`, `speech_levels.py`, `face_grid.py`, `qa_audio.py`, `qa_freeze.sh`, `qa_pace.py`, `qa_hook.py`, `qa_film.py`, `thumb_sheet.py`, `retention_map.py`, `master.sh`, `mix_bed.sh` |
| `film/assets/img/` | The image library (backgrounds, host poses, props). |
| `fal_tts.py`, `kie.py` | Paid: ElevenLabs voice via fal; images via kie (about 0.03 USD each). |
| `channels/<slug>/STYLE.md`, `style.json` | **The channel's own style** (skill `explainer-channel-style`): pace, host use, media mix, visual system, type, sound, hook, chapters, ending. **Read both before Step 2.** `channels/README.md` has the schema and the defaults. |

## The channel style decides the look; this skill decides how to build it

Each channel has its own style, measured from its own competitors (`explainer/channels/<slug>/`). The slug is the folder name. The beat plan and the QA use its `style.json` targets: `pace` (full-frame changes per minute, first 60 s, gaps), `host` (visible and presenter shares, longest presenter stretch, modes, frame 0), `mode_change_s`, `media_mix`, `real_media`, `visual_system`, `typography`, `sound`, `hook`, `chapters`, `ending`. Where this skill gives a number for any of those, it is marked **default**: use it only when the channel's style.json does not set that key, and say in the report that the default was used. A channel without a style gets one before its first film.

Universal, for every channel: the HyperFrames rules, the kit API and habits, the audio levels (SFX bus 12–18 dB under the voice, sync, −14 LUFS, −1.5 dBTP, silence check), the freeze check, chapter length and joins, real-media licensing, the budget and the approval gates.

**Budget: up to 10 USD per long video is pre-approved** (user, 15/11/2026), Shorts included. Spend it on content, not on padding: roughly voice 1–2 USD, new images 3–5 USD (100–150 kie images: scene-specific drawings, props, maps, diagrams, extra host poses and their mouth patches), Gemini/OpenRouter competitor and source analysis up to 1 USD, the rest for data work and re-takes. Keep a running cost line in the chapter README and the final report. Ask before going over 10 USD, and before any subscription or one-off purchase (stock footage etc.). Never print API keys.

## What the human approves

The daily rolling pipeline, the hot-lane 72 h version, the film-level QA table and the upload checklist are in the skill `explainer-flow`; log QA numbers and costs in the video's `channels/<slug>/videos/<video>/STATUS.md`.

Stop and ask at each of these. Do not continue past one on your own.

1. **Script**: the final narration text (normally from `explainer-research`, stage 3).
2. **Voice sample**: the hook takes and chapter 1 audio, before paying for the rest (the whole film is voiced right after G2 in the daily pipeline; a bad sample costs one chapter).
3. **New images**: inside the 10 USD budget no approval is needed; list them and the cost in the report. New host poses also need their face measured (see "Host face" below).
4. **First chapter render**: look and sound. You cannot hear; say so, and ask the human to listen for SFX that feel wrong, too loud, or late.
5. **Final film.**

## Step 1. Voice first

Picture is timed to the voice, never the reverse.

1. Split the script into **chapters of 60–90 s (at most ~1,000 characters)** at paragraph ends. One file per chapter: `vo/<slug>/chNN.txt`.
2. Generate each chapter, passing the neighbours so the tone carries across joins:
   ```
   python3 fal_tts.py vo/<slug>/ch02.txt vo/<slug>/ch02.mp3 <voice> vo/<slug>/ch01.txt vo/<slug>/ch03.txt
   ```
   Arguments 4 and 5 are `previous_text` and `next_text` (use `-` for no previous). Voice = the brand json's `voice` (ElevenLabs via fal). **Direction in the text:** mark one stressed word per sentence and the pauses in `vo_text`; for the hook, voice three takes; the writer picks by `qa_hook` and timing and the operator can swap at G3 or G4 (where fal_tts.py exposes stability and `TTS_SPEED`: hook stability 0.40-0.45 and +5 % speed, body 0.50-0.55, number-heavy lines -5 %). It writes `ch02.fal_ts.json` (character timestamps) next to the audio. One submission per chapter; do not re-run a chapter that already has audio unless the text changed.
3. Post-process, then build the working files for each chapter. First the voice post chain (high-pass 70 Hz, de-esser, 2.5:1 compression, small lift near 4 kHz, short room 6-8 % wet, limiter; word timings do not change), always, before `vo_build.py`: `sh kit/tools/vo_post.sh vo/<slug>/ch02.mp3 vo/<slug>/ch02_p.mp3`. Then build from the processed file:
   ```
   python3 kit/tools/vo_build.py vo/<slug>/ch02_w vo/<slug>/ch02_p.mp3
   ```
   This writes `ch02_w.mp3`, `.words.json`, `.WORDS.txt` (word@second, for you to read) and `.levels.js` (mouth sync). It prints words per minute and every pause over 0.6 s. Pauses are where beats can change.
4. Check: no word missing or doubled against the text, pace inside the style's `script.wpm` (**default** 150–175 wpm), no pause over 1.2 s inside a sentence, and **a pause of 0.4–0.8 s before the peak line and before each re-hook line** (Story card). The pause comes from the text (an ellipsis or a paragraph break before the line; the model takes no SSML breaks); read it in `WORDS.txt`. It is where the hold before the payoff and `K.dip` go (`CRAFT_RULES.md` §15). If a chapter is bad, regenerate that chapter only.

## Step 2. Beat plan

One HyperFrames project per chapter: `film/<slug>/chNN/`. Inside it, 4–8 **beats of 8–20 s**, each made of **2–5 shots** (beat and shot lengths: the style's `visual_system`/`pace` if set, else these defaults). Write the plan as the comment at the top of `index.html` before any markup (for a working example run `./demo.sh` and read `explainer/film/demo/shorts/s1/index.html`; the scaffold is `explainer/shorts/native/template.html`). If the style picks the **script-as-timeline table**, the plan is that table: one row per voice-over line with background / midground / foreground asset.

- First line: the channel slug and three numbers for the chapter: planned full-frame changes per minute, host-visible share, presenter-mode share, each next to the style's target range (see "The host is a tool" below).
- Beat, time range, set (background, the anchor object that stays), transition in.
- Shot list of the beat: start time, framing (wide / close on the object / full-frame insert: map, photo, chart, number, text card / reaction), the host's mode in that shot (none / presenter / actor / corner), what the shot is made of (real photo or footage / proof capture / drawn world / growing diagram / card with words) and its **why** in one clause: what the viewer learns or feels from it. A shot with no why is cut.
- One **hero** shot per chapter, marked in the list: the chapter's biggest picture on its most important sentence. The film's peak (Story card in `SCRIPT.md`) is the hero of its chapter.
- Per sentence: the word that triggers each visual, what appears, what sound it makes.

Rules for the plan. The set, illustration and label rules come from the brief that produced our best film. The numbers for shots, modes, the opening and the ending come from the channel style; the defaults quoted here came from 21 competitor videos across several niches (our competitor study, 15 Nov 2026; table in `kit/CRAFT_RULES.md` §9):

- **Within a beat the set stays put, and the shot changes.** Same background, characters stay where they are and change pose in place, one anchor object persists. Only props, drawings and labels come and go. The client's complaint about the automated version was that every sentence rebuilt the screen with an unrelated layout. Re-framing the same scene is a different thing, and every competitor in both our niches does it every few seconds.
- **Re-frame at the channel's rate.** A shot is one framing of the set: wide, a punch-in on the object the sentence names, a full-frame insert (the diagram, map, photo or number takes the whole frame and the host is gone), a reaction. Targets on the render, measured by `qa_pace.py --channel <slug>`: the style's `pace.shot_changes_per_min` (min, target, max), `median_gap_max_s`, `long_gap_s` and `max_gap_s` (**defaults**: at least 10 per minute, median gap 6 s or less, a framing held over 12 s needs its reason written in the plan, nothing over 20 s). Our first two films changed framing 3.0 and 5.9 times a minute; every competitor measured in either niche is above 9. A long hold is allowed only for one diagram or map that gains a new element at least every 3 s.
  - Punch-in: chain `K.push` segments on the same camera wrapper with different start values, for example `K.push("#cam1", 0, 5.0, 1.0, 1.02, 0, 0, -6, 2); K.push("#cam1", 5.0, 2.6, 1.7, 1.76, 380, 120, 400, 130); K.push("#cam1", 7.6, 2.3, 1.0, 1.02, 0, 0, -6, 2);`. Each segment jumps to its own start on its first frame, which reads as a cut. Segments must not overlap in time. Positive x moves the picture right, so it shows what is left of centre. Keep the scale at 1.8 or less and snapshot just after every cut: a punch-in also enlarges labels and can push the named object out of frame. (Checked with `check` and `snapshot` on a copy of engine ch03, 15/11/2026.)
  - Full-frame insert: a full-size layer above the set, switched on with `tl.set(insert, { opacity: 1 }, t)` and off again the same way. Set the set's own wrapper to opacity 0 for that stretch, so nothing readable sits hidden under the insert. Entrances go on the insert's children, not on the layer.
  - Cut on the trigger word or 0.12 s before it. A plain cut gets no sound of its own.
- **Change mode at the style's `mode_change_s`** (**default** every 30–45 s). A mode is what kind of picture it is: characters in a scene, a diagram, a map, a real photo or footage, a document or screen, a big number, a full-screen text card of 5 words or fewer on a turn line, a chapter card, a metaphor cutaway. Which modes the channel leans on, and in what shares, is its `media_mix`; how many text cards a chapter may have is its `typography` (**default** at most one). More than 30 s of host-plus-diagram is the look the client rejected, in every channel. Do not use the same interrupt twice running.
- **Change set only between beats**, with a whip-pan, wipe or zoom-through that starts 0.12 s before the beat's first word. Each seam enters the next set through something already on screen; three to five kinds in a film (recipes and eases: `CRAFT_RULES.md` §15).
- **Choose what the shot is made of before its layout** (`kit/VISUAL_SOURCES.md`): the real thing → the thing drawn as a world the camera moves through → a diagram that grows part by part → a card with words. A card with words is a proof insert of 2–3 s with one marked phrase of 8 words or fewer; **at most 1 shot in 4 of a chapter, never two in a row**. A grey mock screen where the real page or a drawn scene could be is not a shot.
- **The hero of every shot fills at least 40 % of the frame's height or width**, and a film uses at least three grounds, not one from first frame to last (`CRAFT_RULES.md` §15–16 lists the tells to plan around).
- **Illustrate the exact sentence.** "A few cents per chip" is a chip with one small coin dropping on it. "A toll booth on the mobile industry" is a toll booth with phones queuing through. Never a generic icon.
- **Wrong-context check for library art.** Every reused image from `film/assets/img/` must match the sentence's real object; `film/assets/img/MANIFEST.json` lists where each set and prop may be used. An image showing another place, plane, brand or era than the sentence names is redrawn or replaced, never reused. The picture review (Step 4, item 8) catches what slips through.
- **Draw it when you can**: SVG that builds itself line by line (a building, a circuit on a blueprint, an arrow joining two named things, a red X over the exact object being negated).
- A new visual idea every 1–4 s. No empty or frozen picture longer than 1 s. (This is about props and drawings. It does not replace the shot rule: our films already had 23–28 small events a minute and still looked static.)
- **Every chapter opens on a new picture in its first second**: an establishing shot of the place or object the chapter is about, a date or place card, or the object full frame. Never the host standing where the last chapter left him.
- **Chapter 1, hook (checked by `qa_hook.py`).** Frame 0 is the thumbnail's object, full frame, moving within 0.5 s; no logo, title card, host or channel name. Sentence 1 has 15 words or fewer, names the title's entity and ends by the style's `hook.first_sentence_by_s`. A sentence with two or more content words of the title is spoken by `hook.promise_by_s` (default 20 s); one stakes line of 20 words or fewer by 30 s; the story starts by `hook.story_by_s`. At least 8 full-frame changes in the first 30 s, the first by 3 s, none held over 5 s. None of welcome, "in this video", subscribe, sponsor, the channel's or host's name in the first 60 s. Run `python3 kit/tools/qa_hook.py out/ch01_raw.mp4 vo/<slug>/ch01_w.words.json --title "<title>" --channel <slug>` before G3 (exit 1 blocks it); with `--script SCRIPT.md` it checks the script before any voice is paid for. When it passes and the voice did not change, G3 is skipped (see `explainer-flow`).
- **Last chapter: the end-screen plate.** The final seconds set by the style's `ending` (**default** 8–12 s; YouTube allows end screens on the last 5–20 s) are one designed shot: the part of the frame the style names stays clear of art and text for the next-video box and the subscribe button, the host (or the channel's recurring device, if the style keeps the host out) sits in the rest and points at it, and the voice pitches that one video (the script supplies the line). Keep breathing and float running to the last frame; place the end-screen elements over the clear half in Studio at upload. The film ends at the last word + 2 s at most, so the pitch itself has to last 8 s or more.
- Labels follow the style's `typography` (**default** at most 2 visible, 2–4 words each). Never the same text twice on screen, nothing important hidden behind something else, no text that wraps or overflows (universal).
- **Named real entities get their real media** (how many per chapter and in which frame, prop or full frame: the style's `real_media` and `visual_system`): a company appears as its real logo (`K.sticker`), an aircraft, airport or place as a real photo (`K.photo`), a historic moment as archival footage on a TV prop (`K.tv`). Text name-cards are only a secondary caption next to the real thing. Still no real people's faces unless the brief clears it.
- Real media comes only from `assets/media/` with a row in its `CREDITS.json` (see "Real media" below). Everything else uses images in `film/assets/img/`, is drawn with SVG/HTML/CSS, or goes on the new-images list for approval.

## Step 3. Direct each beat

Set up the chapter folder:

```
film/<slug>/chNN/
  index.html
  kit/            copy of explainer/kit/kit.js, kit.css and sfx/ (plus sfx_v2/ if you built one)
  assets/img/     the images this chapter uses
  assets/vo/      chNN_w.mp3
  levels.js       chNN_w.levels.js renamed
  hyperframes.json, package.json   copy from shorts/native/
```

After any change to `explainer/kit/`, copy it into the project again.

### HyperFrames rules (the render breaks or goes silent if you ignore these)

- Root: `<div id="root" data-composition-id="main" data-start="0" data-duration="<seconds>" data-width="1920" data-height="1080">`. **Chapter length = last word's end + 0.6 s** (the last chapter of the film may hold longer). Do not hold the final frame for seconds: in the joined film every extra second of tail is dead air between chapters (first film: 1.5–3.2 s silences at every join, the client heard the voice "stall"). Land the chapter's last visual event before the last word ends.
- Voice: `<audio id="vo" class="clip" data-start="0" data-duration="<len>" data-volume="1" src="assets/vo/chNN_w.mp3">`.
- Each beat is a `<div class="scene clip" data-start data-duration>`; paint order by CSS `z-index`. Inside it, a shake wrapper, then the camera wrapper, then everything else (`#shk > #cam > …` in the demo).
- One paused timeline: `const tl = gsap.timeline({ paused: true })`, every tween at an absolute second, then `window.__timelines["main"] = tl; tl.seek(0);`.
- No `Math.random`, no `Date.now`, no `repeat: -1`, no network fetch except the GSAP CDN script. `K.rng(seed)` if you need variation.
- Scripts load in this order: GSAP, `kit/sfx/index.js` (or `kit/sfx_v2/index.js` + `palette.js` for edit mode), `levels.js`, `kit/kit.js`, then your inline script.
- **Keep this exact comment directly above `K.finish()`**, in the inline script:
  `// REQUIRED MARKER: K.finish() inserts the SFX with document.createElement("audio").`
  HyperFrames 0.9.46 only picks up script-inserted audio when an inline script contains that text. Without it the film renders with voice only and no error.
- Keep `kit.js` as an external file. Pasting it inline breaks the render: the compiler parses the SVG markup strings inside it as page HTML. In your own inline script, build elements with `document.createElement`, not long markup strings.

### Working with the kit

```js
const K = Kit.create(tl, { root: "#root", words: WORDS, levels: window.KIT_LEVELS, sfxBase: "kit/", fx: "#cam", sound: "edit", channel: "<slug>" });
```

`WORDS` is the chapter's `words.json` pasted into the script (no fetch).

**Sound (kit v2 `sound: "edit"` is the default for every film).** `Kit.create(tl, { ..., sound: "edit", channel: "<slug>" })` loads kit/sfx_v2 (`<script src="kit/sfx_v2/index.js">` + `palette.js`; copy `kit/sfx_v2/std/` into the film). Sound follows the edit: hierarchy transition > reveal > key word > nothing. Only these sound by themselves: `whip/wipe/zoomThrough` (whoosh peaking on the cut), `stamp/drop/cross` (impact), `counter` (soft riser + one boom on the final number, no ticks). pop, label, draw, circle, underline, poseSwap, sticker, photo, sparkle, puff are silent unless you pass `{ sfx: "role" }` (roles: whoosh_s/m/l, riser, subhit, boom, impact, impact_soft, paper, ui_tick, glitch, stinger, chime, engine, gear, radio). Rules enforced in `K.finish()`: 1 accent per sentence besides transitions, no two cues within 0.25 s (except whoosh/riser into a hit, `layer: true`), `force: true` wins. Extras: `K.cut(t)` (hard cut), `K.dip(t, dur)` (bed near-silent, hit at t+dur), `K.beatGrid(bpm, offset)`. Target 15-25 cues/min. Check: `node kit/tools/kit_cues.mjs <film dir> out/kit_cues.json` (anchored % >= 80), then `qa_audio.py ... out/kit_cues.json`; bed: `DIPS=... kit/tools/mix_bed.sh`. The music bed is continuous at 20-26 LU under the voice; `mix_bed.sh` refuses a bed without `approved` in `style.json -> sound.music_beds`. Never use `sound: "legacy"` or `sfxGain` on a new film. **Hook (chapter 1, first ~10 s): add 3–4 explicit accents by hand** (`{ sfx: "role", force: true }` on the hook's reveals), because a hook often has no kit transition and edit mode alone leaves it near-silent (edit-mode test, 17/11/2026).

| Need | Call |
|---|---|
| Thing appears | `K.pop(sel, t, { stagger, maxSfx })` |
| Thing falls in and lands | `K.drop(sel, t, { sfx: "thud_metal" })`: lands at `t + 0.3`, squash, dust, thud |
| Stamp / slam / name reveal | `K.stamp(sel, t, { shake: "#shk" })`: lands at `t + 0.1`, rays, shake |
| Red X over a thing | `K.cross(svgSel, t, { shake: sel })` |
| Drawing draws itself | `K.draw(svgSel, t, { each, gap })`: pencil sound sized to the drawing |
| Circle / underline something | `K.circle(sel, t, { until })`, `K.underline(sel, t)` |
| Coin or object flies A→B | `K.fly(sel, t, dx, dy, { sfx })`: sound on arrival; pair with `K.squash(target, tArrive)` |
| Number counts up | `K.counter(sel, t, { from, to, dur, prefix })` |
| Label | `K.label(sel, t)`; exits `K.out`, `K.popOut` |
| Aftermath | `K.wobble`, `K.shake`, `K.squash`, `K.puff(x, y, t)`, `K.rays(x, y, t)`, `K.sparkle(x, y, t)` |
| Idle life | `K.float(wrapper, t0, t1)`, `K.push("#cam", t0, dur, fromScale, toScale, x0, y0, x1, y1)` |
| Beat change | `K.whip(inSel, outSel, t)`, `K.wipe(inSel, t)`, `K.zoomThrough(inSel, outSel, t)` |
| Extra sound | `K.sfx("riser_air", t, { db: -2 })`; any helper takes `sfx: false` or `sfx: "name"` |
| Host | `const host = K.host("#host", { poses, faces, start, offsets })` then `host.talk(t0, t1)`, `.blinks(t0, t1, { seed, at })`, `.breathe(t0, t1)`, `.pose(name, t)`, `.nod(t)`, `.hop(t)` |

Habits that prevent most bugs:

- **One helper per property per element.** Idle motion (`float`, `breathe`) goes on a wrapper, entrances on the child. Shake the `#shk` wrapper, never `#cam` (the push owns it).
- Give `t` as the moment the viewer should perceive the event: `drop` and `stamp` take their start time, so subtract the fall (0.3 s / 0.1 s) to land on the word.
- Space repeated `K.squash` on one element at least 0.27 s apart.
- For a row of things, let only the first 2–3 make a sound (`maxSfx`, or `sfx` on some items only).
- **The host is a tool, not a fixture.** Decide per shot whether he is on screen, the way a film editor cuts between presenter and B-roll. Typical use: the hook's question line, questions to the viewer, reactions, the core-truth line and the end; mechanisms, numbers, maps, timelines and real photos go **full frame with voice-over only**. How much he is on screen is the channel's choice, set from its competitors: the style's `host.visible_share` for the film (**default** 40–60 %, plan the lower half), `host.presenter_share_max` and `host.presenter_max_s`, `host.chapter_max_share`, and which of the modes below the channel uses (`host.modes`). Both our first films had him in 40 of 40 sampled frames (our competitor study, 15 Nov 2026; table in `kit/CRAFT_RULES.md` §9); no channel style allows that. He stays because he is the channel's own character (YouTube's monetization policy names "a unique character and narrative you invented" as an allowed use of AI), so each appearance has to do a job. Three modes; write the mode in the shot list:
  - **Presenter**: talks to the viewer, bust or full figure. The hook's question, a direct question, the core truth, the sign-off. Limits from the style (**default** at most a quarter of the film and 12 s at a time).
  - **Actor**: inside the scene, doing the thing the sentence says (presses the button, carries the engine, follows the footprints). The default when he is on screen during a mechanism. Use the action poses that exist; a new one goes on the new-images list with its mouth patches.
  - **Corner reactor**: small (a fifth of the frame height or less), at an edge, over a full-frame diagram or map; reacts with a pose change, a nod or a shrug.
  Never a fixed spot for a whole chapter, never in frame 0 of the film. Vary his framing too: full figure, waist-up close-up, small in a corner, peeking in from the edge, or gone. Chapter joins do not require the same host position; a cut to a full-frame picture is a clean join. A single chapter may run from 0 up to the style's `host.chapter_max_share` (**default** 70 %); the visible-share range is for the film.
- While he *is* on screen: call `talk`, `blinks` and `breathe` for his whole on-screen range, `nod` on 1–2 key words per sentence, change pose on a verb about every 3–6 s. When he leaves, cut or slide him out on a pause, never mid-word.
- Sound follows the edit (table above). Title and label changes, camera moves and blinks get no sound.

### Real media (logos, photos, archival footage)

**Use a lot of it.** Real pictures and data make the film specific and visibly hand-researched. How many and in what form is the channel's `real_media` (**default** 25–60 real items per long video: photos, logos, maps, document/headline screenshots, footage clips, real data charts, at least one in every chapter). The tiers, credits and licence rules below are universal. Source tiers (user decision 15/11/2026, YouTube Content ID and the reused-content policy in mind):

| Tier | Sources | Use |
|---|---|---|
| A, free | Wikimedia Commons, Wikidata, Internet Archive PD/CC, **US government** works (NASA, FAA, NTSB, DoD/DVIDS, CISA, FBI, NOAA, Library of Congress), Flickr CC (via Commons or the Flickr licence field), CC-BY YouTube videos (download only with licence check), Pexels/Pixabay video and photo (free API keys), Mixkit video (free, no key), NASA Image and Video Library (images.nasa.gov API, no key), DVIDS (US military photos/video, free API key), ESA (mostly CC BY-SA 3.0 IGO, check each), European Commission Audiovisual Service (free with credit), Natural Earth / OpenStreetMap (map data, ODbL credit), Our World in Data, government and agency datasets | Freely, with the credit the licence asks for |
| B, editorial | Company/agency press kits and media rooms (court filings, official reports and PDFs) | Yes, credited, when the terms allow editorial use; save the terms URL in CREDITS |
| C, news as evidence | Screenshots of a news **headline or paragraph** (outlet name visible), a tweet/post by an official account, a page of an official document | Yes, short on screen (≤ 4 s), framed as a card/paper prop with our own commentary over it, outlet named. Never a full article or the outlet's photo enlarged |
| B+, licensed stock | Storyblocks (subscription approved in principle 15/11/2026; API key pending — the user adds it to `.env`) | When the key exists: any clip under the subscription licence; log the clip ID in CREDITS |
| D, news photos and broadcast video | AP, Reuters, AFP, Getty, TV channels, other YouTubers' footage | **No.** Content ID claims and strikes hit monetized channels even for a few seconds. Use a tier A/B equivalent, a licensed stock clip (ask first), or draw the scene |

Every item goes into `CREDITS.json` (source URL, author, licence or terms, tier). Tier C items need no licence but their outlet and date go in the description sources. Real people's faces: only public officials/executives in their official role from tier A/B photos, never private individuals or victims.

Fetch with `explainer/kit/tools/fetch_media.py` (system `python3`, free, no key) into the chapter's `assets/media/`:

- `logo "Delta Air Lines" assets/media` — official logo via Wikidata P154 (current logo, the one without an end date), falls back to the logo files on the Wikipedia article. SVG is rendered to a transparent PNG.
- `image "Tesla Model 3" assets/media` — the entity's main Wikidata photo (P18). `commons "Tesla Model 3" assets/media --n 5` for more choices.
- `pexels "<query>" assets/media --n 3 [--video]` and `pixabay "<query>" assets/media --n 3 [--video]` — free stock photos and HD video (keys `PEXELS_API_KEY`, `PIXABAY_API_KEY` in the project `.env`, already set 15/11/2026). Good for generic B-roll (airports, cockpits, server rooms, offices, city streets); never use it to fake a specific real event. Cut footage with `clip` like archive files.
- `archive "<query>" assets/media --n 1 --video` — Internet Archive, public-domain/CC only (Prelinger, NASA, gov). Then cut what you need: `clip IN.mp4 START DUR OUT.mp4` (silent, 960 px, 30 fps). Scan the film first with an ffmpeg tile sheet with timestamps; never guess the moment.
- Every fetch appends `CREDITS.json`/`CREDITS.md` and rebuilds `contact_sheet.png`. Open the contact sheet and pick visually (right entity, current logo, right model and colours).

License rule: the `free` column must be true. Files without a clear free license (non-free / fair-use logos that only live on en.wikipedia) land in `assets/media/nonfree/` flagged `non-free (fair use)`: do not use them unless the human approves. Logos are trademarks even when the file is public domain: show them for identification and commentary, never as endorsement or as our own branding. On thumbnails a real logo is allowed (user decision 15/11/2026) to identify the video's subject, unaltered.

### Footage (real moving clips)

**Footage target** (`real_media.footage_share`; the `media_mix` check in `qa_film.py` sums `<video>` time and real items per chapter): default 5-15 % of runtime, at least 1 clip in every chapter, 3-7 s each, never 2 consecutive footage beats. Investigation-style niches also need many real items per film, some of them real public-domain document pages (screenshot and highlight the real official page; redraw only what is not public domain). Event-specific footage rarely exists: use clips as era or atmosphere B-roll, captioned "archive"/"stock", never as proof of a specific moment.
- **Sources, safest first:** US-gov items on Commons (FBI, NASA, White House) and `nasa-video` > Prelinger / `usgovfilms` / FedFlix via `archive --vetted` > Commons CC0/CC BY (credit) > Pexels/Pixabay generic B-roll > DVIDS (stub until `DVIDS_API_KEY`). Corporate PD-claimed films (e.g. a Pan Am promo) get `risk: check` and a Content ID note: keep them under 12 s, silent.
- **Commands** (`fetch_media.py`): `commons-video "q" DIR --n 3`, `nasa-video`, `archive "q" DIR --video --vetted [--hd]`, `pexels|pixabay "q" DIR --video`, then `scan IN.mp4 sheet.png --every 6` (look before cutting), `clip IN START DUR OUT [--width 960|1280] [--look duotone|halftone --palette <slug>]`, or `treat IN OUT --palette … --look …` (silent, 30 fps, channel ink/paper colours).
- **In the film:** on a prop (`K.tv` TV, `K.screen` with `.kit-phone` or `.kit-crt`), split with the host (prop one side, host the other), or full frame only after duotone/halftone. Raw colour footage never sits full-bleed. Demo: `kit_media_demo/footage_demo/`. A `<video data-start>` must not sit inside an element that also has `data-start` (`video_nested_in_timed_element`): use an untimed `.scene` wrapper and fade it with GSAP opacity.
- **Traps:** Internet Archive licence tags are uploader-set (Britannica, Periscope Film reels are not safe); C-SPAN copies are CC BY-NC-SA, not monetizable; Commons "public domain" on TV-news or promo clips is doubtful (the tool sends those to `review/`); PD films that also sit on YouTube can still draw Content ID.
- **Never** use news or broadcast footage, or company press video, without written permission saved in CREDITS..

In the composition:
- Logo: `<div class="kit-sticker" id="lg"><img src="assets/media/logo_x.png"></div>` + `K.sticker("#lg", t, { rot })` (white die-cut border, slap-on pop, sparkle). Add class `plate` for logos that need a white card behind them (thin or dark wordmarks).
- Photo: `<figure class="kit-photo">` with two `<span class="kit-tape l|r">`, the `<img>`, a `<figcaption>` and `<small class="kit-credit" data-layout-ignore>Photo: Author / CC BY-SA 4.0</small>` + `K.photo(sel, t, { rot })` (drops, lands, tape slaps on, paper sound, dust).
- Footage: `<div class="kit-tv"><video class="clip" data-start data-duration muted src></video><small class="kit-credit" data-layout-ignore>…</small></div>` + `K.tv(sel, t)`. **A `<video>` with `data-start` must not sit inside an element that also has `data-start`** (check error `video_nested_in_timed_element`; the frames come out wrong). For a beat with footage, make that beat's scene wrapper an untimed `<div class="scene">` and show/hide it with GSAP opacity, or render that beat as its own chapter.
- CC BY / CC BY-SA photos keep the small on-screen credit; the full list goes in the description: run `fetch_media.py used assets/media index.html` and paste `CREDITS_USED.md` into the video description (merge all chapters).

### Host face

Painted mouth patches (B, A, O, E) and a closed-eyes patch come from your host's face table (`window.KIT_FACES`, see the comment above `FACES` in `kit.js`; measure with `kit/tools/face_grid.py`, paint with `kit/tools/mouth_patches.py`; images in the composition's `assets/img/mouth/`, override the folder with `K.host(..., { mouthDir })`). Copy the channel's mouth-patch folder (made once with `kit/tools/mouth_patches.py` and kept with its brand images) into each new composition. To make another pose talk (≈ 0.15 USD, ~2 min):

1. `python3 kit/tools/face_grid.py <pose>.webp /tmp/grid.png`: read mouth centre and width and each eye's centre and radii in native webp pixels.
2. Write 5 kie jobs (copy `explainer/jobs/mouth/neutral_*.json`): model `gpt-image-2-image-to-image`, `input_urls` = the pose's original kie result URL (from `explainer/state/<name>.json`; if expired, re-upload the raw PNG), prompt "keep everything identical, only change the mouth to …" for B/A/O/E and "only close both eyes" for blink. Run with `python3 kie.py run jobs/mouth/<pose>_*.json`.
3. `python3 kit/tools/mouth_patches.py <face_key> <raw.png> <pose.webp> <comp>/assets/img/mouth <mx> <my> <mw> '[[ex,ey,rx,ry],[...]]' B=.. A=.. O=.. E=.. blink=..` (system python3, needs OpenCV). It prints the `patches` rectangles: paste them into the pose's `FACES` entry.
4. Open `<face_key>_check.png` (base and every patch composited, 2× head crop). Reject a shape if it has a seam, a second lip line, a green fringe or a changed head; regenerate only that job.
5. Render a short stretch and pull a 10 fps face-crop sheet from the MP4; show the human one before using the pose in a film.

Poses without patches fall back to the drawn SVG mouth (looks like a sticker on these painted faces: avoid for long lines). Poses with no `FACES` entry get no mouth or blink; use those for short reactions only.

## Step 4. QA loop (per chapter, repeat until clean)

Run from the chapter folder. Look at every image the tools produce; a passing command is not a passing film.

1. `npx -y hyperframes@0.9.46 check`: must end "Check passed" with 0 errors. The `nested_structure_needs_subcomposition` warning is expected. Fix every layout, overflow and `line_unread` finding.
2. `npx -y hyperframes@0.9.46 snapshot --at <8–15 times> --no-end`: pick moments just after each event, open the contact sheets, and fix anything ugly, overlapping, empty, clipped, or not matching the words. Then zoom on the host: `--zoom x,y,w,h --zoom-scale 1` at a few talking and blinking times. **At least two snapshot-and-fix rounds.**
3. `npx -y hyperframes@0.9.46 render -o out/chNN_raw.mp4`. In the log, `"audioCount"` must rise from 1 to 1 + your cue count. If it stays at 1, the marker comment is missing.
4. `python3 ../../../kit/tools/qa_audio.py out/chNN_raw.mp4 assets/vo/chNN_w.mp3`. Targets:
   - SFX bus **12–18 dB under the voice**. Around 34 dB under means no SFX reached the mix.
   - Loudest SFX frame below the loudest voice frame.
   - Hits per minute inside the style's `sound.sfx_hits_per_min` (**default** 15-25 in the body). The two lines above are universal.
   - If the style has a music bed (`sound.music`), check it sits at the style's level under the voice and never masks a word; otherwise there is none.
5. `sh ../../../kit/tools/qa_freeze.sh out/chNN_raw.mp4 1.0` must list no freeze. Any line is a dead second: add motion there.
6. `python3 ../../../kit/tools/qa_pace.py out/chNN_raw.mp4 --channel <slug>`. It prints the channel's targets from `style.json` (or says it fell back to the defaults: at least 10 per minute, chapter 1 at least 14 in the first 60 s, median gap 6 s or less, gaps over 12 s need a reason, none over 20 s). Every printed long gap matches a reason in the plan. If it reads LOW, add shots (punch-ins, full-frame inserts); do not add props. If it reads HIGH, the chapter is busier than the channel's style: merge shots or hold a build longer.
7. Pull a contact sheet from the rendered MP4 (ffmpeg, 2 frames per second) and compare against the plan: every sentence has its picture, on its word. On the same sheet count the frames with the host and the frames where he presents, and the frames of each picture type: the shares must match the plan's first line and sit inside the style's `host` and `media_mix` ranges.

8. **Picture review** (`kit/REVIEW_PASS.md`; about 5 s of tool time per chapter). `python3 ../../../kit/tools/qa_review.py out/chNN_raw.mp4 --words ../../../vo/<slug>/chNN_w.words.json`, open the phone sheet, write the stranger sentences, then the notes as `t · where · problem → exact change · what stays`, ranked P0/P1/P2. Fix every P0 and every `unanswered` sentence; two passes at most. Chapter 1 and the joined film also get the fresh-eyes agent with the fixed brief (REVIEW_PASS §5). Append the chapter's notes to `film/<slug>/REVIEW.md`. Passing items 1–7 with a P0 open is not a passing chapter.

Report honestly what you could not check: you did not listen, so sound character, masking and comic timing are unverified until the human hears it.

## Thumbnails (per video, made with the chapters; 2 agent hours and 0.50 USD)

1. **Reference sheet (free).** `yt-dlp --skip-download --write-thumbnail "ytsearch8:<query>"` plus `channels/<slug>/research/scan/*/thumbs.jpg`. For each reference record object, conflict, words and colour field; work from that table, not the image.
2. **Six concepts from three families**: the object damaged or in conflict; a number that looks wrong on the object; a versus split. The operator strikes three at G1.
3. **Art.** The hero object is a real photo cut-out (public domain or CC BY, credited) in the channel treatment: the brand's `thumb_look` (`outline`: ink outline on a light ground; `halftone`: halftone with an accent edge on a dark ground). A kie drawing only when no photo works. No faces on objects; the object fills half the frame and crosses an edge. Real logos only as `packaging.real_logo_ok` allows.
4. **Layout rules, checked by `thumb_sheet.py`.** At most 3 words, all known to a 12-year-old (no acronyms or jargon); cap height 110 px or more at 1280x720; text on a solid plate at 7:1 contrast; one accent colour; nothing in the bottom-right 180x90 px.
5. **160 px test.** `python3 kit/tools/thumb_sheet.py` (see its `--help`) places our three among six competitors in random order at 160 and 320 px. Tesseract must read our words at 320 px. A fresh agent with no context names the three it would click and what each is about; one of ours must be chosen and described correctly. The operator picks at G4.
6. **A/B.** Three concept-different variants go into Test & Compare at publish; read at 48 h by the data loop in `explainer-flow`.

## Step 5. Assemble and master

1. Chapters are rendered separately. **Join the `chNN_raw.mp4` renders, trimmed**: cut each chapter (video and audio) at its last word's end + 0.6 s (read the end from `vo/<slug>/chNN_w.words.json`), with a 0.15 s audio fade-out at the cut so a ringing SFX does not click. The gap between the last word of one chapter and the first word of the next must be **0.5–0.8 s** (same as a paragraph pause inside a chapter; up to ~1.0 s before the outro). Use ffmpeg `trim`/`atrim` + `concat` filters (re-encode, crf 16); the first film's working script is `explainer/film/<slug>/final/work/join_cmd_v2.sh` (+ `trim_v2.json`) — copy it. If a chapter's next-chapter continuity depends on its exact last frame (an outro that opens on the previous chapter's final picture), check that frame still matches after the trim.
2. Master once on the joined file: `TP=-2.0 sh kit/tools/master.sh joined.mkv final.mp4` → **−14 LUFS**, true peak ≤ −1.5 dBTP after AAC encode (the plain −1.5 setting measured −0.9 to −1.1 after encoding). Video untouched.
   - **Snap every trim point up to a whole frame** (`ceil(t*30)/30`) and use the same value for `trim` and `atrim`. Otherwise video rounds up per chapter while audio does not, and lip sync drifts (~0.18 s by the end of a 12-chapter film).
   - If the joined mix sits well under −14 LUFS with peaks near −1 dBTP, loudnorm cannot stay linear and its dynamic limiter overshoots (seen once: −1.1 and 0.0 dBTP). Pre-gain and true-peak limit first: `volume=<gain>dB,aresample=192000,alimiter=limit=0.63:level=false,aresample=48000`, then master (see `film/<slug>/final/work/master_cmd.sh`).
   - Decode the master and check the largest sample: the native AAC encoder at 192k can insert a single near-0 dBFS click. If it does, re-run with `AB=256k`.
   - If TP −2.0 still measures above −1.5 after encode (seen once: −0.9 at one spot), master again at `TP=-2.3`. Do not accept the overshoot.
3. Final checks: duration equals the sum of the trimmed chapters, `ffprobe` shows 1920×1080 at 30 fps with AAC audio, freeze check on the whole film, `qa_pace.py final.mp4 --channel <slug>` (the style's film-level pace and first-60-s targets), host-visible and presenter shares of the whole film inside the style's `host` ranges (**default** 40–60 %, presenter a quarter or less), and **a silence check on the whole film**: `ffmpeg -i final.mp4 -af silencedetect=noise=-45dB:d=0.9 -f null -` must list nothing except the end-screen tail (and any deliberate dramatic pause you can name). Also pull frames at each join (0.4 s before, 0.05 s before, 0.1 s after) and look for a cut-off animation or a jarring host jump.
4. Credits: merge every chapter's `assets/media/CREDITS_USED.md` (from `fetch_media.py used`); it must list no non-free file the human did not approve. **Description = short credits, no URLs**: one line per CC photo `- Author (licence)`, one line "Logos: public-domain files from Wikimedia Commons.", the sound line (`slide_whistle_down` is CC BY 3.0, the rest CC0). Public-domain logos need no per-file credit. Image source URLs stay in the local `CREDITS.json` only.
5. **Pinned comment = one question, no links** (user, 17/11/2026; replaces the 15/11 source list): one line that invites a real answer or a side-pick, e.g. "Was <product> a mistake, or just early?". The description names 2–3 primary documents without links. Full sources stay in `final/sources_full.txt`. Each channel's `STYLE.md` §11a has the upload template.
6. Deliver the MP4, the per-chapter QA numbers (SFX-under-voice dB, hits per minute, loudness, full-frame changes per minute, host-visible and presenter shares) next to the channel style's targets, any key where a default was used, and the list of what was not verified.

## Quality bar: a chapter is not done until every line is true

- [ ] The plan names the channel, and its first line gives full-frame changes per minute, host-visible share and presenter share next to the style's ranges; the render matches it.
- [ ] `qa_pace.py --channel <slug>`: inside the style's pace range (chapter 1: its first-60-s target), median gap and long gaps within the style's limits, every long gap has its reason in the plan.
- [ ] The host stays inside the style's chapter ceiling and presenter limits, and does not keep one spot and size for more than two beats running.
- [ ] The mode changes within the style's `mode_change_s`, and the plan names each change; the picture types follow its `media_mix`.
- [ ] The chapter opens on a new picture. Chapter 1 opens on the thumbnail's object with no logo, title card or host in the first sentence.
- [ ] Every sentence has its own picture on its word; named real entities appear as real media.
- [ ] The plan gives every shot its why and marks one hero shot; at most 1 shot in 4 is a card with words and no two are in a row; every hero fills 40 % of the frame.
- [ ] The picture review ran on the render: no P0 open, `unanswered` empty or explained, notes in `REVIEW.md`.
- [ ] `check` passed; SFX bus 12–18 dB under the voice; hits per minute inside the style's range; no freeze over 1 s; chapter length = last word + 0.6 s.
- [ ] Last chapter only: the style's end-screen plate (length and clear area) with the voice pitching one named video.
- [ ] You have listed what you could not check (you cannot listen).

### G4 film review: what slipped through chapter QA (17/11/2026; check these on every film)
- **A film of cards on one ground (18/11/2026).** Two films passed every QA script while 11 of the first 24 frames were a text card on the same dark ground, some heroes filled under a tenth of the frame and no source line could be read at phone width. Run `python3 kit/tools/qa_review.py final/final.mp4 --srt final/film.srt` on the joined film and give its sheets to the fresh-eyes agent (`REVIEW_PASS.md` §5); its answer to "do the first three tiles show the promise?" goes in the G4 report.
- **One-frame black flashes at scene changes.** A template bug spread the same flash to 5 chapters of one film. Scan with `ffmpeg -vf blackdetect=d=0.03:pix_th=0.10` on the final film; any hit that is not a deliberate fade gets fixed at the source template, then every chapter built from it is re-rendered.
- **The photo does not match its label.** A stock "hotel lobby" carried an OMNI sign under an "EXCALIBUR" label. Look at every real photo at full size against its caption. When signage names another brand, use a drawn prop instead.
- **The end plate freezes.** `qa_freeze` on the last chapter catches 1.5 s holds. Keep `breathe`/`float` running to the last frame.
- **SRT text vs spoken words.** Grep the SRT for numbers and articles ("about a $100 million"), names and spelled-out numbers.
- **Wrong-context art.** A reused set or prop shows another place, object or brand than the sentence. Compare the contact sheet and SRT against `MANIFEST.json`.
- **Host share is falling.** One film ended at 11 % against a 25 % plan, because workers drop the host on card-heavy beats. Count it per chapter at G3/QA, not only at G4; `K.host` logs its on-screen ranges to `window.__host`, read by `kit_cues.mjs`.

### Upgrading an existing composition

Keep its scenes and timing. First run `qa_pace.py --channel <slug>` on its render: LOW against the channel's style means the upgrade starts with a shot list (punch-ins and full-frame inserts on the existing sets, host removed from the shots where he only stands), before any sound work. Then add, in this order: the kit scripts and `Kit.create`; `K.host` in place of the stacked pose images, with `talk`, `blinks`, `breathe`; a sound for each existing event by swapping its tween for the matching helper or adding `K.sfx` at the event time; one secondary effect per impact; then run the full QA loop.
