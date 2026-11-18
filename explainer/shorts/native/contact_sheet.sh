#!/bin/sh
# 1 fps contact sheet of a vertical Short with the Shorts UI zones OUTLINED (red: top icons, bottom 20 %, right 12 % action
# column below mid-height; orange: where the overlay reaches when a Related-video pill is shown).
# Usage: sh contact_sheet.sh <short.mp4> [out.jpg]
in="$1"; out="${2:-${1%.mp4}_contact.jpg}"
n=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in" | awk '{printf "%d", $1+1}'); rows=$(( (n + 7) / 8 ))
ffmpeg -hide_banner -loglevel error -y -i "$in" -vf "fps=1,drawbox=x=0:y=1536:w=1080:h=384:color=red@0.9:t=8,drawbox=x=950:y=960:w=130:h=576:color=red@0.9:t=8,drawbox=x=0:y=1400:w=1080:h=136:color=orange@0.9:t=6,drawbox=x=0:y=0:w=1080:h=160:color=red@0.9:t=6,drawtext=fontfile=/usr/share/fonts/noto/NotoSans-Black.ttf:text='%{eif\:t\:d}s':x=20:y=1560:fontsize=90:fontcolor=white:box=1:boxcolor=black@0.6,scale=270:480,tile=8x${rows}:padding=6:color=black" -frames:v 1 "$out"
echo "contact sheet: $out"
