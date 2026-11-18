# kit/tools: new in the 17/11/2026 upgrade (IMPROVE_PLAN)

Run from `explainer/`. Needs ffmpeg, tesseract, numpy, Pillow, OpenCV (all present). `yt-dlp` and `rembg` live in `~/.cache/explainer-venv/bin` (thumb_sheet finds them itself). No paid calls anywhere.

## qa_hook.py: first 30 s of chapter 1
```
python3 kit/tools/qa_hook.py film/<slug>/ch01 --channel my_channel --title "Our title" [--script SCRIPT.md] [--thumb t.png] [--out r.json] [--no-video]
```
Checks voice by 1.5 s, sentence 1 (<= 15 words, by style `first_sentence_by_s`), the promise line (SCRIPT line tagged `[promise]` / `Promise:`, else the section headed "Promise", located in `vo/<slug>/ch01_w.words.json`, spoken by `promise_by_s`), title words by `promise_by_s`, banned words in 60 s, >= 8 full-frame changes in 30 s (first by 3 s, none held > 5 s), no channel/title text or host call in sentence 1 (OCR + index.html), and a thumbnail-vs-frame-0 hash/histogram (WARN only). Exit 1 on FAIL. Also runs inside `qa_film.py`. Tested on two pilot films: one FAILED promise (spoken 51.9 s, limit 20 s), one FAILED pace (one 6 s hold).py: G2 gate
```
python3 kit/tools/remake_diff.py research/remake/<slug>/REMAKE_MAP.md film/<slug>/final/chapters.json [--entity "Acme"] [--title ..] [--src-title ..] [--thumb-text "BIG NUMBER"] [--thumb-img a.png --src-thumb-img b.png]
```
Chapter starts within +-10 s of the source (limit 30 %), beat-order run (limit 60 %, by word overlap with the beat table, or add topic tags later), the `Angle:` line ("They asked X. We ask Y.", Y in our title), title and thumbnail-text overlap, thumbnail dHash >= 20 bits, wording (6-word runs 0, 4-word runs <= 3 per 1,000). Needs `--script`/`--transcript` (defaults: files beside the map). Missing inputs print SKIP, never PASS. Both existing remakes fail `angle` because the REMAKE_MAPs predate the rule (one also fails `title` on a shared place name unless `--entity` names it).

## thumb_sheet.py: sheet and make
```
python3 kit/tools/thumb_sheet.py sheet --query "topic words" --cand a.png b.png c.png --channel my_channel --titles "T1" "T2" "T3" --out DIR
python3 kit/tools/thumb_sheet.py make --photo in.jpg --channel my_channel --words "BIG NUMBER" --out thumb.png --credit "Author, CC BY 4.0, url"
```
`sheet`: yt-dlp fetches 6 competitor thumbnails for the query (image + title only). Output `DIR/sheet_blind.png` (no marks, for the fresh-agent click test), `sheet_marked.png` (ours ringed A/B/C, for the operator), `checks.json` (words <= 3, jargon list, cap height >= 110 px, contrast >= 7:1, empty bottom-right 180x90, tesseract read-back at 320 px). Exit 1 if any candidate fails. OCR on tilted stamps is unreliable; treat the checks as flags. `--refs DIR` replaces yt-dlp with local images.
`make`: rembg cut-out (first run downloads the u2net model once), else `--mask` (white = keep), else GrabCut in `--rect x0,y0,x1,y1`; `thumb_look` outline = ink outline on a light ground, halftone = dot screen with an accent edge on a dark ground; <= 3 words on a solid plate, cap height >= 110. `thumb.png.json` records the cut-out method and credit. Use public-domain / CC BY photos only.

## vo_post.sh: light voice post (new films only)
```
kit/tools/vo_post.sh in.mp3 out.mp3        # env: HPF=70 PRES=2 MUD=-1.5 DEESS=0.4 RATIO=2.5 THRESH=-20 ROOM=6 (0 = off) MAKEUP=2 LIMIT=-1.5
```
High-pass 70 Hz, de-ess, -1.5 dB at 250 Hz, +2 dB at 4 kHz, 2.5:1 compression, 6 % room, limiter. Duration is identical to the input (checked on a 124 s chapter: 124.47 s both). Level rises about 4 LU (-23.9 to -19.7 LUFS on that file); the film mix re-levels. Run before `vo_build.py`. Operator's ears decide: try `ROOM=0 PRES=1` first if it sounds harsh.

## retention_map.py: drops to sentence and picture
```
python3 kit/tools/retention_map.py --project <slug> --chapters film/<slug>/final/chapters.json (--csv studio.csv --duration S | --drops 83,2:10,412) [--video final.mp4] [--script SCRIPT.md]
```
Output in `film/<slug>/final/retention/` (`retention_map.md/.json`, frame grabs with `--video`): time, chapter, sentence spoken, matched SCRIPT beat and its `[visual]` type, cause tag guess (list, number-chain, host, card-only). Script match needs the voiced text to resemble the script (>= 50 % longest-match), otherwise "no script match".

## Fixes in this batch
- `fetch_media.py`: GFDL-only files now `free: false` with `reason`; dual-licensed (GFDL plus CC or PD) stay free. Existing CREDITS.json rows are not rewritten.
- `kit.js` edit mode: `sfxGain` defaults to 0.6 and values above 1.0 are ignored with a console warning. Basis: the edit-mode test ran at 0.6 and measured 15.4 dB under the voice (target 12-18); 1.5 would land about 7 dB under. 1.5 stays valid for legacy mode only. `explainer-direct/SKILL.md` lines 122 and 127 still say 1.5 for new films and need that sentence changed by the skill owner.
- `qa_film.py`: new checks `factcheck` (FAIL if `research/**/<film>/FACTCHECK.md` is missing, has no rows, or any row is UNVERIFIED) and `hook` (qa_hook on chapter 1; title taken from the SCRIPT heading, or `--title`).
