#!/usr/bin/env bash
# default.mp4 から3本の切り抜きを生成。冒頭タイトルカード＋末尾CTAカードを前後に連結。
set -euo pipefail
cd /home/user/ending-note
IPA="/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
SRC="assets/video-src/default.mp4"
OUT="work/out"
mkdir -p "$OUT" work/parts
BG="0x10233A"       # 濃紺
ACC="0xF9A825"      # 金(アクセント)

# 共通エンコード設定(連結のため全パート統一)
enc() { echo "-c:v libx264 -preset fast -crf 20 -pix_fmt yuv420p -r 30 -c:a aac -ar 44100 -ac 2 -b:a 128k -movflags +faststart"; }

# タイトルカード生成: $1=出力 $2=大見出し行1 $3=大見出し行2 $4=秒数
make_title() {
  local out="$1" l1="$2" l2="$3" dur="$4"
  ffmpeg -y -f lavfi -i "color=c=${BG}:s=1280x720:r=30" -f lavfi -i "anullsrc=r=44100:cl=stereo" \
    -t "$dur" -filter_complex "\
[0]drawtext=fontfile=${IPA}:text='2025年4月3日  暴落の日の買い増し『答え合わせ』':fontcolor=${ACC}:fontsize=30:x=(w-tw)/2:y=130,\
drawtext=fontfile=${IPA}:text='${l1}':fontcolor=white:fontsize=66:x=(w-tw)/2:y=290,\
drawtext=fontfile=${IPA}:text='${l2}':fontcolor=white:fontsize=66:x=(w-tw)/2:y=385,\
drawtext=fontfile=${IPA}:text='バフェットかおる':fontcolor=white:fontsize=34:x=(w-tw)/2:y=560[v]" \
    -map "[v]" -map 1:a $(enc) "$out" >/dev/null 2>&1
}

# CTAカード生成: $1=出力 $2=秒数
make_cta() {
  local out="$1" dur="$2"
  ffmpeg -y -f lavfi -i "color=c=${BG}:s=1280x720:r=30" -f lavfi -i "anullsrc=r=44100:cl=stereo" \
    -t "$dur" -filter_complex "\
[0]drawtext=fontfile=${IPA}:text='▶ フル版は概要欄のリンクから':fontcolor=white:fontsize=52:x=(w-tw)/2:y=300,\
drawtext=fontfile=${IPA}:text='チャンネル登録もよろしくね':fontcolor=${ACC}:fontsize=38:x=(w-tw)/2:y=400[v]" \
    -map "[v]" -map 1:a $(enc) "$out" >/dev/null 2>&1
}

# セグメント抽出: $1=出力 $2=IN秒 $3=長さ秒
make_seg() {
  local out="$1" in="$2" dur="$3"
  ffmpeg -y -ss "$in" -i "$SRC" -t "$dur" $(enc) "$out" >/dev/null 2>&1
}

# 1クリップ生成: $1=slug $2=IN $3=長さ $4=見出し1 $5=見出し2
build() {
  local slug="$1" in="$2" dur="$3" l1="$4" l2="$5"
  echo ">> $slug  (in=${in}s dur=${dur}s)"
  make_title "work/parts/${slug}_intro.mp4" "$l1" "$l2" 2.2
  make_seg   "work/parts/${slug}_seg.mp4"   "$in" "$dur"
  make_cta   "work/parts/${slug}_cta.mp4"   2.5
  printf "file '%s'\n" "$(pwd)/work/parts/${slug}_intro.mp4" "$(pwd)/work/parts/${slug}_seg.mp4" "$(pwd)/work/parts/${slug}_cta.mp4" > "work/parts/${slug}_list.txt"
  ffmpeg -y -f concat -safe 0 -i "work/parts/${slug}_list.txt" -c copy "${OUT}/${slug}.mp4" >/dev/null 2>&1
  # durationとサイズ確認
  d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${OUT}/${slug}.mp4")
  s=$(stat -c%s "${OUT}/${slug}.mp4")
  echo "   -> ${OUT}/${slug}.mp4  dur=${d}s  size=$((s/1024/1024))MB"
}

build "20％下落した高配当株リスト_Opus作成" 0     47.6 "暴落で20％下がった" "高配当株リスト"
build "単元未満株とは_Opus作成"             334.1 49.1 "1株から買える"       "単元未満株とは"
build "アネスト岩田_世界シェアNo2_Opus作成" 383.2 48.6 "アネスト岩田は"       "世界シェアNo.2"

echo "ALL DONE"
ls -la "$OUT"/
