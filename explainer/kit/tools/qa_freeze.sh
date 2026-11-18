#!/bin/sh
# Static-frame check. Usage: qa_freeze.sh <render.mp4> [max_static_seconds=1.0]
# Lists every stretch where the picture does not change for longer than the limit (ffmpeg freezedetect, noise -50 dB).
# A talking host with blinks/breathing should produce NO output; any line here is a dead moment to fix.
f="$1"; d="${2:-1.0}"
ffmpeg -hide_banner -nostats -i "$f" -vf "freezedetect=n=-50dB:d=$d" -map 0:v -f null - 2>&1 | grep -E "freeze_(start|duration)" | sed 's/.*lavfi.//' || true
echo "freeze check done (limit ${d}s)"
