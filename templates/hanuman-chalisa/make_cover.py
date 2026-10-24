#!/usr/bin/env python3
"""Hanuman Chalisa "Shanivar Special" cover + thumbnail generator.

Usage:
  python3 make_cover.py [--image hanuman.png] [--out-dir out] [--no-live]

Writes:
  out/cover.png       1920x1080  - background frame for the MP4 / live stream
  out/thumbnail.jpg   1280x720   - YouTube thumbnail (< 2 MB)

--image is optional: a picture of Hanuman ji (ideally a PNG with a transparent
background). It is placed inside the golden halo on the left. Without it the
halo shows a large "ॐ".
"""

import argparse
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_TITLE = os.path.join(HERE, "fonts", "YatraOne-Regular.ttf")
FONT_SUB = os.path.join(HERE, "fonts", "RozhaOne-Regular.ttf")

W, H = 1920, 1080
GOLD = (255, 209, 64)
LIGHT_GOLD = (255, 240, 170)
DEEP_RED = (120, 8, 0)
SAFFRON = (255, 110, 0)
WHITE = (255, 255, 255)


def font(path, size):
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)


def background():
    # radial saffron -> deep red gradient, centred on the halo
    cx, cy = 560, 540
    small = Image.new("RGB", (W // 4, H // 4))
    px = small.load()
    maxd = math.hypot(W, H) / 4 * 0.75
    for y in range(small.height):
        for x in range(small.width):
            t = min(math.hypot(x - cx / 4, y - cy / 4) / maxd, 1.0)
            t = t ** 0.9
            px[x, y] = tuple(int(SAFFRON[i] * (1 - t) + DEEP_RED[i] * t) for i in range(3))
    img = small.resize((W, H), Image.BICUBIC)

    # sun rays
    rays = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(rays)
    n = 36
    for k in range(n):
        a0 = 2 * math.pi * k / n
        a1 = a0 + math.pi / n * 0.55
        r = 2400
        d.polygon([(cx, cy),
                   (cx + r * math.cos(a0), cy + r * math.sin(a0)),
                   (cx + r * math.cos(a1), cy + r * math.sin(a1))], fill=38)
    rays = rays.filter(ImageFilter.GaussianBlur(6))
    img = Image.composite(Image.new("RGB", (W, H), LIGHT_GOLD), img, rays)

    # vignette
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).rectangle([0, 0, W, H], outline=255, width=140)
    vig = vig.filter(ImageFilter.GaussianBlur(120))
    img = Image.composite(Image.new("RGB", (W, H), (40, 0, 0)), img, vig)
    return img


def halo(img, deity_path):
    cx, cy, r = 560, 540, 380
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([cx - r - 60, cy - r - 60, cx + r + 60, cy + r + 60], fill=200)
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    img.paste(Image.new("RGB", (W, H), (255, 225, 120)), (0, 0), glow)

    d = ImageDraw.Draw(img)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 150, 20), outline=GOLD, width=14)
    d.ellipse([cx - r + 28, cy - r + 28, cx + r - 28, cy + r - 28], outline=(255, 235, 150), width=4)
    # small petals around the ring
    for k in range(48):
        a = 2 * math.pi * k / 48
        x, y = cx + (r + 22) * math.cos(a), cy + (r + 22) * math.sin(a)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=GOLD)

    if deity_path:
        deity = Image.open(deity_path).convert("RGBA")
        box = int(r * 2.1)
        deity.thumbnail((box, box), Image.LANCZOS)
        if deity.getextrema()[3][0] == 255:  # no transparency: crop into the circle
            mask = Image.new("L", deity.size, 0)
            ImageDraw.Draw(mask).ellipse([0, 0, *deity.size], fill=255)
            deity.putalpha(mask)
        img.paste(deity, (cx - deity.width // 2, cy + r - deity.height + 20), deity)
    else:
        om = font(FONT_TITLE, 470)
        d.text((cx, cy + 10), "ॐ", font=om, fill=DEEP_RED, anchor="mm",
               stroke_width=6, stroke_fill=GOLD)


def shadow_text(img, xy, text, f, fill, stroke=6, stroke_fill=DEEP_RED, anchor="mm", blur=10):
    sh = Image.new("L", img.size, 0)
    ImageDraw.Draw(sh).text((xy[0] + 6, xy[1] + 8), text, font=f, fill=200, anchor=anchor,
                            stroke_width=stroke, stroke_fill=200)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    img.paste(Image.new("RGB", img.size, (30, 0, 0)), (0, 0), sh)
    ImageDraw.Draw(img).text(xy, text, font=f, fill=fill, anchor=anchor,
                             stroke_width=stroke, stroke_fill=stroke_fill)


def ribbon(img, cx, cy, text, f, fill, fg, pad=(46, 18)):
    d = ImageDraw.Draw(img)
    l, t, r, b = d.textbbox((cx, cy), text, font=f, anchor="mm")
    box = [l - pad[0], t - pad[1], r + pad[0], b + pad[1]]
    d.rounded_rectangle([box[0] + 6, box[1] + 8, box[2] + 6, box[3] + 8], radius=40, fill=(50, 0, 0))
    d.rounded_rectangle(box, radius=40, fill=fill, outline=GOLD, width=6)
    d.text((cx, cy), text, font=f, fill=fg, anchor="mm")
    return box


def live_pill(img, x, y, text="LIVE"):
    d = ImageDraw.Draw(img)
    f = font(FONT_SUB, 50)
    tw = d.textlength(text, font=f)
    d.rounded_rectangle([x, y, x + tw + 110, y + 76], radius=38, fill=(220, 0, 0), outline=WHITE, width=4)
    d.ellipse([x + 26, y + 24, x + 54, y + 52], fill=WHITE)
    d.text((x + 74, y + 38), text, font=f, fill=WHITE, anchor="lm")


def cover(deity_path, live=True):
    img = background()
    halo(img, deity_path)

    tx = 1390  # centre of the text column
    ribbon(img, tx, 175, "शनिवार स्पेशल", font(FONT_SUB, 78), (200, 0, 0), WHITE)
    shadow_text(img, (tx, 390), "श्री हनुमान", font(FONT_TITLE, 190), GOLD, stroke=8)
    shadow_text(img, (tx, 590), "चालीसा", font(FONT_TITLE, 230), GOLD, stroke=9)
    shadow_text(img, (tx, 760), "संकट मोचन  •  भय बाधा नाशक", font(FONT_SUB, 62), WHITE,
                stroke=4, blur=6)
    ribbon(img, tx, 880, "जय श्री राम  |  जय बजरंगबली", font(FONT_SUB, 58), (255, 200, 40), DEEP_RED)
    if live:
        live_pill(img, 60, 50, "LIVE")
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", help="optional Hanuman ji picture (PNG with transparency works best)")
    ap.add_argument("--out-dir", default=os.path.join(HERE, "out"))
    ap.add_argument("--no-live", action="store_true", help="omit the LIVE badge (normal uploads)")
    a = ap.parse_args()

    os.makedirs(a.out_dir, exist_ok=True)
    img = cover(a.image, live=not a.no_live)
    img.save(os.path.join(a.out_dir, "cover.png"), optimize=True)
    img.resize((1280, 720), Image.LANCZOS).save(
        os.path.join(a.out_dir, "thumbnail.jpg"), quality=90, optimize=True)
    print("wrote", os.path.join(a.out_dir, "cover.png"), "and thumbnail.jpg")


if __name__ == "__main__":
    main()
