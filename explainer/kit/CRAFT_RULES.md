# Craft rules for the cartoon explainer

What to add to our hand-directed films so they keep their look and gain the small-detail craft the client missed: sound on events, secondary motion, a host who talks. Ranked by how much each changes what a viewer perceives.

Every number has a source tag:

- **[b5]** measured in the stickman film's project files (`sound_cues.json`, `mix.py`, `renderer.cjs`, `stage.cjs`), the film the client said had better sound, effects and mouth.
- **[ours]** read from `hand_opus/index.html`, our best-looking film.
- **[demo]** measured on a demo film built with this kit.
- **[ref]** seen in a reference video and confirmed by measurement.
- **[std]** standard animation practice, not measured here.
- **[meas]** measured on 15/11/2026 on 21 competitor videos and two test films with `tools/qa_pace.py`, YouTube captions and contact sheets.
- **[hf]** read in the HyperFrames skill references (`motion.md`, `story.md`, `spec.md`, `review.md`) on 18/11/2026: the renderer authors' rules, not measured on our films. Each is an experiment until our own data agrees (`research_flow/REFERENCE_REPOS.md`).
- **[sheet]** seen on our own films' review sheets, 18/11/2026 (`REVIEW_PASS.md`).

**Universal or per channel.** Sections 2–8, 11, 12 (mouth, blinks, idle life, no dead second, entrance recipes, consequences, stagger, exact-sentence illustration, real media), the sync and loudness rules of section 1 and the HyperFrames mechanics of section 9 hold for every channel. Sections 15 and 16 (seams, hero shots, tells) hold for every channel too. The numbers marked **(default)** — SFX density, music, shot rate, beat and mode rhythm, text cards, host shares, the opening and the end plate — are only the defaults: each channel's `explainer/channels/<slug>/style.json` sets its own from its competitors (skill `explainer-channel-style`; schema and defaults in `explainer/channels/README.md`).

Gemini's sound tables were not used: of 133 claims checked, 33 were wrong and 13 only partly right, including whole invented SFX tracks for two videos that have none.

---

## 1. Put a sound on every meaningful visual event

Our best film had zero sound effects [ours]. The stickman film has 73 in 64.5 s [b5]. This is the largest single gap.

### Sound follows the edit (kit v2, default; supersedes the density table below for new films)

Hierarchy: **transition > reveal > key word > nothing.** A cut gets a whoosh (0.5-1.5 s, peak on the cut); a stamp, drop, cross or final number gets an impact or boom (counter: soft riser + one hit, no ticks); a key word may get one accent; everything else is silent. Pops, labels, scribbles, pose swaps and counter ticks do not sound. Max 1 accent per sentence besides transitions; no two cues within 0.25 s except whoosh/riser into a hit. Body 15-25 cues/min, hook up to 35. At least 80 % of cues within 0.15 s of a scene change, reveal helper or stressed word (`kit/tools/kit_cues.mjs` + `qa_audio.py`). A continuous bed (-30 LUFS un-ducked, ducked about 5-7 dB under speech) and a 0.5-1 s `K.dip` before the key number. `Kit.create(..., { sound: "edit", channel })`; `sound: "legacy"` and the table below apply to old films only.

### Density

| Where | Hits per minute | Source |
|---|---|---|
| Body of the film | 15–45 depending on niche **(measured on competitors + A/B test; channel style.json wins)** | old default 60–75 retired: the user rated it bad |
| Hook (first 10–15 s) | up to 120 **(default)** | demo: 28 hits in 14 s |
| Hard ceiling | 4 hits in any one second | std |
| Deliberate quiet | 2–3 stretches per minute of 1–2 s with voice only | b5 has ten seconds with no cue |

Count events, not items. A row of six phones popping is one event: the first 2–3 pops sound (each 1 dB quieter than the last), the rest are silent [demo]. Five coins flying is one event with 2–3 clinks.

### Which event gets which sound

| Visual event | Sound (kit name) | When the transient lands |
|---|---|---|
| Object pops in | `pop_1/2/3` rotating; `boing_1/2` for something springing up | On the first visible frame |
| Object drops and lands | `thud_soft`, `thud_wood`, `thud_metal`, `tap_light` by weight and material | On the contact frame |
| Stamp, red X, "NO" slam | `stamp_1/2`, with a quiet `swish_1` on the first stroke | On the contact frame |
| Line or drawing draws itself | `scribble_short/mid/long` matched to the stroke length; `marker` for a circle or underline | 30 ms after the stroke starts, runs for its length |
| Coin or money arrives | `coin_1…4` rotating; `coins_handful` for a bag | On arrival, never on launch |
| Throw, fast slide, character enters | `swish_1…3` | 50 ms into the move |
| Beat transition (whip, wipe, zoom) | `swish_4`, `whoosh_air`, `zoom_in` | 40–80 ms after the move starts |
| Number counts up | `tick_1/2` every 75 ms, `ding_1` when it lands | Ticks during, ding on the last frame |
| Big reveal (the name, the answer) | `riser_air` ending on the reveal, then `stamp` + `sting_hit` together | Riser starts 0.9–1.0 s before |
| Negation without a stamp | `error_buzz` | On the slash |
| Card, document, photo placed | `paper_place`, `page_flip`, `camera` | On the contact frame |
| Part clicks in, gate, lock | `metal_click`, `latch` | On the contact frame |
| Sparkle / success | `ding_1` at most once per sentence | With the first star |
| Something fails and falls | `slide_whistle_down` (CC-BY, credit it) then `flop` | Whistle 0.5 s before the landing |
| Machine or conveyor running | `loop_machine` | Fade in 0.3 s, keep very low |

What gets **no** sound: section-title or label changes (b5 gives its eight title changes none), camera pushes, pose changes (at most one soft swish per beat), idle float, blinks, the mouth.

### Sync

- Transient on the contact frame or one frame early: **−33 to 0 ms**. Never late. b5 sits 20–50 ms ahead of the visual settle (X lands 5.27 s, cue 5.25 s) [b5].
- Kit files are trimmed so the transient is 4 ms into the file; `data-start` is the hit time [demo, verified sample-accurate].
- Big physical actions are three sounds, not one: throw swish → impact 0.43 s later → debris (coins) 30 ms after that [b5: 18.28 / 18.71 / 18.74].

### Loudness

Voice clip at `data-volume="1"`. Kit files peak at −3 dBFS; `kit.js` applies these per role.

| Role | Level vs voice peak | Notes |
|---|---|---|
| Stamp, slam | −10 dB | b5's loudest cue is −10 |
| Impact, thud | −12 dB | b5: −11 to −14 |
| Click, paper | −14 dB | |
| Pop, coin, scribble | −15 dB | b5 coins: −16 to −17 |
| Ding | −16 dB | |
| Whoosh, swish | −17 dB | b5: −17 to −18 |
| Sting, tick, riser, comedy | −18 to −19 dB | |
| Loop / ambience | −30 dB | b5: −28 |

- Hit under a spoken word: 2 dB lower. Second hit within 60 ms of another: 3 dB lower. (Both automatic in `K.finish()`.)
- Whole SFX bus **12–18 dB under the voice** by RMS. b5 measures 14 [b5]; the demo 15.3 [demo]. Check with `tools/qa_audio.py`.
- Kit default levels land the bus ~19–20 dB under the voice (measured on a 12-chapter film). New films pass `Kit.create(tl, { …, sfxGain: 1.5 })` (linear multiplier on every cue, default 1.0) instead of multiplying `data-volume` by hand after `K.finish()`; with 1.33–1.6 the chapters measured 16–17.5 dB under. Always verify with `tools/qa_audio.py`.
- No SFX frame louder than the loudest voice frame (demo: 7.6 dB under).
- Master the finished film to **−14 LUFS integrated, −1.5 dBTP** with `tools/master.sh`. b5 shipped at −17.8, our film at −14.1.
- **Music bed ON (A/B test B won).** Bed 18–26 LU under the voice, gentle ducking 3–5 dB, one bed per act, sources and moods in each STYLE.md; mix with `kit/tools/mix_bed.sh`. Old rule kept for history: **No music (default).** Neither film the client compared has any, and Tradeoff Layer is voice-only [ref]. A channel style may choose a bed (many niches' competitors run one; see the channel's EVIDENCE.md). If it does: a licensed or CC0 track approved by the user, continuous, at least 20 dB under the voice (universal), and it does not replace event sounds.

### Variety

Rotate 3–4 variants of pops, coins and thuds (`kit.js` does this). Never the same file twice within 0.3 s. Match material: metal chip → `thud_metal`, building → `thud_wood`, paper → `paper_place`. Do not put the same heavy impact on everything.

---

## 2. The host's mouth moves with the speech

The client noticed b5's mouth; our host was a still picture [ours].

- **Method (since 15/11, v2):** painted mouth patches, not drawn stickers. The first version laid SVG cartoon mouths over the painted face; the client said it looked unnatural (sticker look, the artwork's own lip line showing underneath, and on `host_shrug` the mouth sat off the lips). Now each talking pose has 4 image-to-image edits of its own raw artwork (gpt-image-2 on kie, only the mouth changed) plus one with the eyes closed. `tools/mouth_patches.py` aligns each edit to the base (ECC), cuts a feathered region around what changed, colour-matches it to the surrounding skin and removes green spill. All mouth shapes of a pose share one region, so swapping them never changes the patch outline. Cost ≈ 0.15 USD per pose (5 images × 0.03). The SVG mouths remain only as a fallback for poses without patches.
- **Shapes:** rest (the artwork's own closed mouth), B slightly parted, A open "ah", O rounded "oh/oo", E wide "ee" with teeth. Level under 0.12 → rest, under 0.38 → B, above → A/O/E by the syllable's vowel (a → A, o/u → O, e/i/y → E).
- **In-betweens:** rest never jumps straight to A/O/E: the first step after rest is B, and the last open step before rest is B when the opening lasted more than one step.
- **Head life:** at each phrase start (pause ≥ 0.28 s) the whole host drifts to a new tilt of at most 0.8° with a 2–5 px shift over 0.7–1.1 s (`.kit-host-sway` wrapper), and back to level at the end of the range. A 2 px jaw dip only on words longer than 0.22 s. No motion on every word.
- **On twos:** the mouth may change at most every 2 frames (15 changes per second). Faster reads as flicker [std].
- **Closed** in any gap longer than 90 ms and for the first 50 ms of words starting with b, m, p [b5]. Shorter gaps keep shape B so the mouth does not snap shut between words.
- This is not phoneme-accurate lip-sync and must never be described as such.
- A pose whose artwork already has an open mouth (`host_happy`) gets no overlay: use it for reactions, not for long lines.

## 3. Blinks

- Every **2.3–4.4 s**, seeded, mean 3.4 s; eyes closed for **3 frames (0.1 s)** [b5: 19 blinks in 64.5 s].
- One in five is a double blink 0.24 s later [std].
- Add a blink on each pose change and just before a big reveal.
- Drawn as a skin-coloured lid plus a lash line inside each lens; glasses and brows stay untouched.

## 4. Idle life on the host

| Motion | Amount | Timing | Source |
|---|---|---|---|
| Breathing | scaleY +1.2 %, scaleX −0.5 %, origin at the feet | 3.4 s period, whole time on screen | std |
| Word dip | 3 px down and back | 0.07 s + 0.13 s at each word longer than 0.16 s | demo |
| Emphasis nod | 10 px | 0.09 s down, 0.2 s back; 1–2 key words per sentence | b5 dips 5 px / 2.2° on each caption key word |
| Pose change | swap in 0.06 s + squash 0.965 → 1.012 → 1 over 0.31 s | on a verb or key word, about every 3–6 s | ours (swap), b5 gestures every 3.6 s |
| Hop | 26 px | 0.14 s up, 0.16 s down, on the payoff word | std |

b5's hand gestures use 0.14 s anticipation, 0.14 s attack, 0.32 s hold, 0.28 s release [b5]. Use the same proportions if a pose is held only briefly: never less than 0.6 s in a pose.

## 5. Nothing on screen is still for more than 1 second

- Hard limit: **no frozen picture longer than 1.0 s** (`tools/qa_freeze.sh` must print nothing). Our film already held this [ours]; Tradeoff Layer does not: it holds a frozen picture for 2–4 s at a time [ref], and that is where it looks cheapest.
- No freeze is not the same as a lively picture. Tradeoff Layer is frozen for 21–26 % of its runtime and still changes the whole frame every 2.4–3.0 s. Our films were frozen for 0.2–4 % and changed the frame every 7–13 s [meas]. Rule 9 covers the framing; this rule only covers dead seconds.
- Slow camera push on the scene wrapper for the whole beat: scale 1.0 → 1.03–1.10, 10–80 px drift, `power1.inOut` [ours]. Keep it.
- Props that wait get a float: ±8 px, period 1.1–1.4 s, alternate direction per item [demo].
- Fill gaps with the picture itself (a draw-on, a camera push, a prop moving), or the host when he is on screen; do not add decoration (orbiting dots, pulsing rings) to fill time.

## 6. Entrances have weight

| Entrance | Recipe | Source |
|---|---|---|
| Pop | scale 0.2 → 1, opacity 0 → 1, **0.35 s**, `back.out(2.2)` | ours |
| Drop | falls 500–700 px in **0.30 s** `power2.in`; on contact squash to 0.84 × 1.12 in 70 ms, rebound to 1.06 × 0.97 in 110 ms, settle in 160 ms | demo, after b5's contact → result → rebound rule |
| Stamp / slam | scale **2.2 → 1 in 0.10 s** `power4.in`, tilted −8°; then 1.06 → 1 in 0.17 s | b5 |
| Label | slides up 60 px, **0.30 s**, `power3.out` | ours |
| Character or big prop from the side | 0.45 s, `back.out(1.6)` | ours |
| Exit | scale to 0.6 + fade, 0.18 s, `back.in(2)`; or fade 0.25 s | demo / ours |

Appear on the word that names the thing. Start a drop 0.3 s before the word so it lands on it.

## 7. Every impact has a consequence

One secondary effect per primary event, chosen from:

| Effect | Recipe | Use on |
|---|---|---|
| Dust puff | 4 circles thrown sideways, 0.22 s out + 0.32 s fade | anything that lands on the ground [b5: five times in the film] |
| Radial rays | 10 lines, expand 0.12 s, gone by 0.45 s | stamps, reveals, the red X [b5] |
| Shake | 8–10 px, 5 swings, decaying, **0.2 s**; whole scene only for the 1–2 biggest hits per minute | slams [b5] |
| Squash of the receiver | 5–10 %, 0.26 s | building takes a coin, pot takes a bag |
| Wobble | 2.5–6°, 3 swings in 0.5–0.6 s, each 60 % of the last | tall thing after landing; hanging sign [b5: 12° over 1.2 s] |
| Sparkles | 5–7 four-point stars, 0.42 s each, 50 ms apart | value, success, finished drawing |

Shake goes on a wrapper outside the camera wrapper, or the camera push will fight it.

## 8. Stagger

| Group | Gap between items | Source |
|---|---|---|
| 4–8 props popping | 50–70 ms | ours 60, b5 70 |
| Grid of 20+ | 30 ms, from the centre | ours |
| Flying coins | 90–110 ms | demo |
| Map pins, stamps in a row | 120 ms; b5's three regulator stamps are 0.58 s and 0.35 s apart, accelerating | ours, b5 |
| SVG paths drawing | 75–120 ms between starts, 0.34–0.5 s each | ours, demo |

## 9. Beat structure, shots and transitions

- Group sentences into **beats of 8–20 s**. Within a beat the set stays: same background, one anchor object that persists (and the host, if this beat uses him, in place). Beats without the host are normal (see explainer-direct: host is a tool, ~40–60 % screen time). Only props, drawings and labels change [ours; this is what fixed "fragmented"].
- **A beat is 2–5 shots.** A shot is one framing of the set: wide, punch-in on the named object, full-frame insert (diagram, map, photo, number, text card), reaction. Change shot every 3–6 s. "Fragmented" meant an unrelated layout on every sentence; a new framing of the same scene is what every competitor does [meas].

| Full-frame changes (more than 20 % of the picture within 0.2 s) | Per minute | Median gap | 90th percentile gap | Source |
|---|---|---|---|---|
| Tradeoff Layer, 3 videos | 16.0–20.5 | 2.4–3.0 s | 4.8–5.4 s | meas |
| Crayon Capital, CoreSight, The Invisible Game | 15.7–17.6 | 2.8–3.4 s | 6.0–7.1 s | meas |
| Kurzgesagt, fern and similar | 12.3–13.2 | 2.8–3.8 s | 8.5–9.1 s | meas |
| Sam O'Nella, The Infographics Show (slowest animated ones) | 8.9–10.8 | 3.8–5.3 s | 12.5–14.7 s | meas |
| **Default target** (a channel's `style.json` → `pace` overrides) | **≥ 10 (first 60 s of a film: ≥ 14)** | **≤ 6 s** | over 12 s only with a reason in the plan, never over 20 s | `tools/qa_pace.py --channel <slug>` |

- A framing may run past 12 s only when it is one diagram or map that gains a new element at least every 3 s (Kurzgesagt holds such builds for 14–34 s [meas]).
- A cut inside a beat is a new `K.push` segment that starts at a different scale and position, or a full-frame layer switched on. It gets no sound of its own.
- **Change mode every 30–45 s (default; the style's `mode_change_s`)**: scene with characters, diagram, map, real photo or footage, big number, a full-screen text card on a turn line, a metaphor cutaway. The Infographics Show drops a 3–6 word text card every 30–40 s; Tradeoff Layer cuts to a chart or a map about once a minute [meas, Gemini estimate for the second]. At most one text card per chapter (default).
- A chapter opens on a new picture, not on the host where the last chapter left him. The film opens on the thumbnail's object: Tradeoff Layer shows 14 different compositions in its first 30 s, our films showed one [meas].
- Change set only between beats, with one of: whip-pan (0.42 s, `power3.inOut`), clip-path wipe (0.45 s, `power3.inOut`), zoom-through (0.40 s out `power2.in`, 0.42 s in `power2.out`) [ours]. Vary them; do not use the same one twice running.
- The move starts **0.12 s before the first word** of the new beat [ours].
- One whoosh per transition, and no other sound within 0.25 s of it.

## 10. Text: keyword badges, no subtitles

- **No burned-in word-by-word captions.** Our best film has none, and neither do three of the four references [ours, ref]. b5 uses them because its stage is small and its presenter sits in a corner; our host and props fill the frame and captions would cover them. YouTube supplies closed captions.
- Badges: 2–4 words, all caps, **at most 2 visible at once**, never the same text twice on screen.
- A full-screen text card (5 words or fewer, on a turn line of the script) is a pattern interrupt, not a caption: at most one per chapter, held like a badge (0.5 s + 0.3 s per word) [meas: The Infographics Show, Kurzgesagt chapter cards].
- Hold each at least 0.5 s + 0.3 s per word, and the last line of a film at least 2 s (HyperFrames' check enforces this).
- Colour by meaning: primary colour = fact, red = negative, accent = money.
- Numbers roll up (0.5–1.0 s, ticking, ding on landing) [ref: Jaguar, Invisible Game, Crayon Capital all do it].
- Highlight by drawing: circle in 0.42 s, underline in 0.30 s, both with the marker sound [ref: red hand-drawn circle and highlighter swipes confirmed].

## 11. Visuals illustrate the exact sentence

Kept from the brief that made our best film, because craft on top of generic pictures is wasted:

- "A few cents per chip" is a chip with one small coin dropping on it, not a money bag.
- Draw what the sentence says with SVG that builds itself: a building line by line, a circuit on a blueprint, an arrow between the two named things, a red X over the exact object being negated.
- A new visual idea every 1–4 s. No empty frame longer than 1 s.
- Named real entities appear as their real media, not as text: logo sticker for a company, real photo print for a product/building/place, archival footage on a TV prop for a historic moment (rule 12). Text is a secondary caption. Still no real people's faces unless the brief clears it.

## 12. Real logos, photos and footage live inside the cartoon world

What other channels in the niche do: they pull logos from Wikipedia/Wikimedia Commons and old footage from the Internet Archive, so the viewer recognises the real thing instantly. A text card saying "NIKE" is weaker than the Nike logo.

- Fetch with `tools/fetch_media.py` (Wikidata P154 logo / P18 image, Commons search, Internet Archive). Every file carries source, author and license in `CREDITS.json`. Only `free: true` files go in a film; non-free logos are flagged into `nonfree/` for a human decision.
- Never paste a flat rectangle on the stage. Logos become die-cut stickers (`K.sticker`: white outline, hard shadow, pop with overshoot, slight rotation, sparkle). Photos become taped prints (`K.photo`: white border, caption, tape, slight rotation, drop-and-land with paper sound and dust). Footage plays inside a TV prop (`K.tv`: rolls in, screen flashes on, click). Same weight, overshoot, secondary-effect and SFX rules as every other prop.
- Photos get a light grade (`saturate .82, sepia .12`) so they sit on the channel palette; footage a stronger one.
- CC BY / BY-SA photos keep a small on-screen credit (texture, `data-layout-ignore`); the full credit list (`fetch_media.py used`) goes in the description.
- Logos are trademarks: identification/commentary only, never in a way that implies endorsement or as our own brand.

## 13. The host appears in three modes, and often not at all

None of the 21 competitor videos keeps a presenter on screen: 0–5 % of runtime. Their pictures are story characters acting in scenes (70–85 % at Tradeoff Layer, Crayon Capital, Kurzgesagt by Gemini's estimate), diagrams, maps and real media [meas]. Both our first films had the host in 40 of 40 sampled frames, in one spot, at one size [meas]. We keep him because he is the channel's own character; the client's rule is that he is a tool. How much he is on screen is per channel (`host` in style.json; default 40–60 % of a film, plan the lower half).

| Mode | What he does | Size | Where it fits | Limit |
|---|---|---|---|---|
| Presenter | Talks to the viewer | Bust or full figure | The hook's question, a direct question, the core truth, the sign-off | From the channel style (default a quarter of the film at most, 12 s at a time) |
| Actor | Does what the sentence says, inside the scene | As the scene needs | Mechanisms where a person does something | Existing action poses; a new pose needs approval and mouth patches |
| Corner reactor | Reacts to a full-frame diagram or map | A fifth of the frame height or less, at an edge | Numbers, maps, timelines | Pose change, nod or shrug on the key word |
| Absent | Voice-over only | none | Real photos and footage, the densest diagrams, frame 0 of the film | no limit |

Whenever he is visible in any mode, `talk`, `blinks` and `breathe` still run (rules 2–4).

## 14. The first 30 seconds and the end-screen plate

- Frame 0 is the thumbnail's object, full frame and already moving. No logo, title card or host during the first sentence. At least 8 shots in the first 30 s [meas: competitor hooks end at 0:26–0:50 with no logo and no self-introduction].
- The last 8–12 s (default; the style's `ending`) of the film are one designed shot: half the frame clear for YouTube's next-video box and subscribe button, the host pointing at it from the other half, the voice pitching that one video. YouTube allows end screens on the last 5–20 s and asks creators to "leave enough space and time at the end of the video". Nothing static: breathing and float run to the last frame.

---

## 15. Every seam has a cause, and every chapter has one hero shot

- **Enter the next set through something already on screen** [hf]. A set change that starts from nothing reads as the next slide. Recipes, all seek-safe (mechanisms in `VISUAL_SOURCES.md` §1):

| Seam | How | When |
|---|---|---|
| Object becomes the world | the anchor object grows past the frame in about 0.65 s, its surroundings blur about 15 px, its fill is the next ground | the next beat happens inside that object (a server, a cockpit, a factory floor) |
| Zoom through | an opening on screen (a door, a screen, a lens) scales from about 8 % to 250 % in 0.35 s on a strong ease-in | going from the outside to the inside |
| Match cut | one shape holds its place and size for a single-frame swap while everything round it changes | two things that share a shape (a key card and a boarding pass, a dial and a clock) |
| Carry across | the result of this beat shrinks to about 0.6 and lands inside the next set as a prop | a number or object the next beat keeps using |
| Whip | 0.13–0.3 s smear, text blurred no more than 10 px | a jump in place or time, announced by the voice |
| Dip cut | the outgoing frame darkens about 40 % for 3 frames, then a hard cut | a deliberate hard turn ("But.") |

- **Three to five kinds of seam in a film**, each caused by something on screen; at most a third of the seams between beats are hard cuts; never the same seam twice running (rule 9) [hf].
- **Ease by role** [hf]: arrivals `expo.out` or `power4.out`; camera moves and colour floods `power2.inOut`; exits and zoom-throughs `power3.in`. Exits are 40–50 % shorter than the matching entrance. The next element starts when the previous one is 30–50 % done. The same `power2.out` at 0.5 s on everything is the flat default.
- **Hold 0.3–0.75 s before the payoff** [hf]: the picture and the bed go quiet (`K.dip`), then the hit. The process plays fast; the payoff plays at normal speed.
- **One hero shot per chapter**, named in the beat plan: the biggest picture of the chapter, on its most important sentence. It is where the budget goes (a build, a real clip, a generated clip, the one 3D reveal). The film's peak (Story card) is the hero shot of its chapter.
- **The hero of any shot fills at least 40 % of the frame's height or width** [hf; sheet: our weakest frames had a hero under a tenth of the frame]. Too many things to fit: cut things, never shrink them.
- **Worlds.** A film visits several grounds, each with its own background, light and scale, never one ground from the first frame to the last [hf; sheet]. Default: at least three in a film. A channel's dark or paper ground is its home, not its only room.

## 16. Tells of a generated film

A viewer does not name these; they read the film as cheap and leave. Check the list on the review sheets (`REVIEW_PASS.md` §3) and add any new default a first render shows to the channel's STYLE.md "what we never do".

- **A card with words standing in for a scene** [sheet]: a quote card, a form, a date card, a headline crop, a label alone. More than 1 frame in 4 on a review sheet, or two in a row, is a slideshow. Show the thing; bring the document in for 2–3 s with one phrase marked.
- **A dark void with a small thing floating in the middle** [hf; sheet].
- **A grey mock screen** (a fake chat, a fake booking page, bars for text) where the real page, the real object or a drawn scene could be [hf; sheet].
- **Three cards in a row**, icons in circles, side-by-side panels as the whole picture [hf].
- **Every scene entering the same way**, or the same move beat after beat; everything centred; everything fading and sliding up [hf].
- **Text that keeps moving after it lands.** A landed title, number or label is dead still: no float, no creeping scale. The motion moves to the next element, the camera or the world behind it [hf]. This narrows rule 5: the float is for waiting props in a scene, never for text; the slow camera push and the host's breathing stay.
- **The whole diagram at once.** One part per beat, each when it is named, across the back half of the shot; everything on screen in the first quarter and then frozen reads as a slide [hf].
- **A narrator repeating the on-screen text word for word** [hf].
- **Text nobody can read on a phone**: anything meant to be read under 28 px at 1080 (2.6 % of the short side), or held shorter than 0.5 s + 0.3 s a word [hf]. Too many words: cut words, never shrink type.
- **Glow, bloom, floating particles as decoration** [hf].

---

## Not adopted, and why

| Idea | Why not |
|---|---|
| Whoosh on every section or label change | A Gemini read claimed a reference does this; measurement showed it does not. It would add 8+ meaningless sounds a minute. |
| Whole-pose sprites swapped per mouth shape | Different generations of the same pose do not align pixel for pixel, so the head would jump. Only a small aligned, feathered mouth/eye patch is swapped (v2). |
| Karaoke captions | See rule 10. |
| Locked camera | b5 and three references lock it, but our slow push is part of why our film looks better. |
| Host on screen for the whole film | Our first two films did it (40 of 40 sampled frames). The client rejected it and no measured competitor does it. See rule 13. |
| A whoosh or sting on every cut | With a cut every 3–6 s it would add 10–20 sounds a minute on top of 60–75 event sounds. Cuts inside a beat are silent. |
| Music bed copied from the documentary references | Different genre (footage + motion graphics). Not what the client compared. |
| Glass panels, 3D tilts, film-gate frames | Confirmed in the references, but they belong to the documentary look, not ours. |
| "Never hard-cut: always animate the transition" (a Manim skill) | Our measured competitors cut hard inside a beat every 3–6 s. Hard cuts stay inside beats; rule 15 covers the seams between sets. |
| "Breathing and floating loops look generated" applied to the host | HyperFrames itself exempts a character's idle breath (acting). Ours is measured from the film the client preferred. The rule is adopted for text only (rule 16). |
| Mounting HyperFrames registry components as they come | They bring their own ground, fonts and colours (tested 18/11/2026). Port the mechanism or re-skin the installed copy (`VISUAL_SOURCES.md` §1). |
| A score out of 10 for a chapter or a script | A score finds nothing to fix. Reviews produce notes with an exact change (`REVIEW_PASS.md`). |

## Quick numbers

| Thing | Number |
|---|---|
| SFX hits per minute | per channel style (default 15–45; hook up to ~60); max 4 in one second; prefer a cinematic role-levelled library (kit/sfx_v2) over game-UI sounds |
| SFX sync | −33 to 0 ms against the contact frame |
| SFX bus vs voice | 12–18 dB under (RMS) |
| Master | −14 LUFS, −1.5 dBTP |
| Mouth | painted patches rest/B/A/O/E, on twos, through B in and out of rest, shut in gaps > 90 ms |
| Blink | every 2.3–4.4 s, 0.1 s closed |
| Breathing | 1.2 %, 3.4 s |
| Max static picture | 1.0 s |
| Pop | 0.35 s `back.out(2.2)` |
| Drop + settle | 0.30 s + 0.34 s |
| Stamp | 2.2 → 1 in 0.10 s, shake 0.2 s |
| Stagger | 60 ms props, 30 ms grids, 100 ms coins |
| Transition | 0.42–0.45 s, starts 0.12 s before the first word |
| Badges | 2–4 words, max 2 on screen |
| Beat | 8–20 s, one set, 2–5 shots |
| Full-frame changes | default ≥ 10 per minute, ≥ 14 in a film's first 60 s, median gap ≤ 6 s; per channel in `style.json` (`tools/qa_pace.py --channel <slug>`) |
| Longest single framing | default 12 s; up to 20 s for one diagram that keeps building |
| Mode change | default every 30–45 s; at most one text card per chapter |
| Host | default visible 40–60 % of a film (plan the lower half), presenter mode ≤ 25 % and ≤ 12 s at a time; per channel in `style.json`; never in frame 0 (all channels) |
| End-screen plate | default last 8–12 s, half the frame clear, voice pitches one video |
| Hero of a shot | at least 40 % of the frame's height or width |
| Text meant to be read | 28 px or more at 1080; held 0.5 s + 0.3 s a word; a landed line does not move |
| Document on screen | a proof insert of 2–3 s with one marked phrase of 8 words or fewer; at most 1 card frame in 4 |
| Seams | 3–5 kinds per film, each entered through an object on screen; at most a third hard cuts |
| Hold before the payoff | 0.3–0.75 s |
| Grounds | at least 3 in a film |
| Hero shot | one per chapter, named in the plan; generated clips at most 3 per film and 2 USD |
