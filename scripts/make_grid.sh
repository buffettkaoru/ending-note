#!/usr/bin/env bash
set -euo pipefail
cd /home/user/ending-note
IPA="/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
TIMES=(0 30 60 90 120 150 180 210 240 270 300 330 360 390 420)
CW=426; CH=240; COLS=5

inputs=()
filter=""
i=0
for t in "${TIMES[@]}"; do
  inputs+=(-i "work/frames/ov_${t}.png")
  filter+="[${i}]scale=${CW}:${CH},drawtext=fontfile=${IPA}:text='${t}s':x=6:y=6:fontsize=24:fontcolor=yellow:box=1:boxcolor=black[v${i}];"
  i=$((i+1))
done

refs=""; layout=""
for j in $(seq 0 14); do
  refs+="[v${j}]"
  col=$(( j % COLS )); row=$(( j / COLS ))
  x=$(( col * CW )); y=$(( row * CH ))
  [ -n "$layout" ] && layout+="|"
  layout+="${x}_${y}"
done

ffmpeg -y "${inputs[@]}" -filter_complex "${filter}${refs}xstack=inputs=15:layout=${layout}" work/frames/default_overview.png
echo done
