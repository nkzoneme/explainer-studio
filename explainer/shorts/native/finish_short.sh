#!/bin/sh
# Render + master + QA one native Short.   Usage (from explainer/):  sh shorts/native/finish_short.sh <short_dir> <out.mp4>
# Writes <short_dir>/out/raw.mp4, <out.mp4> (-14 LUFS, TP<=-1.5 after AAC), <out>_contact.jpg (1 fps sheet with the
# UI zones drawn), and prints: render audioCount, loudness, SFX-vs-voice, freeze list, silence list, ffprobe line.
set -e
d="$1"; out="$2"; here=$(cd "$(dirname "$0")" && pwd); ex=$(cd "$here/../.." && pwd)
case "$out" in /*) ;; *) out="$ex/$out";; esac
cd "$d"
mkdir -p out
npx -y hyperframes@0.9.46 check 2>&1 | grep -E "✗|Check (passed|failed)" || true
npx -y hyperframes@0.9.46 render -o out/raw.mp4 > out/render.log 2>&1
grep -o '"audioCount":[0-9]*' out/render.log | tail -1
vo=$(ls assets/vo/*.mp3 | head -1)
# master: -14 LUFS, true-peak ceiling -2.0 before AAC so the encoded file lands <= -1.5 dBTP (see explainer-direct)
TP=-2.0 sh "$ex/kit/tools/master.sh" out/raw.mp4 "$out"
python3 "$ex/kit/tools/qa_audio.py" out/raw.mp4 "$vo" 2>&1 | tail -4
echo "freeze:"; sh "$ex/kit/tools/qa_freeze.sh" "$out" 1.0 || true
echo "silence (>0.9 s under -45 dB):"; ffmpeg -hide_banner -nostats -i "$out" -af silencedetect=noise=-45dB:d=0.9 -f null - 2>&1 | grep -E "silence_(start|end)" || echo "  none"
ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate -show_entries format=duration -of compact "$out"
sh "$here/contact_sheet.sh" "$out"
