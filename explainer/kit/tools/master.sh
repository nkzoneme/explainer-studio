#!/bin/sh
# Loudness master. Usage: master.sh <in.mp4> <out.mp4>
# Two-pass EBU R128 loudnorm of the audio to -14 LUFS integrated, -1.5 dBTP; video stream is copied untouched.
# Optional: TP=-2.0 sh master.sh in out  (lower true-peak ceiling; AAC encoding can overshoot the target by ~0.4 dB).
# Optional: AB=256k (AAC bitrate, default 192k).
set -e
TP="${TP:--1.5}"
AB="${AB:-192k}"   # AAC bitrate; AB=256k if the 192k encode shows a click/spike (native aac twoloop glitch seen once)
in="$1"; out="$2"
j=$(ffmpeg -hide_banner -nostats -i "$in" -af loudnorm=I=-14:TP=$TP:LRA=11:print_format=json -f null - 2>&1 | sed -n '/^{/,/^}/p')
v() { echo "$j" | sed -n "s/.*\"$1\" *: *\"\([^\"]*\)\".*/\1/p"; }
ffmpeg -hide_banner -loglevel error -y -i "$in" -c:v copy \
  -af "loudnorm=I=-14:TP=$TP:LRA=11:measured_I=$(v input_i):measured_TP=$(v input_tp):measured_LRA=$(v input_lra):measured_thresh=$(v input_thresh):offset=$(v target_offset):linear=true,aresample=48000" \
  -c:a aac -b:a $AB "$out"
ffmpeg -hide_banner -nostats -i "$out" -af ebur128=peak=true -f null - 2>&1 | grep -E "^ +(I:|Peak:)" | tr -s ' ' | tr '\n' ' '; echo
