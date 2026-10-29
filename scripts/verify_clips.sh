#!/usr/bin/env bash
set -euo pipefail
cd /home/user/ending-note
IPA="/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
OUT="work/out"
mkdir -p work/verify
declare -a CLIPS=("20％下落した高配当株リスト_Opus作成" "単元未満株とは_Opus作成" "アネスト岩田_世界シェアNo2_Opus作成")

rowfiles=()
r=0
for c in "${CLIPS[@]}"; do
  f="${OUT}/${c}.mp4"
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  # 4点: intro(1.0) / seg(4.0) / seg後半(dur-4) / cta(dur-1)
  t1=1.0; t2=4.0; t3=$(awk "BEGIN{print $dur-4}"); t4=$(awk "BEGIN{print $dur-1}")
  i=0
  for t in $t1 $t2 $t3 $t4; do
    ffmpeg -y -ss "$t" -i "$f" -frames:v 1 -q:v 2 "work/verify/r${r}_${i}.png" >/dev/null 2>&1
    i=$((i+1))
  done
  # 1x4 行
  ffmpeg -y -i "work/verify/r${r}_0.png" -i "work/verify/r${r}_1.png" -i "work/verify/r${r}_2.png" -i "work/verify/r${r}_3.png" \
    -filter_complex "[0]scale=440:248[a];[1]scale=440:248[b];[2]scale=440:248[c];[3]scale=440:248[d];[a][b][c][d]xstack=inputs=4:layout=0_0|440_0|880_0|1320_0" \
    "work/verify/row${r}.png" >/dev/null 2>&1
  rowfiles+=("work/verify/row${r}.png")
  # 音声・尺チェック
  a=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name,channels -of csv=p=0 "$f")
  echo "[$c] dur=${dur}s audio=${a}"
  r=$((r+1))
done
# 3行をvstack
ffmpeg -y -i "${rowfiles[0]}" -i "${rowfiles[1]}" -i "${rowfiles[2]}" \
  -filter_complex "[0][1][2]vstack=inputs=3" "work/verify/verify_grid.png" >/dev/null 2>&1
echo "GRID: work/verify/verify_grid.png"
ls -la work/verify/verify_grid.png
