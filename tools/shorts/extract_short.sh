#!/usr/bin/env bash
# 指定した区間を切り出して、YouTubeショート用の縦動画(1080x1920)に変換するツール。
#
# 使い方:
#   ./extract_short.sh -i "https://www.youtube.com/watch?v=XXXX" -s 00:12:30 -e 00:13:15
#   ./extract_short.sh -i live.mp4 -s 00:12:30 -e 00:13:15 -t "NTT 配当利回り3.5%" -o ntt_short.mp4
#
# オプション:
#   -i  入力 (YouTubeのURL または ローカル動画ファイル)   ※必須
#   -s  開始時刻 HH:MM:SS                                  ※必須
#   -e  終了時刻 HH:MM:SS                                  ※必須
#   -t  画面上部に載せるタイトル文字 (例: "NTT 利回り3.5%")
#   -o  出力ファイル名 (既定: short.mp4)
#   -m  変換モード: blur(既定・横動画の上下を背景ぼかしで埋める) / crop(中央を切り抜き)
#
# 必要なもの: ffmpeg, (URLを使う場合) yt-dlp
set -euo pipefail

IN="" START="" END="" TITLE="" OUT="short.mp4" MODE="blur"
while getopts "i:s:e:t:o:m:" opt; do
  case "$opt" in
    i) IN="$OPTARG" ;;
    s) START="$OPTARG" ;;
    e) END="$OPTARG" ;;
    t) TITLE="$OPTARG" ;;
    o) OUT="$OPTARG" ;;
    m) MODE="$OPTARG" ;;
    *) exit 1 ;;
  esac
done
if [ -z "$IN" ] || [ -z "$START" ] || [ -z "$END" ]; then
  grep '^#' "$0" | head -18
  exit 1
fi

to_sec() { echo "$1" | awk -F: '{ if (NF==3) print $1*3600+$2*60+$3; else if (NF==2) print $1*60+$2; else print $1 }'; }
DUR=$(( $(to_sec "$END") - $(to_sec "$START") ))
if [ "$DUR" -le 0 ]; then echo "エラー: 終了時刻が開始時刻より前です"; exit 1; fi
if [ "$DUR" -gt 60 ]; then
  echo "注意: ${DUR}秒あります。ショートは最大3分ですが、最初の1本は60秒以内が伸びやすいです。"
fi

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

SRC="$IN"
case "$IN" in
  http*)
    echo "== 指定区間のみダウンロード中... =="
    yt-dlp --no-warnings -f "bv*[height<=1080]+ba/b" \
      --download-sections "*${START}-${END}" --force-keyframes-at-cuts \
      -o "$WORK/clip.%(ext)s" "$IN"
    SRC=$(ls "$WORK"/clip.* | head -1)
    CUT=(-i "$SRC")   # ダウンロード時に切り出し済み
    ;;
  *)
    if [ ! -f "$IN" ]; then echo "エラー: ファイルが見つかりません: $IN"; exit 1; fi
    CUT=(-ss "$START" -to "$END" -i "$SRC")
    ;;
esac

# 縦型 1080x1920 へ変換
if [ "$MODE" = "crop" ]; then
  VF="crop=ih*9/16:ih,scale=1080:1920"
else
  VF="split[bg][fg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20:5[bgb];[fg]scale=1080:-2[fgs];[bgb][fgs]overlay=(W-w)/2:(H-h)/2"
fi

# タイトル文字 (日本語対応フォントが見つかった場合のみ)
if [ -n "$TITLE" ]; then
  FONT=$(fc-list :lang=ja --format '%{file}\n' 2>/dev/null | grep -iE 'bold|black|heavy' | head -1)
  [ -z "$FONT" ] && FONT=$(fc-list :lang=ja --format '%{file}\n' 2>/dev/null | head -1)
  if [ -n "$FONT" ] && [ -f "$FONT" ]; then
    printf '%s' "$TITLE" > "$WORK/title.txt"
    VF="$VF,drawtext=expansion=none:fontfile='$FONT':textfile='$WORK/title.txt':fontsize=72:fontcolor=white:borderw=6:bordercolor=black:x=(w-text_w)/2:y=140"
  else
    echo "注意: 日本語フォントが見つからないためタイトル文字はスキップします。"
  fi
fi

echo "== 変換中 (${DUR}秒 / モード: $MODE) =="
ffmpeg -y -hide_banner -loglevel warning "${CUT[@]}" \
  -vf "$VF" -r 30 \
  -af "loudnorm=I=-14:TP=-1.5:LRA=11" \
  -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart \
  "$OUT"

echo ""
echo "完成: $OUT (${DUR}秒, 1080x1920)"
echo "タイトルに #Shorts を入れるか、そのままアップすればショートとして認識されます。"
