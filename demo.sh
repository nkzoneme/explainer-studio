#!/usr/bin/env bash
# Demo: build one 1080x1920 Short from scratch with every key you have.
#   FAL_API_KEY       voice + word timings            (required)
#   PEXELS_API_KEY    real photo from Pexels          (else Wikimedia Commons, no key)
#   KIE_API_KEY       one generated cartoon prop      (else skipped)
# Cost with all keys: about 0.05 USD. Output: explainer/film/demo/shorts/short_1.mp4 (+ _contact.jpg)
# Usage: ./demo.sh [voice]      e.g. ./demo.sh Rachel
set -euo pipefail
cd "$(dirname "$0")"
PY=python3; [ -x .venv/bin/python ] && PY="$(pwd)/.venv/bin/python"
VOICE="${1:-Rachel}"
has() { "$PY" -c "import sys; sys.path.insert(0,'explainer'); from envload import get_key; sys.exit(0 if get_key('$1', required=False) else 1)"; }

has FAL_API_KEY || { echo "FAL_API_KEY is missing: run ./setup.sh first"; exit 1; }
[ -f explainer/shorts/styles/demo.json ] || ./setup.sh --new-channel demo "Demo Studio" >/dev/null
cd explainer
D=film/demo/shorts/s1; M=film/demo/media; mkdir -p "$D/vo" "$M"

echo "== 1/5 script"
cat > "$D/vo/s1.txt" <<'EOF'
Your pencil has no lead in it. Not a trace. The grey core is graphite, mixed with clay and baked in a kiln. More clay makes a harder, lighter pencil. Less clay makes it softer and darker. People called it lead because early miners thought graphite was a kind of lead. Why the name stuck for five hundred years is the full video, linked below.
EOF
cat "$D/vo/s1.txt"

echo "== 2/5 voice (FAL / ElevenLabs, voice $VOICE)"
[ -f "$D/vo/s1.mp3" ] || "$PY" fal_tts.py "$D/vo/s1.txt" "$D/vo/s1.mp3" "$VOICE"
"$PY" kit/tools/vo_build.py "$D/vo/s1_w" "$D/vo/s1.mp3" | tail -1

echo "== 3/5 real photo"
if [ -f "$M/CREDITS.json" ]; then echo "  cached"
elif has PEXELS_API_KEY; then "$PY" kit/tools/fetch_media.py pexels "pencil graphite" "$M" --n 1 | tail -1
else "$PY" kit/tools/fetch_media.py commons "pencil" "$M" --n 1 | tail -1; fi
PHOTO=$("$PY" -c "import json,sys; r=[x for x in json.load(open('$M/CREDITS.json')) if x.get('kind','photo')=='photo']; print('$M/'+r[0]['file'] if r else '')" 2>/dev/null || true)

echo "== 4/5 generated prop (KIE)"
PROP=""
if has KIE_API_KEY; then
  cat > film/demo/kie_pencil.json <<'EOF'
{"name": "demo_pencil", "model": "gpt-image-2-text-to-image", "out": "film/demo/media/prop_pencil.png",
 "input": {"prompt": "A single yellow wooden pencil cut in half lengthwise showing the grey graphite core, flat 2D cartoon explainer illustration, bold even dark outlines, simple cel shading, plain light background, no text, no logos, no watermark.", "aspect_ratio": "1:1", "resolution": "1K"}}
EOF
  "$PY" kie.py run film/demo/kie_pencil.json | tail -1
  PROP=film/demo/media/prop_pencil.png
else echo "  KIE_API_KEY not set: skipped"; fi

echo "== 5/5 compose + render + master + QA"
ARGS=(--style demo --dir "$D" --vo "$D/vo/s1_w" --force)
[ -n "$PHOTO" ] && ARGS+=(--media "$PHOTO")
[ -n "$PROP" ] && ARGS+=(--img "$PROP")
"$PY" shorts/native/new_short.py "${ARGS[@]}" | tail -1
"$PY" - "$D" "$(basename "${PHOTO:-none}")" "$(basename "${PROP:-none}")" <<'EOF'
import json, sys, re
d, photo, prop = sys.argv[1:]
words = json.load(open(f"{d}/words.json"))
def at(w):  # start time of the first word that starts with w
    return next((x["start"] for x in words if x["word"].lower().strip(".,").startswith(w)), 1.0)
html = open(f"{d}/index.html").read()
props = []
if photo != "none":
    props.append(f'<figure class="kit-photo" id="ph" style="position:absolute;left:170px;top:470px;width:720px;transform:rotate(-3deg)"><img src="assets/media/{photo}" style="display:block;width:100%;height:520px;object-fit:cover"><figcaption>Photo: see CREDITS</figcaption></figure>')
if prop != "none":
    props.append(f'<img id="pr" src="assets/img/{prop}" style="position:absolute;left:250px;top:500px;width:560px;border-radius:24px;opacity:0">')
props.append('<div class="label" id="lb" style="position:absolute;left:190px;top:1100px;font-size:64px;opacity:0">GRAPHITE + CLAY</div>')
html = html.replace("<!-- props here -->", "\n".join(props))
tl = []
if prop != "none":
    tl.append(f'tl.to("#ph", {{ opacity: 0, duration: 0.25 }}, {at("graphite") - 0.1:.2f});' if photo != "none" else "")
    tl.append(f'K.pop("#pr", {at("graphite"):.2f}, {{ sfx: "pop_2" }});')
tl.append(f'K.pop("#lb", {at("clay"):.2f}, {{ sfx: "pop_1" }});')
html = html.replace('HOOK <em>TITLE</em>', 'NO <em>LEAD</em>?').replace("      S.finish();", "      " + "\n      ".join(t for t in tl if t) + "\n      S.finish();", 1)
open(f"{d}/index.html", "w").write(html)
EOF
sh shorts/native/finish_short.sh "$D" film/demo/shorts/short_1.mp4 2>&1 | grep -E "Check (passed|failed)|LUFS|SFX bus|freeze_duration|silence_duration|codec_name=h264|contact sheet" || true
echo
echo "Done: explainer/film/demo/shorts/short_1.mp4"
echo "Credits for the photo: explainer/$M/CREDITS.md"
