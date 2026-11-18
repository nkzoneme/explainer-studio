# Picture review: see the film as a first-time viewer on a phone

The QA scripts catch what is broken (freeze, loudness, pace, levels). This pass catches what is weak. You wrote the timeline, so you know what happens; the viewer sees it once, at full speed, often on a phone. Review as a harsh director, not a proud author.

Adapted from HyperFrames `skills/hyperframes/references/review.md` and browser-use/video-use `SKILL.md` (both in `research_flow/REFERENCE_REPOS.md`). Run on our own films on 18/11/2026: the first sheet of one film showed 11 of 24 tiles as a text card on the same dark ground, a hero object under a tenth of the frame, and source lines nobody can read on a phone. `qa_pace`, `qa_freeze` and `qa_audio` had all passed.

**When.** Every chapter, after its QA loop passes (explainer-direct Step 4). The joined film, before G4.
**Who.** The agent that built the chapter does steps 1–4. A fresh agent does step 5 on chapter 1 and on the joined film.

## 1. Make the sheets

```
python3 kit/tools/qa_review.py out/chNN_raw.mp4 --words ../../../vo/<slug>/chNN_w.words.json     # one chapter, about 5 s
python3 kit/tools/qa_review.py final/final.mp4 --srt final/film.srt                               # the film, about 45 s
```

It writes `review_beats_NN.jpg` (one frame about a second after every full-frame change, with the sentence being spoken; a framing held over 8 s gets a second tile marked `held`, 70 % in), `review_phone_NN.jpg` (the same frames 360 px wide, shown 1:1) and `review.json` (`unanswered`: sentences of 2 s or more during which nothing on screen changed). Open every sheet. A tile is one instant: before you file an empty-looking frame as a P0, look at its `held` tile or snapshot that second. On a film over about 95 shots the film-level sheets are thinned after the first 30 s; the chapter runs show every shot.

Before a render exists, HyperFrames can make the same kind of sheets from the composition. It needs one marker per beat, placed in `#root` before the stage (zero size; checked: `check` still passes and the frames are pixel-identical):

```html
<i id="bm1" class="clip" data-beat="b1-invite" data-start="0" data-duration="8.5" data-track-index="9" style="position:absolute;width:0;height:0"></i>
```

`npx -y hyperframes@0.9.46 snapshot --review -o <dir>` then writes `review-beats.jpg`, `review-phone.jpg` and a five-frame strip across every beat boundary (`review-seam-NN.jpg`, −0.2 s to +0.2 s). Use the strips to look at a transition frame by frame.

## 2. The stranger test (write it down)

For each tile on the phone sheet write one sentence as someone who has never read the script: what is on screen, naming every object. Then answer in one word each: is the thing the sentence names on screen (yes / no)? Could you read the largest text (yes / no / none)?

An object you would have to explain is a P0. A sentence whose subject is not on screen is a P0. Text meant to be read that you cannot read at 360 px is a P0.

## 3. One pass per question

| Question | What it catches | Rank |
|---|---|---|
| Is it a picture or a document? | Count the tiles whose main content is words on a card: a quote, a filing, a headline crop, a date, a label alone. More than 1 tile in 4 on a sheet, or 2 in a row | P1 (P0 inside the first 30 s) |
| Does the hero fill the frame? | The thing the sentence is about takes under 40 % of the frame's height or width; a small object floating in the ground | P1 (P0 inside the first 30 s) |
| Same ground, same layout? | 3 tiles in a row with the same background and the same arrangement (card in the centre, host at one side) | P1 |
| Say it, show it | Every entry of `unanswered`; a list that finishes on screen while the voice is still naming it; a result stamped before the voice has earned it | P1 |
| Does it read as what it is? | A shape that reads as another object, a photo whose signage contradicts its label, a mock screen standing in for the real thing | P0 |
| Framing and contact | Crops, text at the edge, things floating that should touch, an empty half | P1 |
| The pictures alone | Cover the sentences: do the tiles still tell the story in order? | P1 |
| Tells | Anything from `CRAFT_RULES.md` §16 | P1 (P0 in the hook) |

A document is evidence, not the scene. Show the thing itself (the object, the place, the drawn person, the map) and bring the document in as a proof insert of 2–3 s with **one** phrase of 8 words or fewer, large enough to read on the phone sheet. The source line belongs in the description; an on-screen source line under 28 px is not read by anyone.

## 4. Notes and fixes

One line per problem, exactly this shape:

```
t=12.7s · booking card · a grey mock web page stands in for the real one → a capture of the real page, its button greyed out · the time stamp stays
```

`t · where · problem → exact change · what stays`. Rank each P0 (breaks the read: unreadable, wrong, unexplained, a tell in the hook), P1 (weakens the film: a dead stretch, a document run, a small hero, a seam that jumps) or P2 (polish).

- Fix every P0 and the P1s worth their time: text first, then framing, then timing, then detail.
- Re-make only the sheets you changed, once. A second pass only while a P0 is open. Two passes at most per chapter.
- Never score the film out of 10: a score finds nothing to fix.
- A chapter that feels busy: remove a third of the motion and keep the moves that lead the eye.

## 5. Fresh eyes (chapter 1 and the joined film)

Start one `explainer-worker` that gets **only** the title, the thumbnail file and the sheet paths. No script, no beat plan, no brief. Its whole brief:

```
You are a first-time viewer and a harsh director. Read only these files: <thumbnail>, <review_phone_*.jpg>, <review_beats_*.jpg>, <review.json>. The title is "<title>".
1. First 10 s: what do the title and thumbnail make you expect to see? Do the first three tiles show it? Answer yes or no, then one line.
2. For the first 12 tiles, one sentence each: what a stranger sees, naming every object.
3. P0 and P1 notes in this exact shape, one per line: t=<s> · where · problem → exact change · what stays
4. The three tiles where you would stop watching, and why, one line each.
No praise, no summary, no score. Do not edit any file.
```

Keep the editing to yourself. Its notes join yours; the same caps apply.

## 6. The delivery note

Write `film/<slug>/REVIEW.md` (append per chapter) and put its short form in the G4 report:

- what was measured (name the tool) and what was only looked at; what nobody checked (the sound was measured, not heard);
- the P0 and P1 notes with their status: fixed, or kept on purpose and why;
- the weakest shot of the chapter, and what you would change with more time.

The next agent reads it before changing anything.
