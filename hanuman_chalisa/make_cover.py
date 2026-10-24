#!/usr/bin/env python3
"""Hanuman Chalisa "Shanivar Special" cover / thumbnail generator.

Writes two files:
  <out>.png        1920x1080 video background / stream slate
  <out>-thumb.jpg  1280x720 YouTube thumbnail (under 2 MB, as YouTube requires)

Usage:
  python3 make_cover.py                          # -> out/cover.png, out/cover-thumb.jpg
  python3 make_cover.py --image hanuman.png      # put your own Hanuman ji artwork in the halo
  python3 make_cover.py --day "मंगलवार स्पेशल"     # change the badge (default: शनिवार स्पेशल)
  python3 make_cover.py --tagline "11 बार पाठ"     # change the line next to LIVE
  python3 make_cover.py --no-live                # leave out the red LIVE tag (for VOD uploads)

Needs Pillow built with libraqm (needed to shape Devanagari correctly):
  pip install pillow
"""

import argparse
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

HERE = os.path.dirname(os.path.abspath(__file__))
SANS = os.path.join(HERE, "fonts", "NotoSansDevanagari-Bold.ttf")
SERIF = os.path.join(HERE, "fonts", "NotoSerifDevanagari-Bold.ttf")
LATIN = os.path.join(HERE, "fonts", "NotoSans-Bold.ttf")

W, H = 1920, 1080
SAFFRON = (255, 140, 0)
MAROON = (90, 8, 8)
GOLD = (255, 215, 64)
CREAM = (255, 244, 214)
RED = (214, 20, 20)


def font(path, size):
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)


def background():
    # radial gradient: bright saffron glow behind the halo, fading to maroon
    cx, cy = int(W * 0.72), int(H * 0.46)
    small = Image.new("RGB", (W // 4, H // 4))
    px = small.load()
    maxd = math.hypot(W, H) * 0.62
    for y in range(small.height):
        for x in range(small.width):
            d = min(math.hypot(x * 4 - cx, y * 4 - cy) / maxd, 1.0)
            t = d ** 0.8
            px[x, y] = tuple(int(SAFFRON[i] * (1 - t) + MAROON[i] * t) for i in range(3))
    img = small.resize((W, H), Image.BICUBIC)

    # sun rays from the halo centre
    rays = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(rays)
    n = 36
    r = W * 1.2
    for i in range(n):
        if i % 2:
            continue
        a0 = 2 * math.pi * i / n
        a1 = 2 * math.pi * (i + 1) / n
        d.polygon([(cx, cy), (cx + r * math.cos(a0), cy + r * math.sin(a0)),
                   (cx + r * math.cos(a1), cy + r * math.sin(a1))], fill=38)
    rays = rays.filter(ImageFilter.GaussianBlur(6))
    img = Image.composite(Image.new("RGB", (W, H), GOLD), img, rays)
    return img, (cx, cy)


def halo(img, centre, artwork):
    cx, cy = centre
    R = 340
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((cx - R - 60, cy - R - 60, cx + R + 60, cy + R + 60), fill=200)
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    img = Image.composite(Image.new("RGB", (W, H), (255, 230, 120)), img, glow)

    d = ImageDraw.Draw(img)
    # decorative rings with petal dots
    for rr, wdt in ((R + 26, 6), (R + 6, 3)):
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=GOLD, width=wdt)
    for i in range(48):
        a = 2 * math.pi * i / 48
        x, y = cx + (R + 46) * math.cos(a), cy + (R + 46) * math.sin(a)
        d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=GOLD)

    if artwork:
        art = Image.open(artwork).convert("RGBA")
        side = 2 * R
        scale = max(side / art.width, side / art.height)
        art = art.resize((int(art.width * scale), int(art.height * scale)), Image.LANCZOS)
        left, top = (art.width - side) // 2, (art.height - side) // 2
        art = art.crop((left, top, left + side, top + side))
        mask = Image.new("L", (side, side), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, side, side), fill=255)
        img.paste(art, (cx - R, cy - R), Image.composite(art.getchannel("A"), mask, mask))
    else:
        # no artwork supplied: saffron disc with "राम" and a gada (mace)
        d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(230, 90, 0))
        d.ellipse((cx - R + 30, cy - R + 30, cx + R - 30, cy + R - 30), outline=GOLD, width=3)
        draw_gada(d, cx + 205, cy - 40)
        f = font(SERIF, 210)
        outlined(d, (cx - 75, cy - 10), "राम", f, CREAM, MAROON, 8, anchor="mm")
        outlined(d, (cx - 75, cy + 170), "॥ जय श्री राम ॥", font(SANS, 46), GOLD, MAROON, 4, anchor="mm")
    return img


def draw_gada(d, x, y):
    # handle
    d.rounded_rectangle((x - 14, y - 10, x + 14, y + 250), radius=10, fill=(150, 75, 0),
                        outline=MAROON, width=3)
    for yy in (y + 60, y + 120, y + 180):
        d.rectangle((x - 18, yy, x + 18, yy + 12), fill=GOLD, outline=MAROON)
    d.ellipse((x - 26, y + 236, x + 26, y + 280), fill=GOLD, outline=MAROON, width=3)
    # head
    d.ellipse((x - 85, y - 170, x + 85, y), fill=GOLD, outline=MAROON, width=5)
    # ridges on the head
    ridge = (200, 140, 0)
    d.line((x, y - 170, x, y), fill=ridge, width=4)
    d.arc((x - 50, y - 170, x + 50, y), 90, 270, fill=ridge, width=4)
    d.arc((x - 50, y - 170, x + 50, y), 270, 90, fill=ridge, width=4)
    d.line((x - 85, y - 85, x + 85, y - 85), fill=ridge, width=4)
    d.polygon([(x, y - 215), (x - 18, y - 165), (x + 18, y - 165)], fill=GOLD, outline=MAROON)


def outlined(d, xy, text, f, fill, stroke, sw, anchor="la"):
    d.text((xy[0] + 5, xy[1] + 6), text, font=f, fill=(40, 0, 0), anchor=anchor,
           stroke_width=sw, stroke_fill=(40, 0, 0))
    d.text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=sw, stroke_fill=stroke)


def pill(d, x, y, text, f, bg, fg, pad=(34, 14)):
    l, t, r, b = d.textbbox((x, y), text, font=f)
    d.rounded_rectangle((l - pad[0], t - pad[1], r + pad[0], b + pad[1]), radius=(b - t) // 2 + pad[1],
                        fill=bg, outline=GOLD, width=4)
    d.text((x, y), text, font=f, fill=fg)
    return r + pad[0]


def text_panel(img, day, tagline, live):
    d = ImageDraw.Draw(img)
    x = 90
    pill(d, x + 10, 70, day, font(SANS, 64), RED, GOLD)

    outlined(d, (x, 210), "श्री हनुमान", font(SERIF, 150), GOLD, MAROON, 10)
    outlined(d, (x, 400), "चालीसा", font(SERIF, 190), GOLD, MAROON, 12)
    outlined(d, (x + 6, 650), "SHRI HANUMAN CHALISA", font(LATIN, 58), CREAM, MAROON, 5)
    outlined(d, (x + 6, 740), "जय बजरंगबली । संकट मोचन", font(SANS, 56), CREAM, MAROON, 5)

    if live:
        f = font(LATIN, 62)
        l, t, r, b = d.textbbox((x + 80, 880), "LIVE", font=f)
        d.rounded_rectangle((x, t - 18, r + 34, b + 18), radius=14, fill=RED)
        d.ellipse((x + 22, (t + b) // 2 - 18, x + 58, (t + b) // 2 + 18), fill="white")
        d.text((x + 80, 880), "LIVE", font=f, fill="white")
        x2 = r + 70
    else:
        x2 = x
    d.text((x2, 884), tagline, font=font(SANS, 54), fill=CREAM,
           stroke_width=4, stroke_fill=MAROON)
    return img


def border(img):
    d = ImageDraw.Draw(img)
    d.rectangle((14, 14, W - 15, H - 15), outline=GOLD, width=6)
    d.rectangle((28, 28, W - 29, H - 29), outline=(255, 190, 60), width=2)
    return img


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--image", help="your own Hanuman ji artwork (shown in the halo)")
    p.add_argument("--day", default="शनिवार स्पेशल", help="badge text")
    p.add_argument("--tagline", default="हर शनिवार । विशेष पाठ", help="line next to the LIVE tag")
    p.add_argument("--no-live", action="store_true", help="omit the LIVE tag")
    p.add_argument("--out", default=os.path.join(HERE, "out", "cover"), help="output path without extension")
    a = p.parse_args()

    if not features.check("raqm"):
        sys.exit("Pillow lacks libraqm; Hindi text would render broken. "
                 "Install libraqm (e.g. apt install libraqm0) and reinstall pillow.")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)

    img, centre = background()
    img = halo(img, centre, a.image)
    img = text_panel(img, a.day, a.tagline, not a.no_live)
    img = border(img)

    img.save(a.out + ".png", optimize=True)
    img.resize((1280, 720), Image.LANCZOS).save(a.out + "-thumb.jpg", quality=90, optimize=True)
    print(f"cover:     {a.out}.png (1920x1080)")
    print(f"thumbnail: {a.out}-thumb.jpg (1280x720)")


if __name__ == "__main__":
    main()
