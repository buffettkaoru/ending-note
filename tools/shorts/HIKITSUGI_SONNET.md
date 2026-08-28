# 引き継ぎ書【Sonnet用】バフェットかおる「答え合わせ切り抜き動画」制作・完全手順版

あなた（Claude Sonnet）はこの文書のとおりに作業すれば、前任と同じ品質の
切り抜き動画を作れます。**この文書は上から順に実行する手順書です。**
自分の判断で手順を省略しないでください。特に「☑チェックリスト」と
「⛔絶対禁止」は必ず守ってください。判断に迷う場面の答えは §10 の判断表にあります。

---

## 0. 最初に必ずやること

1. この文書を最後まで読む
2. `apt-get install -y ffmpeg fonts-noto-cjk` を実行（環境に無い場合）
3. 依頼主・目的を理解する：
   - 依頼主=投資系YouTuber「バフェットかおる」さん（登録者27,500人・毎晩21時ライブ・
     資産1.5億円超・高配当株の長期投資）。ITは得意でない。スクショ提供は得意
   - 作るもの=**過去ライブの切り抜き＋「答え合わせアイキャッチ」**
     （当時の株価→現在の株価・配当・本人の実額を画面に焼き込み、
     「この人当たってる」と2秒でわかる動画）
   - 発信スタンス=自慢でなく事実。概算と明記。「参考にしてください」の姿勢。
     負けた銘柄も隠さない

## 1. 環境の制約（変更不可の前提）

- この環境からは **YouTube・Googleドライブに接続できない**（プロキシ403）
- 使えるのは github.com / objects.githubusercontent.com / WebSearch のみ
- **WebSearchで得た株価は使わない**（古い値が混ざる）。ユーザーのSBIスクショが正
- ユーザーのMacにローカルClaude Codeあり。YouTubeからのダウンロードはそちらに依頼可

## 2. 動画の受け取り手順

ユーザーへの案内文（コピペして使う）:
```
動画をこちらに送る手順です：
1. https://github.com/buffettkaoru/ending-note/releases/new を開く
2. 「Choose a tag」をクリック → 好きな名前（例: video1）を入力 →
   「+ Create new tag: video1」をクリック
3. 点線の枠に動画ファイルをドラッグ＆ドロップ → バーが100%になるまで待つ
4. 緑色の「Publish release」ボタンを必ずクリック（これを押さないと届きません）
5. このチャットで「入れた」と一言ください
```

届いたかの確認コマンド:
```bash
curl -sSL -m 30 --cacert /root/.ccr/ca-bundle.crt \
  "https://github.com/buffettkaoru/ending-note/releases/expanded_assets/<タグ名>" \
  | grep -oE 'releases/download/[^"]+'
```
※日本語タグはURLエンコード（例:「動画」→ %E5%8B%95%E7%94%BB）
※何も出ない場合=まだPublishされていない。上の手順4を再案内する

ダウンロード:
```bash
curl -sSL -m 570 --cacert /root/.ccr/ca-bundle.crt -o video.mp4 \
  "https://github.com/buffettkaoru/ending-note/releases/download/<タグ>/<ファイル名>"
ffprobe -v error -show_entries format=duration,size \
  -show_entries stream=codec_type,width,height -of default=noprint_wrappers=1 video.mp4
```

待機中の監視: send_later で60分ごとにreleasesを確認。変化がなければユーザーに
通知せず静かに再スケジュール。トリガー本文に「今の状況と次にやること」を毎回書く。

## 3. フレームスキャン手順（動画の中身を知る）

```bash
FONT=$(fc-list :lang=ja --format '%{file}\n' | grep -i bold | head -1)
# 間隔の決め方: 動画60分超→180秒 / 10〜60分→60秒 / 10分以下→30秒
mkdir -p frames
for i in $(seq 0 19); do t=$((i*180+60)); \
  ffmpeg -y -hide_banner -loglevel error -ss $t -i video.mp4 -frames:v 1 \
  -vf "scale=400:225,drawtext=fontfile='$FONT':text='$((t/60))m$((t%60))s':fontsize=24:fontcolor=yellow:borderw=3:bordercolor=black:x=8:y=8" \
  frames/f$(printf %02d $i).png; done
ffmpeg -y -hide_banner -loglevel error $(ls frames/f*.png | while read f; do echo -n " -i $f"; done) \
  -filter_complex "concat=n=20:v=1:a=0[t];[t]tile=4x5:padding=4:color=black" -frames:v 1 sheet.png
```
できた sheet.png を **Readツールで必ず自分の目で見る**。探すもの：
- ☑ 銘柄名・銘柄コードが映る画面（スライド・証券画面・四季報）
- ☑ **当時の株価と日付が同時に映る画面**（SBI画面の右上に日時が出る。答え合わせの証拠）
- ☑ 実際の売買・入金画面
- ☑ 話題の切り替わり位置（切り抜き範囲の候補）
見つけた内容をタイムスタンプ付きでユーザーに報告する。

## 4. 数字の集め方（この順番を守る）

| 必要な数字 | 入手方法 |
|---|---|
| 当時の株価 | ①動画内の画面から読む（最優先・日付付きなら最強） ②ユーザーにスクショ依頼 ③チャート読み取りで「約」を付ける |
| 現在の株価 | ユーザーのSBIスクショ（現在値の画面）。**WebSearch値は禁止** |
| 配当の推移 | ユーザーのIR BANK風スクショ（年度別の一株配当と増配率が並ぶ画面） |
| 保有株数 | ユーザーのSBI保有証券一覧スクショ |

ユーザーへの依頼文（コピペ可）:
```
アイキャッチ用に、SBI証券のスクショをお願いします：
1. ○○（銘柄名・コード）の現在値が見える画面
2. ○○の配当推移（IR BANKの一株配当のページ）
3. 保有証券一覧（株数がわかる画面）
```

**検算（省略禁止）**: すべての計算をpython3で行い、結果の表をユーザーに見せる。
```bash
python3 - <<'EOF'
rows = [  # (銘柄, 当時株価, 現在株価, 株数, 配当2年分/株)
 ("三菱UFJ", 1983, 3326, 636, 64+86),
]
tu=td=0
for n,a,b,s,d in rows:
    up=(b-a)*s; dv=d*s; tu+=up; td+=dv
    print(f"{n}: +{(b/a-1)*100:.1f}%  値上がり{up:,.0f}円  配当{dv:,.0f}円")
print(f"値上がり計 {tu:,.0f} / 配当計 {td:,.0f} / 合計 {tu+td:,.0f}")
EOF
```
配当2年分 = 直近2期の実績合計（実績が無い銘柄はユーザー指定の仮定を使い、概要欄に注記）。

## 5. 切り抜き手順

1. 切り抜き範囲を決める（優先順: ①銘柄を一気に説明する区間 ②実際の売買シーン
   ③ユーザーがアナリティクスのスクショをくれたらチャットが盛り上がった時間帯）。
   通常動画は**8分超**にする（ミッドロール広告のため）。ショートは60秒以内
2. 境界を無音にスナップ:
```bash
ffmpeg -hide_banner -ss <候補秒-20> -t 40 -i video.mp4 -vn \
  -af silencedetect=noise=-30dB:d=0.4 -f null - 2>&1 | grep silence
```
   無音区間（silence_start〜end）の中の秒を開始・終了に採用する
3. 境界前後のフレームを抽出して、スライドの切り替わりと合っているか目で確認
4. 無劣化カット（**この段階ではアイキャッチを焼き込まない**）:
```bash
ffmpeg -y -ss <開始秒> -i video.mp4 -t <長さ秒> -c copy -movflags +faststart cut.mp4
```

## 6. アイキャッチ焼き込み手順

### 配置ルール（固定）
- **左上** = 動画の正体：赤帯バッジ＋「映像:いつのライブか／作成:今日の日付」＋
  金文字の後日談（例:バフェット出資）
- **右上** = 数字の証拠：黄色見出し＋緑の銘柄行（当時→現在 +○%）＋
  金色のお金の行（本人の値上がり・配当・合計）
- **下部 = 何も置かない**（⛔本編の字幕と衝突するため禁止）
- 古い焼き込みを隠す場合のみ、不透明パネル(drawbox @0.97)を先に敷く

### 色コード（固定）
赤=0xCC0000@0.95 / 黄=yellow@0.95(黒文字) / 緑=0x0B6E2F@0.9 /
金=0xFFC93C@0.95(黒文字) / 金文字=0xFFD24A / 灰(負け銘柄)=0x666666 /
背景パネル=0x101018@0.97

### 手順
1. 文言をテキストファイルに書く（**直書き禁止**。% & : が化けるため）:
```bash
mkdir -p txt
printf '1年半前の銀行株予想 答え合わせ' > txt/L1.txt
printf '映像:2025年2月17日ライブ／作成:<今日の日付>' > txt/L2.txt
printf 'この後バフェットが東京海上に2,874億円出資' > txt/L3.txt
printf '→株価は急騰し上場来高値に' > txt/L4.txt
printf '銀行・保険株の答え合わせ' > txt/R0.txt
printf '三菱UFJ 1,983→3,326円 +68%%' > txt/R1.txt   # 銘柄行は R1〜R4
printf '私の保有分：値上がり +284万円' > txt/R5.txt
printf '配当2年分 +30万円' > txt/R6.txt
printf '合計 +314万円に' > txt/R7.txt
```
2. 焼き込み（720p用の実寸。1080pなら全数値を1.5倍）:
```bash
FONT=$(fc-list :lang=ja --format '%{file}\n' | grep -i bold | head -1)
D="fontfile='$FONT':expansion=none:fontcolor=white"
ffmpeg -y -i cut.mp4 -vf "\
drawbox=x=10:y=10:w=560:h=200:color=0x101018@0.97:t=fill,\
drawbox=x=iw-480:y=10:w=470:h=380:color=0x101018@0.97:t=fill,\
drawtext=$D:textfile=txt/L1.txt:fontsize=31:box=1:boxcolor=0xCC0000@0.95:boxborderw=9:x=27:y=24,\
drawtext=$D:textfile=txt/L2.txt:fontsize=21:x=27:y=82,\
drawtext=$D:textfile=txt/L3.txt:fontsize=23:fontcolor=0xFFD24A:x=27:y=122,\
drawtext=$D:textfile=txt/L4.txt:fontsize=23:fontcolor=0xFFD24A:x=27:y=158,\
drawtext=$D:textfile=txt/R0.txt:fontsize=28:fontcolor=black:box=1:boxcolor=yellow@0.95:boxborderw=8:x=w-text_w-24:y=22,\
drawtext=$D:textfile=txt/R1.txt:fontsize=26:box=1:boxcolor=0x0B6E2F@0.9:boxborderw=7:x=w-text_w-24:y=70,\
drawtext=$D:textfile=txt/R2.txt:fontsize=26:box=1:boxcolor=0x0B6E2F@0.9:boxborderw=7:x=w-text_w-24:y=113,\
drawtext=$D:textfile=txt/R3.txt:fontsize=26:box=1:boxcolor=0x0B6E2F@0.9:boxborderw=7:x=w-text_w-24:y=156,\
drawtext=$D:textfile=txt/R4.txt:fontsize=26:box=1:boxcolor=0x0B6E2F@0.9:boxborderw=7:x=w-text_w-24:y=199,\
drawtext=$D:textfile=txt/R5.txt:fontsize=25:fontcolor=black:box=1:boxcolor=0xFFC93C@0.95:boxborderw=7:x=w-text_w-24:y=252,\
drawtext=$D:textfile=txt/R6.txt:fontsize=25:fontcolor=black:box=1:boxcolor=0xFFC93C@0.95:boxborderw=7:x=w-text_w-24:y=294,\
drawtext=$D:textfile=txt/R7.txt:fontsize=27:fontcolor=black:box=1:boxcolor=0xFFC93C@0.98:boxborderw=8:x=w-text_w-24:y=334" \
-c:v libx264 -preset veryfast -crf 21 -pix_fmt yuv420p -c:a copy -movflags +faststart final.mp4
```
（銘柄が2つなら R3/R4行を削る。行のy座標は43〜48px間隔で詰める）
3. 縦型ショートが必要な場合は同フォルダの `extract_short.sh` を使う

### ☑焼き込み後チェックリスト（全部やってから納品）
- [ ] 冒頭・中間・末尾の3フレームを抽出してReadで目視した
- [ ] 誤字がない・数字が検算表と一致している
- [ ] 本編の字幕・テロップがアイキャッチに隠されていない
- [ ] 「映像の日付」が正しい（作成日と混同していない）
- [ ] ffprobeで長さが想定どおり・ファイルが100MB未満
- [ ] 概算の数字に「約」が付いている

## 7. 納品手順

⛔SendUserFileのカードはユーザーが開けないことがある。**必ずGitHub rawリンク方式**：
```bash
mkdir -p /home/user/ending-note/deliverables
cp final.mp4 /home/user/ending-note/deliverables/<ASCII名>.mp4   # 日本語名禁止・100MB未満
cd /home/user/ending-note && git add deliverables && git commit -m "納品用: <内容>（一時配置）" \
  && git push -u origin <作業ブランチ>
curl -sSL -o /dev/null -m 30 -w "%{http_code}\n" --cacert /root/.ccr/ca-bundle.crt \
  "https://github.com/buffettkaoru/ending-note/raw/<ブランチ>/deliverables/<名前>.mp4" -r 0-1000
# 206ならOK。404なら15秒待って再確認
```
ユーザーには「このリンクをクリックするとダウンロードフォルダに保存されます」と案内。
**「できた」の返事をもらったら必ず `git rm` でお掃除コミット**。
リリースの素材動画も削除を勧める（公開状態のため）。

納品メッセージに含めるもの: ①リンク ②画面に入れた内容の説明 ③検算の表
④タイトル・概要欄・サムネ文言（§8のテンプレ）

## 8. タイトル・概要欄・サムネのテンプレ

**タイトル**: 「【答え合わせ】<いつ>に<何をした>結果→<実額 or %>【<配信日>ライブ】」

**概要欄**（<>を埋めて使う）:
```
<配信日>のライブ配信で「<当時の主張>」とお話しした回の答え合わせです。
（この動画の作成日：<今日>）

📈 株価の答え合わせ（<配信日> → <株価の時点>）
・<銘柄>　<当時>円 → <現在>円（+<X>%）
（銘柄ぶん繰り返し）

💰 配当も増配が続いています
・<銘柄> <前期>円→<今期>円（銘柄ぶん）

🧮 私の保有分では、値上がり約<X>万円＋配当約<Y>万円＝合計約<Z>万円のプラスになりました。

【計算と投資方法についての注記】
※金額・騰落率はすべて概算です（株価は<時点>時点）。
※保有株数は現在のものです。私は株価が割安になったタイミングで数株ずつ追加投資を
続けているため、実際の損益とは差があります。

【出典・参考情報】
動画内で視聴・引用しているのは、松井証券公式YouTubeチャンネルです。
▶ https://www.youtube.com/channel/UCS5dVIXy8SYcIMWRmEI-_3A
そのほか、ダイヤモンドZAiなどの経済メディア、ネット上の公開情報を参考にしています。

【お願い】
私の考えがすべて正しいわけではありません。「こういう見方もあるんだ」と参考に
していただく姿勢で発信しています。投資は必ずご自身の判断と責任でお願いします。

🔴 毎晩21時ごろからライブ配信中。
#高配当株 #答え合わせ #新NISA #配当金生活 #増配
```

**サムネ文字**: 特大数字1つ（例「+314万円」）／赤帯「答え合わせ」／
日付「<配信日>→<現在>」／隅に小さく「概算」

## 9. ⛔絶対禁止（すべて実際の失敗が由来）

1. ⛔ 編集用素材にアイキャッチを焼き込む（再編集で字幕が復元不能になった事故あり）
2. ⛔ 画面下部にオーバーレイを置く（本編の字幕・テロップと衝突する）
3. ⛔ 映像の日付欄に作成日・編集日を書く（「映像がいつか」だけを書く）
4. ⛔ 暗算・検算なしで金額を画面に載せる
5. ⛔ WebSearchの株価をそのまま画面に載せる（ユーザーのスクショが正）
6. ⛔ 銘柄コードの取り違え（8306三菱UFJ / 8316三井住友FG / 8309三井住友トラストGは別会社）
7. ⛔ 納品後のお掃除（deliverables削除）を忘れる
8. ⛔ モデルIDをコミット・PR・動画に書く

## 10. 判断に迷ったときの表

| 状況 | やること |
|---|---|
| リリースに動画が見えない | Publishボタン未押下の可能性→§2の案内文を再送 |
| Studioでダウンロードできないと言われた | 著作権申し立て or 回数制限→MacのローカルClaude Codeにyt-dlpを依頼する案内 |
| 数字が2つのソースで食い違う | ユーザーのスクショ＞映像内画面＞WebSearch の順で採用し、採用根拠を伝える |
| 当時の株価がどこにも無い | チャートから読み「約」を付け、合計は「約○万円」で丸めて誤差を吸収。ユーザーに仮値でよいか確認 |
| ユーザーが操作で詰まった | 「その画面のスクショを送ってください」と言う |
| 大きな方針が2択になった | 案A/案Bとして提示し選んでもらう（勝手に選ばない） |
| ユーザーから返事がない | send_laterで60分ごとに静かに監視。催促は1回まで |

## 11. 実績データと現在の状況（2026/7/5時点）

確定済みの答え合わせ数字は `HIKITSUGI_OPUS.md` §8 を参照（コピー元として使える）。

**進行中**: 「20%ルール」回（2025/4/3・77分・リリース「動画」タグ 20.2.mp4）の
答え合わせ制作。スキャン済みの見どころ: 12:36 買い増し9銘柄リスト / 16:28 保有資産
1億665万円の管理ツール画面 / 24:12 347万円入金の実画面 / 28:04 アネスト岩田 当時1,102円。
待ち: オカムラ(7994)・アネスト岩田(6381)の現在値スクショ（竹本容器869円は確認済み）。
未処理ネタ: NISA.mp4（伊藤忠1:5分割）、旧チャンネル「NTTの株は買いか」(2,140回)。
