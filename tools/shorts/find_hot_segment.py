#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""動画の中から「一番視聴されている銘柄紹介の箇所」を自動で見つけるツール。

2つの情報源を組み合わせて、ショート動画に切り出すべき区間を提案します。

  1. YouTube の「最も再生された箇所」ヒートマップ（Most Replayed）
     ※再生回数が少ない動画にはヒートマップが付かないため、その場合は 2 だけで判定
  2. 日本語の自動字幕から「銘柄」「配当」「利回り」などのキーワードが
     集中している区間

使い方:
    python3 find_hot_segment.py "https://www.youtube.com/watch?v=XXXX"
    python3 find_hot_segment.py "URL" --duration 45 --keywords "銘柄,配当,NTT"

必要なもの: yt-dlp (pip install yt-dlp)
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.request

DEFAULT_KEYWORDS = [
    "銘柄", "配当", "利回り", "高配当", "増配", "株価", "決算",
    "買い", "買った", "保有", "おすすめ", "紹介", "優待",
]


def hms(seconds):
    seconds = int(round(seconds))
    return "%02d:%02d:%02d" % (seconds // 3600, (seconds % 3600) // 60, seconds % 60)


def load_info(args):
    """yt-dlp で動画情報(JSON)を取得。--info-json 指定時はファイルから読む。"""
    if args.info_json:
        with open(args.info_json, encoding="utf-8") as f:
            return json.load(f)
    try:
        out = subprocess.run(
            ["yt-dlp", "-J", "--no-warnings", args.url],
            capture_output=True, text=True, check=True,
        ).stdout
    except FileNotFoundError:
        sys.exit("yt-dlp が見つかりません。`pip install yt-dlp` でインストールしてください。")
    except subprocess.CalledProcessError as e:
        sys.exit("動画情報の取得に失敗しました:\n" + e.stderr.strip())
    return json.loads(out)


def load_caption_events(info, args):
    """日本語の自動字幕(json3)を取得して [(開始秒, テキスト), ...] を返す。"""
    if args.subs_file:
        with open(args.subs_file, encoding="utf-8") as f:
            data = json.load(f)
    else:
        tracks = (info.get("automatic_captions") or {}).get("ja") or \
                 (info.get("subtitles") or {}).get("ja") or []
        url = next((t["url"] for t in tracks if t.get("ext") == "json3"), None)
        if not url:
            return []
        try:
            with urllib.request.urlopen(url, timeout=30) as r:
                data = json.load(r)
        except Exception as e:
            print("字幕の取得に失敗しました(%s)。ヒートマップのみで判定します。" % e)
            return []
    events = []
    for ev in data.get("events", []):
        text = "".join(seg.get("utf8", "") for seg in ev.get("segs", [])).strip()
        if text and "tStartMs" in ev:
            events.append((ev["tStartMs"] / 1000.0, text))
    return events


def keyword_hits(events, keywords):
    """字幕からキーワード出現位置 [(秒, キーワード)] を抽出。"""
    hits = []
    for t, text in events:
        for kw in keywords:
            if kw and kw in text:
                hits.append((t, kw))
    return hits


def score_windows(duration_total, win, heatmap, hits, step=5):
    """動画全体を step 秒刻みでずらした win 秒の窓ごとにスコアを付ける。"""
    windows = []
    t = 0
    while t < max(duration_total - win, 1):
        heat = 0.0
        if heatmap:
            vals = [h["value"] for h in heatmap
                    if h["start_time"] < t + win and h["end_time"] > t]
            heat = sum(vals) / len(vals) if vals else 0.0
        in_win = [(ht, kw) for ht, kw in hits if t <= ht < t + win]
        # ヒートマップ(0〜1)とキーワード密度を同じ重みで合算
        kw_score = min(len(in_win) / 5.0, 1.0)
        windows.append({
            "start": t, "end": t + win,
            "score": heat + kw_score,
            "heat": heat,
            "keywords": sorted({kw for _, kw in in_win}),
        })
        t += step
    # スコア順に、重なり合う窓を除いて上位を返す
    windows.sort(key=lambda w: w["score"], reverse=True)
    picked = []
    for w in windows:
        if all(w["end"] <= p["start"] or w["start"] >= p["end"] for p in picked):
            picked.append(w)
        if len(picked) >= 5:
            break
    return picked


def main():
    p = argparse.ArgumentParser(description="銘柄紹介の山場を自動検出してショート切り出し区間を提案")
    p.add_argument("url", help="YouTube動画のURL")
    p.add_argument("--duration", type=int, default=45, help="切り出す秒数 (既定: 45)")
    p.add_argument("--keywords", help="カンマ区切りの検索キーワード（既定の銘柄系ワードに追加）")
    p.add_argument("--info-json", help="(テスト用) yt-dlp -J の出力ファイル")
    p.add_argument("--subs-file", help="(テスト用) json3字幕ファイル")
    args = p.parse_args()

    keywords = list(DEFAULT_KEYWORDS)
    if args.keywords:
        keywords += [k.strip() for k in args.keywords.split(",") if k.strip()]

    info = load_info(args)
    total = info.get("duration") or 0
    if not total:
        sys.exit("動画の長さが取得できませんでした。")
    heatmap = info.get("heatmap") or []
    events = load_caption_events(info, args)
    hits = keyword_hits(events, keywords)

    print("動画: %s (%s)" % (info.get("title", "?"), hms(total)))
    print("ヒートマップ: %s / 字幕キーワードヒット: %d件" %
          ("あり" if heatmap else "なし（再生数が少ない動画には付きません）", len(hits)))
    if not heatmap and not hits:
        sys.exit("判定材料がありません。--keywords で動画内の銘柄名を指定してみてください。")

    print("\n=== おすすめの切り出し区間 (%d秒) ===" % args.duration)
    for i, w in enumerate(score_windows(total, args.duration, heatmap, hits), 1):
        print("\n%d位: %s 〜 %s  (スコア %.2f%s)" % (
            i, hms(w["start"]), hms(w["end"]), w["score"],
            ", 再生ヒート %.2f" % w["heat"] if heatmap else ""))
        if w["keywords"]:
            print("   キーワード: " + " ".join(w["keywords"]))
        print("   切り出しコマンド:")
        print('   ./extract_short.sh -i "%s" -s %s -e %s' %
              (args.url, hms(w["start"]), hms(w["end"])))


if __name__ == "__main__":
    main()
