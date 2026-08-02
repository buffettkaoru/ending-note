#!/usr/bin/env python3
"""Build a 9:16 YouTube Short from the JAL/企業年金 source video.

Layout (1080x1920):
    y    0 - 600  black band  : eye-catch (kicker + impact line)
    y  600 - 1080 video panel : source cropped to remove its burned-in captions
    y 1080 - 1920 black band  : full white large-text subtitles
"""
import subprocess, os
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
CUT_IN, CUT_OUT = 138.20, 190.90          # source seconds
INTRO = 4.0                                # thumbnail card duration
VID_Y, VID_H = 600, 480                    # video panel placement

BLACK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
BOLD  = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
REG   = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
JP_IDX = 0   # .ttc face index for the JP family

_cache = {}
def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size, index=JP_IDX)
    return _cache[key]

def tw(draw, text, f):
    return draw.textbbox((0, 0), text, font=f)[2]

# ---------------------------------------------------------------- captions
# (start, end, text) in SOURCE seconds - read off the source's burned-in captions.
# "|" marks a hand-placed line break; Japanese must not be split automatically.
CAPTIONS = [
    (138.40, 141.30, "先に500万円を|払ってくださいと"),
    (141.30, 143.00, "そうしないと"),
    (143.00, 144.70, "渡せませんと|言われたんです"),
    (144.70, 147.80, "先に500万円払うんです"),
    (147.80, 149.70, "何度も私は電話して"),
    (149.70, 151.60, "総務の人に聞きました"),
    (151.60, 153.90, "500万円|払わなかったら"),
    (153.90, 156.30, "その企業年金|もらえないんですか"),
    (156.30, 157.80, "って聞いたら"),
    (157.80, 159.40, "もらえませんと|言われてしまったんです"),
    (159.40, 163.90, "だから私の中で|30年間働いた退職金は"),
    (163.90, 166.20, "合計500万円|となりました"),
    (166.20, 168.80, "理由を聞いて|2度驚きました"),
    (168.80, 171.20, "休職していた期間|年金の"),
    (171.20, 174.10, "掛け金を払って|いなかったからです"),
    (174.10, 177.00, "休職中の未払い分を|先に"),
    (177.00, 179.90, "精算してくださいと|空白の期間に"),
    (179.90, 182.70, "なんと500万円も|払っていなかった"),
    (182.70, 185.60, "働けなかった期間の|請求書が"),
    (185.60, 188.20, "数十年の出口で|まとめて届いた"),
    (188.20, 190.90, "それが私の|500万円の正体です"),
]

# eye-catch cards: (start, end, kicker, impact-line)
EYECATCH = [
    (138.20, 147.80, "受け取る日に言われた一言", "先に500万円を払え"),
    (147.80, 159.40, "総務に電話して確認した", "払わないと|年金は出ない"),
    (159.40, 166.20, "30年間 働いた結果", "退職金 合計500万円"),
    (166.20, 174.10, "2度目の衝撃 その理由は", "休職中の 掛金未払い"),
    (174.10, 190.90, "空白の期間の請求書が", "数十年後に|まとめて届く"),
]

RIBBON = "実話｜JAL経営破綻と企業年金カット"

# ---------------------------------------------------------------- text wrap
def wrap(text, fpath, max_w, sizes):
    """Split on hand-placed '|' only, then pick the largest size that fits."""
    img = Image.new("L", (10, 10)); d = ImageDraw.Draw(img)
    lines = [p.strip() for p in text.split("|") if p.strip()]
    for size in sizes:
        f = font(fpath, size)
        if all(tw(d, l, f) <= max_w for l in lines):
            return lines, size
    return lines, sizes[-1]

# ---------------------------------------------------------------- ASS output
def ass_time(t):
    t = max(0.0, t)
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"

def esc(s):
    return s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")

def build_ass(path):
    ev = []

    def add(style, t0, t1, text, layer=0):
        # Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Text
        ev.append(f"Dialogue: {layer},{ass_time(t0 - CUT_IN)},{ass_time(t1 - CUT_IN)},"
                  f"{style},,0,0,0,{text}")

    # persistent ribbon
    add("Ribbon", CUT_IN, CUT_OUT, r"{\pos(540,84)}" + esc(RIBBON))

    # eye-catch
    for s, e, kicker, impact in EYECATCH:
        add("Kicker", s, e, r"{\pos(540,232)\fad(160,120)}" + esc(kicker))
        lines, size = wrap(impact, BLACK, 950, [96, 88, 80, 72, 64])
        body = r"\N".join(esc(l) for l in lines)
        y = 396 if len(lines) == 1 else 416
        add("Impact", s, e, rf"{{\pos(540,{y})\fs{size}\fad(160,120)}}" + body)
        # accent rule between kicker and impact line
        add("Bar", s, e, r"{\pos(540,286)\fad(160,120)\p1}"
                         r"m -150 0 l 150 0 l 150 7 l -150 7", layer=-1)

    # subtitles
    for s, e, text in CAPTIONS:
        lines, size = wrap(text, BLACK, 980, [96, 90, 84, 78, 72, 66])
        body = r"\N".join(esc(l) for l in lines)
        add("Sub", s, e, rf"{{\pos(540,1300)\fs{size}}}" + body)

    # closing CTA
    add("Cta", CUT_OUT - 4.2, CUT_OUT, r"{\pos(540,1570)\fad(300,0)}▶ 本編はチャンネルから")

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Noto Sans CJK JP Black,90,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,2,0,1,0,0,5,20,20,20,1
Style: Impact,Noto Sans CJK JP Black,96,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,3,0,1,0,0,5,20,20,20,1
Style: Kicker,Noto Sans CJK JP Black,54,&H0000D7FF,&H0000D7FF,&H00000000,&H00000000,0,0,0,0,100,100,6,0,1,0,0,5,20,20,20,1
Style: Ribbon,Noto Sans CJK JP,40,&H009C9C9C,&H009C9C9C,&H00000000,&H00000000,0,0,0,0,100,100,4,0,1,0,0,5,20,20,20,1
Style: Bar,Noto Sans CJK JP,40,&H002424E6,&H002424E6,&H002424E6,&H002424E6,0,0,0,0,100,100,0,0,1,0,0,5,0,0,0,1
Style: Cta,Noto Sans CJK JP Black,52,&H0000D7FF,&H0000D7FF,&H00000000,&H00000000,0,0,0,0,100,100,4,0,1,0,0,5,20,20,20,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Text
"""
    open(path, "w").write(header + "\n".join(ev) + "\n")
    print(f"wrote {path}: {len(ev)} events")

# ---------------------------------------------------------------- thumbnail
def fit(d, text, fpath, max_w, start):
    """Largest size <= start whose rendered width fits max_w."""
    size = start
    while size > 16 and tw(d, text, font(fpath, size)) > max_w:
        size -= 2
    return font(fpath, size), size

def build_thumb(path):
    """16:9 thumbnail card that opens the Short."""
    TW_, TH_ = 1080, 608
    im = Image.new("RGB", (TW_, TH_), (22, 22, 26))
    d = ImageDraw.Draw(im)

    # portrait on the right, with a thin white edge
    p = Image.open("portrait.png").convert("RGB").crop((0, 0, 390, 450))
    ph = TH_ - 44
    pw = int(p.width * ph / p.height)
    p = p.resize((pw, ph), Image.LANCZOS)
    px = TW_ - pw - 26
    d.rectangle([px - 3, 19, px + pw + 2, 22 + ph + 2], fill=(255, 255, 255))
    im.paste(p, (px, 22))

    col_w = px - 56 - 34          # text column, clear of the portrait

    # red 実話 badge
    fb = font(BLACK, 38)
    bw_, bh_ = tw(d, "実話", fb) + 40, 62
    d.rectangle([56, 42, 56 + bw_, 42 + bh_], fill=(200, 24, 30))
    d.text((56 + 20, 42 + bh_ // 2), "実話", font=fb, fill=(255, 255, 255), anchor="lm")
    fm, _ = fit(d, "元JAL CA・30年勤務", BOLD, col_w - bw_ - 40, 34)
    d.text((56 + bw_ + 20, 42 + bh_ // 2), "元JAL CA・30年勤務",
           font=fm, fill=(195, 195, 200), anchor="lm")

    # headline
    y = 178
    for line in ("30年働いた", "退職金は"):
        f, size = fit(d, line, BLACK, col_w, 78)
        d.text((56, y), line, font=f, fill=(255, 255, 255))
        y += size + 20
    f, size = fit(d, "500万円", BLACK, col_w, 124)
    d.text((56, y + 12), "500万円", font=f, fill=(255, 214, 0))
    d.rectangle([56, y + size + 40, 56 + col_w, y + size + 47], fill=(200, 24, 30))

    im.save(path)
    print(f"wrote {path}")
    return path

# ---------------------------------------------------------------- intro card
def build_intro(path, thumb):
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)

    d.text((W // 2, 96), "この動画で話していること",
           font=font(BOLD, 46), fill=(156, 156, 156), anchor="mm")

    for i, line in enumerate(["30年働いた退職金が", "なぜ500万円だったのか"]):
        d.text((W // 2, 220 + i * 118), line,
               font=font(BLACK, 84), fill=(255, 255, 255), anchor="mm")

    # the thumbnail, framed so it reads as a pasted-in card
    t = Image.open(thumb)
    tx, ty = (W - t.width) // 2, 470
    d.rectangle([tx - 5, ty - 5, tx + t.width + 4, ty + t.height + 4], fill=(255, 255, 255))
    im.paste(t, (tx, ty))

    d.rectangle([W // 2 - 160, 1198, W // 2 + 160, 1205], fill=(200, 24, 30))

    body = [("受け取る日に言われたのは", (255, 255, 255), 72),
            ("「先に500万円 払って」", (255, 214, 0), 80),
            ("その理由とは", (255, 255, 255), 72)]
    y = 1300
    for line, col, size in body:
        d.text((W // 2, y), line, font=font(BLACK, size), fill=col, anchor="mm")
        y += size + 46

    im.save(path)
    print(f"wrote {path}")

# ---------------------------------------------------------------- render
def render(out):
    vf = (
        "crop=1280:570:0:0,"                       # drop the source's burned-in caption band
        "scale=1080:480:flags=lanczos,"
        f"pad={W}:{H}:0:{VID_Y}:black,"
        "setsar=1,fps=30,"
        "subtitles=short.ass:fontsdir=/usr/share/fonts"
    )
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(INTRO), "-i", "intro.png",
        "-ss", str(CUT_IN), "-to", str(CUT_OUT), "-i", "src.mp4",
        "-f", "lavfi", "-t", str(INTRO), "-i", "anullsrc=r=44100:cl=stereo",
        "-filter_complex",
        f"[0:v]scale={W}:{H},setsar=1,fps=30,format=yuv420p[v0];"
        f"[1:v]{vf},format=yuv420p[v1];"
        "[v0][v1]concat=n=2:v=1:a=0[v];"
        f"[1:a]afade=t=in:st=0:d=0.20,afade=t=out:st={CUT_OUT-CUT_IN-0.5:.2f}:d=0.5[a1];"
        "[2:a][a1]concat=n=2:v=0:a=1[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "19",
        "-pix_fmt", "yuv420p", "-r", "30", "-g", "60",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-movflags", "+faststart",
        out,
    ]
    subprocess.run(cmd, check=True)
    print(f"wrote {out}")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    build_ass("short.ass")
    build_intro("intro.png", build_thumb("thumb.png"))
    render("short_9x16.mp4")
