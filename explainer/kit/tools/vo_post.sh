#!/bin/sh
# Light voice post for NEW films. Timings do not change (duration is forced equal to the input).
# Usage: vo_post.sh in.mp3 out.mp3
# Chain: high-pass 70 Hz -> de-ess -> gentle EQ (-1.5 dB mud at 250 Hz, +2 dB presence at 4 kHz) -> 2.5:1 compression
#        -> small room (ROOM % wet, default 6; ROOM=0 disables) -> limiter at -1.5 dBFS.
# Env: HPF=70  PRES=2 (dB at 4 kHz)  MUD=-1.5  DEESS=0.4 (deesser intensity 0..1)  RATIO=2.5  THRESH=-20 (dB)  ROOM=6  MAKEUP=2 (dB)  LIMIT=-1.5
# Run it on the TTS file BEFORE vo_build.py (words.json is unchanged). Operator's ears decide: re-run with PRES=1 / ROOM=0 if harsh.
set -e
IN="$1"; OUT="$2"
[ -n "$IN" ] && [ -n "$OUT" ] || { sed -n '2,9p' "$0"; exit 2; }
HPF="${HPF:-70}"; PRES="${PRES:-2}"; MUD="${MUD:--1.5}"; DEESS="${DEESS:-0.4}"; RATIO="${RATIO:-2.5}"; THRESH="${THRESH:--20}"; ROOM="${ROOM:-6}"; MAKEUP="${MAKEUP:-2}"; LIMIT="${LIMIT:--1.5}"
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$IN")
SR=$(ffprobe -v error -select_streams a:0 -show_entries stream=sample_rate -of csv=p=0 "$IN")
LIM=$(awk "BEGIN{printf \"%.4f\", 10^($LIMIT/20)}"); TH=$(awk "BEGIN{printf \"%.5f\", 10^($THRESH/20)}"); WET=$(awk "BEGIN{printf \"%.3f\", $ROOM/100}")
CHAIN="highpass=f=$HPF,deesser=i=$DEESS:m=0.5:f=0.5,equalizer=f=250:t=q:w=1.0:g=$MUD,equalizer=f=4000:t=q:w=0.9:g=$PRES,acompressor=threshold=$TH:ratio=$RATIO:attack=12:release=180:makeup=$MAKEUP"
if [ "$ROOM" = "0" ]; then
  FC="[0:a]$CHAIN,alimiter=limit=$LIM:level=disabled:attack=5:release=60,atrim=0:$D,asetpts=N/SR/TB[o]"
else
  FC="[0:a]$CHAIN,asplit[d][w];[w]aecho=1:1:23|41|67:0.5|0.35|0.22,lowpass=f=6000[wr];[d][wr]amix=inputs=2:weights='1 $WET':normalize=0,alimiter=limit=$LIM:level=disabled:attack=5:release=60,atrim=0:$D,asetpts=N/SR/TB[o]"
fi
ffmpeg -hide_banner -loglevel error -y -i "$IN" -filter_complex "$FC" -map "[o]" -ar "$SR" -c:a libmp3lame -q:a 2 "$OUT"
A=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$OUT")
echo "vo_post: $IN -> $OUT  (in ${D}s, out ${A}s, hpf $HPF Hz, presence +$PRES dB, ratio $RATIO:1, room ${ROOM}% wet)"
