#!/usr/bin/env bash
#
# YouTube動画アイキャッチ編集スクリプト
#
#   ・左下  : 収録日バッジ「2025/12/23 収録」(常時表示・字幕に被らない高さ)
#   ・右上  : 重要箇所のアイキャッチ(銘柄名や注目ポイントを時間指定で表示)
#
# 使い方:
#   1. 下の INPUT にダウンロードした動画ファイルのパスを設定
#   2. SEGMENTS に「開始-終了|表示テキスト」を追加(銘柄名など)
#   3. ./edit_video.sh を実行(まず ./edit_video.sh --preview 0:30 で確認推奨)
#
set -euo pipefail

# ============================== 設定 ==============================

# 入力動画(ダウンロードフォルダのファイル名に合わせて変更してください)
INPUT="${INPUT:-$HOME/Downloads/NISA.mp4}"

# 出力ファイル
OUTPUT="${OUTPUT:-$HOME/Downloads/output_edited.mp4}"

# 左下の収録日テキスト
DATE_TEXT="2025/12/23 収録"

# 右上アイキャッチ: "開始-終了|表示テキスト" (時間は MM:SS または H:MM:SS)
# ※ 2025/12/23収録回(株式分割・伊藤忠商事ほか)の実際の内容に合わせた設定です
# ※ テキストに半角コロン「:」は使わないでください(ffmpegの区切り文字と衝突します)
SEGMENTS=(
  "0:08-0:22|★ 本日のテーマ「株式分割」"
  "0:56-1:10|★ 基礎知識「株式分割とは」"
  "1:55-2:07|★ 分割後も低迷した銘柄"
  "2:13-2:27|★ 分割後に上昇した銘柄"
  "3:28-3:42|★ 伊藤忠商事 3つの盤石"
  "4:26-4:39|★ 鉄則「時間を分散して買う」"
  "4:56-5:10|★ 個別株はタイミング投資"
  "5:15-5:29|★ NISA新時代の戦略"
  "5:58-6:12|★ 失敗しない銘柄選び"
  "6:28-6:40|★ 危険な失敗に注意"
  "7:00-7:14|★ 長期投資の黄金ルール"
  "7:37-7:50|★ 焦らず・じっくり・堅実に"
  "8:03-8:17|★ オリジナル曲 JALの歌"
)

# 字幕エリアの高さ(画面下から何%を字幕用に空けるか)
SUBTITLE_ZONE_PCT=14

# ============================ フォント検出 ============================

detect_font() {
  local candidates=(
    "/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc"        # macOS
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"        # macOS
    "/System/Library/Fonts/Hiragino Sans GB.ttc"             # macOS(代替)
    "/c/Windows/Fonts/meiryob.ttc"                           # Windows (Git Bash)
    "/c/Windows/Fonts/YuGothB.ttc"                           # Windows
    "/c/Windows/Fonts/msgothic.ttc"                          # Windows
    "C:/Windows/Fonts/meiryob.ttc"                           # Windows
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"    # Linux
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc" # Linux
  )
  for f in "${candidates[@]}"; do
    [ -f "$f" ] && { echo "$f"; return; }
  done
  echo "エラー: 日本語フォントが見つかりません。FONT=/path/to/font.ttc を指定してください。" >&2
  exit 1
}
FONT="${FONT:-$(detect_font)}"

# ============================ 事前チェック ============================

command -v ffmpeg >/dev/null || { echo "ffmpeg が必要です (Mac: brew install ffmpeg / Win: winget install Gyan.FFmpeg)"; exit 1; }
[ -f "$INPUT" ] || { echo "入力動画が見つかりません: $INPUT"; echo "スクリプト冒頭の INPUT を実際のファイル名に変更してください。"; exit 1; }

# 解像度を取得してサイズを自動計算
IFS=',' read -r W H < <(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$INPUT")
echo "入力: $INPUT (${W}x${H})"

DATE_FS=$(( H / 28 ))                          # 収録日: 中位サイズ(1080pで約38px)
DATE_X=$(( W * 3 / 100 ))                      # 左端から3%
DATE_Y=$(( H - H * SUBTITLE_ZONE_PCT / 100 - DATE_FS - DATE_FS ))  # 字幕エリアの上
CATCH_FS=$(( H / 24 ))                         # アイキャッチ(720pで約30px)
MARGIN=$(( W * 3 / 100 ))

# 時間文字列(MM:SS / H:MM:SS)を秒に変換
to_sec() {
  local t="$1" IFS=':'; read -ra p <<< "$t"
  case ${#p[@]} in
    1) echo "${p[0]}";;
    2) echo "$(( 10#${p[0]} * 60 + 10#${p[1]} ))";;
    3) echo "$(( 10#${p[0]} * 3600 + 10#${p[1]} * 60 + 10#${p[2]} ))";;
  esac
}

# ============================ フィルタ構築 ============================

# 左下: 収録日バッジ(半透明黒地に白文字・常時表示)
FILTERS="drawtext=fontfile='${FONT}':text='${DATE_TEXT}':fontcolor=white:fontsize=${DATE_FS}:box=1:boxcolor=black@0.55:boxborderw=14:x=${DATE_X}:y=${DATE_Y}"

# 右上: アイキャッチ(赤地に白文字・指定区間のみフェード付き表示)
for seg in "${SEGMENTS[@]}"; do
  range="${seg%%|*}"; label="${seg#*|}"
  label="${label//:/\\:}"   # 半角コロンをエスケープ(drawtextの区切り文字対策)
  S=$(to_sec "${range%-*}"); E=$(to_sec "${range#*-}")
  FILTERS+=",drawtext=fontfile='${FONT}':text='${label}':fontcolor=white:fontsize=${CATCH_FS}"
  FILTERS+=":box=1:boxcolor=0xD32F2F@0.85:boxborderw=18"
  FILTERS+=":x=w-tw-${MARGIN}:y=$(( H * 5 / 100 ))"
  FILTERS+=":enable='between(t\\,${S}\\,${E})'"
  FILTERS+=":alpha='if(lt(t\\,${S}+0.4)\\,(t-${S})/0.4\\,if(gt(t\\,${E}-0.4)\\,(${E}-t)/0.4\\,1))'"
done

# ============================== 実行 ==============================

if [ "${1:-}" = "--preview" ]; then
  # プレビュー: 指定位置から15秒だけ高速レンダリング
  START="${2:-0:00}"
  PREVIEW_OUT="${OUTPUT%.*}_preview.mp4"
  echo "プレビュー生成中 (${START} から15秒) → $PREVIEW_OUT"
  ffmpeg -y -i "$INPUT" -ss "$(to_sec "$START")" -t 15 -vf "$FILTERS" \
    -c:v libx264 -preset ultrafast -crf 23 -c:a aac -movflags +faststart "$PREVIEW_OUT"
  echo "完了: $PREVIEW_OUT"
else
  echo "本番レンダリング中(動画の長さに応じて数分〜かかります)→ $OUTPUT"
  ffmpeg -y -i "$INPUT" -vf "$FILTERS" \
    -c:v libx264 -preset medium -crf 18 -c:a copy -movflags +faststart "$OUTPUT"
  echo "完了: $OUTPUT"
fi
