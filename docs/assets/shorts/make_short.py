#!/usr/bin/env python3
"""Build a 9:16 YouTube Short (and its thumbnails) from a source video + a JSON config.

This is the generalised version of `build_short.py` (which is hard-wired to the
JAL/企業年金 video). Everything that changes per video lives in a config file:

    python3 make_short.py configs/takahaitou-hajimekata.json              # full render
    python3 make_short.py configs/takahaitou-hajimekata.json --thumbs-only # thumbnails only

Layout (1080x1920), same design language as the JAL short:

    y    0 -  600  black band  : eye-catch (kicker + impact line)
    y  600 - 1080  video panel : source, cropped so its burned-in captions are dropped
    y 1080 - 1920  black band  : large white subtitles

Requirements: ffmpeg, Pillow, fonts-noto-cjk.
"""
import argparse
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920

BLACK = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
JP_IDX = 0  # .ttc face index for the JP family

RED = (200, 24, 30)
YELLOW = (255, 214, 0)
WHITE = (255, 255, 255)
GREY = (170, 170, 176)
BG = (22, 22, 26)

COLORS = {"white": WHITE, "yellow": YELLOW, "red": RED, "grey": GREY}

_font_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _font_cache:
        _font_cache[key] = ImageFont.truetype(path, size, index=JP_IDX)
    return _font_cache[key]


def tw(draw, text, f):
    return draw.textbbox((0, 0), text, font=f)[2]


def fit(d, text, fpath, max_w, start, floor=18):
    """Largest size <= start whose rendered width fits max_w."""
    size = start
    while size > floor and tw(d, text, font(fpath, size)) > max_w:
        size -= 2
    return font(fpath, size), size


def wrap(text, fpath, max_w, sizes):
    """Split on hand-placed '|' only, then pick the largest size that fits.

    Japanese must never be line-broken automatically - a break in the wrong
    place changes how the sentence reads, so the copy carries its own breaks.
    """
    img = Image.new("L", (10, 10))
    d = ImageDraw.Draw(img)
    lines = [p.strip() for p in text.split("|") if p.strip()]
    for size in sizes:
        f = font(fpath, size)
        if all(tw(d, l, f) <= max_w for l in lines):
            return lines, size
    return lines, sizes[-1]


# ---------------------------------------------------------------- ASS output
def ass_time(t):
    t = max(0.0, t)
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def esc(s):
    return s.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")


def build_ass(cfg, path):
    cut_in, cut_out = cfg["cut_in"], cfg["cut_out"]
    ev = []

    def add(style, t0, t1, text, layer=0):
        # Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Text
        ev.append(
            f"Dialogue: {layer},{ass_time(t0 - cut_in)},{ass_time(t1 - cut_in)},"
            f"{style},,0,0,0,{text}"
        )

    if cfg.get("ribbon"):
        add("Ribbon", cut_in, cut_out, r"{\pos(540,84)}" + esc(cfg["ribbon"]))

    for s, e, kicker, impact in cfg.get("eyecatch", []):
        add("Kicker", s, e, r"{\pos(540,232)\fad(160,120)}" + esc(kicker))
        lines, size = wrap(impact, BLACK, 950, [96, 88, 80, 72, 64])
        body = r"\N".join(esc(l) for l in lines)
        y = 396 if len(lines) == 1 else 416
        add("Impact", s, e, rf"{{\pos(540,{y})\fs{size}\fad(160,120)}}" + body)
        # accent rule between kicker and impact line
        add(
            "Bar",
            s,
            e,
            r"{\pos(540,286)\fad(160,120)\p1}m -150 0 l 150 0 l 150 7 l -150 7",
            layer=-1,
        )

    for s, e, text in cfg.get("captions", []):
        lines, size = wrap(text, BLACK, 980, [96, 90, 84, 78, 72, 66])
        body = r"\N".join(esc(l) for l in lines)
        add("Sub", s, e, rf"{{\pos(540,1300)\fs{size}}}" + body)

    if cfg.get("cta"):
        add("Cta", cut_out - 4.2, cut_out, r"{\pos(540,1570)\fad(300,0)}" + esc(cfg["cta"]))

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
    with open(path, "w") as fh:
        fh.write(header + "\n".join(ev) + "\n")
    print(f"wrote {path}: {len(ev)} events")


# ---------------------------------------------------------------- thumbnail
def build_thumb(spec, path, size=(1280, 720)):
    """16:9 thumbnail. Typography-first; a portrait is used only if one is given.

    The JAL short reused a still from that video. For a different video, an
    off-tone face hurts more than no face at all, so `portrait` is optional.
    """
    TW_, TH_ = size
    k = TW_ / 1280.0  # every hard-coded distance below is tuned at 1280 wide
    im = Image.new("RGB", (TW_, TH_), BG)
    d = ImageDraw.Draw(im)

    m = int(64 * k)
    col_w = TW_ - m * 2

    portrait = spec.get("portrait")
    if portrait and os.path.exists(portrait):
        p = Image.open(portrait).convert("RGB")
        if spec.get("portrait_crop"):
            p = p.crop(tuple(spec["portrait_crop"]))
        ph = TH_ - int(52 * k)
        pw = int(p.width * ph / p.height)
        p = p.resize((pw, ph), Image.LANCZOS)
        px = TW_ - pw - int(30 * k)
        edge = max(2, int(3 * k))
        d.rectangle([px - edge, int(24 * k) - edge, px + pw + edge, int(26 * k) + ph + edge],
                    fill=WHITE)
        im.paste(p, (px, int(26 * k)))
        col_w = px - m - int(40 * k)

    # badge + meta line
    y = int(48 * k)
    fb = font(BLACK, int(40 * k))
    badge = spec.get("badge")
    bx = m
    bh = int(66 * k)
    if badge:
        bw = tw(d, badge, fb) + int(44 * k)
        d.rectangle([m, y, m + bw, y + bh], fill=RED)
        d.text((m + int(22 * k), y + bh // 2), badge, font=fb, fill=WHITE, anchor="lm")
        bx = m + bw + int(22 * k)
    if spec.get("meta"):
        fm, _ = fit(d, spec["meta"], BOLD, m + col_w - bx, int(36 * k))
        d.text((bx, y + bh // 2), spec["meta"], font=fm, fill=(195, 195, 200), anchor="lm")

    # headline block, centred in the space left under the badge.
    # CJK glyphs sit well inside the em box, so every position below is measured
    # from the real ink bounds - going by font size alone leaves ragged gaps.
    def ink(text, f):
        x0, y0, x1, y1 = d.textbbox((0, 0), text, font=f)
        return y0, y1 - y0

    top_limit = int(48 * k) + bh + int(56 * k)
    bottom_limit = TH_ - int(64 * k)

    blocks = []  # (text, font, ink_top, ink_h, colour, gap_after)
    head_size = int(spec.get("head_size", 86) * k)
    accent_size = int(spec.get("accent_size", 124) * k)
    line_gap = int(26 * k)

    for line in spec.get("lines", []):
        f, _ = fit(d, line, BLACK, col_w, head_size)
        y0, hgt = ink(line, f)
        blocks.append((line, f, y0, hgt, WHITE, line_gap))

    accent = spec.get("accent")
    rule_h = max(4, int(8 * k))
    if accent:
        if blocks:
            t, f, y0, hgt, col, _ = blocks[-1]
            blocks[-1] = (t, f, y0, hgt, col, int(34 * k))
        af, _ = fit(d, accent, BLACK, col_w, accent_size)
        ay0, ahgt = ink(accent, af)
        blocks.append((accent, af, ay0, ahgt, YELLOW, int(30 * k)))

    block_h = sum(hgt for _, _, _, hgt, _, _ in blocks)
    block_h += sum(g for *_, g in blocks[:-1]) if len(blocks) > 1 else 0
    if accent:
        block_h += blocks[-1][5] + rule_h

    y = top_limit + max(0, (bottom_limit - top_limit - block_h) // 2)
    for i, (text, f, y0, hgt, col, gap) in enumerate(blocks):
        d.text((m, y - y0), text, font=f, fill=col)
        y += hgt + (gap if i < len(blocks) - 1 or accent else 0)
    if accent:
        d.rectangle([m, y, m + col_w, y + rule_h], fill=RED)

    if spec.get("handle"):
        fh_ = font(REG, int(28 * k))
        d.text((TW_ - int(30 * k), TH_ - int(24 * k)), spec["handle"],
               font=fh_, fill=(120, 120, 128), anchor="rb")

    im.save(path)
    print(f"wrote {path} ({TW_}x{TH_})")
    return path


# ---------------------------------------------------------------- cover card
def build_cover(spec, thumb_1080, path):
    """1080x1920 opening card - also usable as the Short's custom cover image."""
    im = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(im)

    if spec.get("kicker"):
        d.text((W // 2, 96), spec["kicker"], font=font(BOLD, 46), fill=(156, 156, 156),
               anchor="mm")

    for i, line in enumerate(spec.get("top", [])):
        f, _ = fit(d, line, BLACK, W - 90, 84)
        d.text((W // 2, 220 + i * 118), line, font=f, fill=WHITE, anchor="mm")

    t = Image.open(thumb_1080)
    tx, ty = (W - t.width) // 2, 470
    d.rectangle([tx - 5, ty - 5, tx + t.width + 4, ty + t.height + 4], fill=WHITE)
    im.paste(t, (tx, ty))

    d.rectangle([W // 2 - 160, 1198, W // 2 + 160, 1205], fill=RED)

    y = 1300
    for line, col, size in spec.get("bottom", []):
        f, s = fit(d, line, BLACK, W - 90, size)
        d.text((W // 2, y), line, font=f, fill=COLORS.get(col, WHITE), anchor="mm")
        y += size + 46

    im.save(path)
    print(f"wrote {path} ({W}x{H})")
    return path


# ---------------------------------------------------------------- render
def render(cfg, ass_path, cover_path, out):
    cut_in, cut_out = cfg["cut_in"], cfg["cut_out"]
    intro = cfg.get("intro", 4.0)
    lay = cfg.get("layout", {})
    vid_y = lay.get("vid_y", 600)
    vid_h = lay.get("vid_h", 480)

    crop = cfg.get("source_crop")
    if crop:
        pre = "crop={w}:{h}:{x}:{y},".format(**crop)
    else:
        # no burned-in captions to drop: fill the panel width and centre-crop
        pre = f"scale={W}:-2:flags=lanczos,crop={W}:{vid_h}:0:(ih-{vid_h})/2,"

    vf = (
        pre
        + f"scale={W}:{vid_h}:flags=lanczos,"
        + f"pad={W}:{H}:0:{vid_y}:black,"
        + "setsar=1,fps=30,"
        + f"subtitles={ass_path}:fontsdir=/usr/share/fonts"
    )
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-t", str(intro), "-i", cover_path,
        "-ss", str(cut_in), "-to", str(cut_out), "-i", cfg["source"],
        "-f", "lavfi", "-t", str(intro), "-i", "anullsrc=r=44100:cl=stereo",
        "-filter_complex",
        f"[0:v]scale={W}:{H},setsar=1,fps=30,format=yuv420p[v0];"
        f"[1:v]{vf},format=yuv420p[v1];"
        "[v0][v1]concat=n=2:v=1:a=0[v];"
        f"[1:a]afade=t=in:st=0:d=0.20,"
        f"afade=t=out:st={cut_out - cut_in - 0.5:.2f}:d=0.5[a1];"
        "[2:a][a1]concat=n=2:v=0:a=1[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-profile:v", "high", "-preset", "slow", "-crf", "19",
        "-pix_fmt", "yuv420p", "-r", "30", "-g", "60",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-movflags", "+faststart",
        out,
    ]
    subprocess.run(cmd, check=True)
    print(f"wrote {out}  ({intro + cut_out - cut_in:.1f}s)")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("config")
    ap.add_argument("--thumbs-only", action="store_true",
                    help="build thumbnails and cover cards without the source video")
    ap.add_argument("--variant", help="build only this thumbnail variant id")
    args = ap.parse_args()

    cfg_path = os.path.abspath(args.config)
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    # every relative path in the config is resolved against the config's own folder
    os.chdir(os.path.dirname(cfg_path))

    slug = cfg["slug"]
    outdir = cfg.get("outdir", "out")
    os.makedirs(outdir, exist_ok=True)

    variants = cfg.get("thumb_variants") or [cfg["thumb"]]
    if args.variant:
        variants = [v for v in variants if v.get("id") == args.variant]
        if not variants:
            sys.exit(f"no thumbnail variant named {args.variant!r}")

    covers = {}
    for v in variants:
        vid = v.get("id", "a")
        base = f"{outdir}/{slug}_{vid}"
        build_thumb(v, f"{base}_thumb_16x9.png", size=(1280, 720))
        embed = build_thumb(v, f"{base}_embed.png", size=(1080, 608))
        cover_spec = v.get("cover") or cfg.get("cover", {})
        covers[vid] = build_cover(cover_spec, embed, f"{base}_cover_9x16.png")
        os.remove(embed)

    if args.thumbs_only:
        return
    if not os.path.exists(cfg["source"]):
        sys.exit(f"source video not found: {cfg['source']} "
                 f"(put it next to the config, or run with --thumbs-only)")
    if not cfg.get("captions"):
        sys.exit("config has no captions - transcribe the cut first")

    main_variant = cfg.get("cover_variant") or variants[0].get("id", "a")
    ass_path = f"{outdir}/{slug}.ass"
    build_ass(cfg, ass_path)
    render(cfg, ass_path, covers[main_variant], f"{outdir}/{slug}_9x16.mp4")


if __name__ == "__main__":
    main()
