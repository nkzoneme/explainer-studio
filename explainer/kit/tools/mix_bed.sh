#!/bin/sh
# Music bed + ambience under a rendered film, ducked by the dry voice, then mastered.
# Usage: mix_bed.sh <render.mp4> <dry_voice.mp3> <bed.wav> <out_master.mp4> [amb.wav]
# Env: DIPS="t:dur,t:dur" (from kit_cues.mjs / K.dip: bed+ambience near-silent from t to t+dur), BED=-30 (final-scale LUFS of the un-ducked bed), AMB=-42, DUCK_THR=0.04, DUCK_RATIO=3, FADE_IN=2, FADE_OUT=3
# The bed level is measured and set relative to the film's loudness BEFORE mastering (master.sh adds the offset to -14 LUFS).
set -e
IN="$1"; VO="$2"; BEDF="$3"; OUT="$4"; AMBF="$5"
BED="${BED:--30}"; AMB="${AMB:--42}"; THR="${DUCK_THR:-0.04}"; RAT="${DUCK_RATIO:-3}"; FI="${FADE_IN:-2}"; FO="${FADE_OUT:-3}"
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
li() { ffmpeg -hide_banner -nostats -i "$1" ${2:+-af "$2"} -af "${2:+$2,}ebur128" -f null - 2>&1 | sed -n '/Summary/,$p' | sed -n 's/.*I: *\(-\?[0-9.]*\) LUFS.*/\1/p'; }
PRE=$(li "$IN"); OFF=$(awk "BEGIN{print -14 - $PRE}")
FILT="aformat=channel_layouts=stereo,aresample=48000,highpass=f=50,lowpass=f=7000,atrim=0:$D"
BL=$(li "$BEDF" "$FILT"); BG=$(awk "BEGIN{print $BED - $OFF - $BL}")
echo "pre-master $PRE LUFS, master offset $OFF dB, bed filtered $BL LUFS -> gain $BG dB" >&2
FC="[1:a]anull[vk];[2:a]$FILT,volume=${BG}dB,afade=t=in:d=$FI,afade=t=out:st=$(awk "BEGIN{print $D - $FO}"):d=$FO[bed]"
if [ -n "$AMBF" ]; then
  AL=$(li "$AMBF" "$FILT"); AG=$(awk "BEGIN{print $AMB - $OFF - $AL}")
  FC="$FC;[3:a]$FILT,volume=${AG}dB,afade=t=in:d=$FI,afade=t=out:st=$(awk "BEGIN{print $D - $FO}"):d=$FO[amb];[bed][amb]amix=inputs=2:normalize=0[bg]"
else FC="$FC;[bed]anull[bg]"; fi
BGL=bg
if [ -n "$DIPS" ]; then
  EX=$(echo "$DIPS" | tr "," "\n" | awk -F: '{a=$1; b=$1+$2; printf "%s(1-0.9*clip(min((t-%s)/0.2,(%s-t)/0.1),0,1))", (NR>1?"*":""), a, b}')
  FC="$FC;[bg]volume='$EX':eval=frame[bgd]"; BGL=bgd
fi
FC="$FC;[$BGL][vk]sidechaincompress=threshold=$THR:ratio=$RAT:attack=20:release=700:makeup=1[duck];[0:a][duck]amix=inputs=2:normalize=0:duration=first[mix]"
TMP="${OUT%.mp4}_prem.mp4"
ffmpeg -hide_banner -loglevel error -y -i "$IN" -i "$VO" -i "$BEDF" ${AMBF:+-i "$AMBF"} -filter_complex "$FC" -map 0:v -map "[mix]" -c:v copy -c:a aac -b:a 256k -t "$D" "$TMP"
sh "$(dirname "$0")/master.sh" "$TMP" "$OUT"
rm -f "$TMP"
