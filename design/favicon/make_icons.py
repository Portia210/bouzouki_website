"""Builds the site icons from the supplied pick photo.

    uv run python design/favicon/make_icons.py deepblue    # apply: writes static/favicon.ico + static/img/*.png
    uv run python design/favicon/make_icons.py sheet    # preview sheet -> design/favicon/sheets/

Variants (tile background): pearl, deepblue (current), blue, black, night. Needs Pillow (dev dependency).
The pick outline is cut from originals/pick-photo.png; the colour is the amber in originals/color-sample-amber.png.
"""
import io, struct, sys
from collections import deque
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw, ImageChops

HERE = Path(__file__).resolve().parent
SRC = HERE / "originals" / "pick-photo.png"
D = str(HERE.parent.parent / "static")
SHEETS = HERE / "sheets"

def build_pick():
    im = Image.open(SRC).convert("RGB"); W, H = im.size; px = im.load()
    seen = bytearray(W * H)
    q = deque([(x, y) for x in range(W) for y in (0, H - 1)] + [(x, y) for y in range(H) for x in (0, W - 1)])
    while q:
        x, y = q.popleft()
        if x < 0 or y < 0 or x >= W or y >= H or seen[y * W + x] or min(px[x, y]) <= 236: continue
        seen[y * W + x] = 1; q.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
    mask = Image.new("L", (W, H), 255); mp = mask.load()
    for y in range(H):
        for x in range(W):
            if seen[y * W + x]: mp[x, y] = 0
    mask = mask.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(2.2)).point(lambda v: max(0, min(255, (v - 128) * 6 + 128))).filter(ImageFilter.GaussianBlur(0.6))
    mask = mask.crop(mask.getbbox()); w, h = mask.size
    base = (224, 144, 47)   # the amber the developer supplied (#e0902f)
    fill = Image.new("RGB", (w, h)); fp = fill.load()
    for y in range(h):
        for x in range(w):
            k = 1.06 - 0.14 * ((x / w + y / h) / 2); fp[x, y] = tuple(min(255, round(c * k)) for c in base)
    inner = mask.point(lambda v: 255 if v > 200 else 0).filter(ImageFilter.MinFilter(2 * max(1, round(min(w, h) * 0.022)) + 1)).filter(ImageFilter.GaussianBlur(0.8))
    pick = Image.composite(fill, Image.new("RGB", (w, h), (176, 104, 24)), inner).convert("RGBA"); pick.putalpha(mask)
    return pick

PICK = build_pick()
BIG = 1024

def gradient(c1, c2):
    g = Image.new("RGB", (BIG, BIG)); gp = g.load()
    for y in range(BIG):
        for x in range(BIG):
            t = (x + y) / (2 * BIG - 2); gp[x, y] = tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))
    return g

def glow(color, center, radius, alpha):
    g = Image.new("L", (BIG, BIG), 0); d = ImageDraw.Draw(g)
    cx, cy = center; d.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=alpha)
    g = g.filter(ImageFilter.GaussianBlur(radius / 2.2))
    return Image.merge("RGBA", (*[Image.new("L", (BIG, BIG), c) for c in color], g))

VARIANTS = {
    "blue":  dict(grad=((60, 110, 245), (20, 44, 140)), glows=[((120, 170, 255), (300, 220), 420, 150)]),
    "deepblue": dict(grad=((33, 68, 188), (7, 16, 66)), glows=[((90, 140, 240), (300, 220), 400, 105)]),
    "night": dict(grad=((30, 40, 82), (9, 13, 30)), glows=[((255, 170, 60), (BIG // 2, BIG // 2 + 40), 420, 120)]),
    "black": dict(grad=((34, 34, 40), (3, 3, 5)), glows=[((255, 170, 60), (BIG // 2, BIG // 2 + 30), 400, 85)], ring=True),
    "pearl": dict(grad=((250, 246, 236), (222, 210, 186)), glows=[((255, 255, 255), (300, 240), 380, 190)]),
}

def master(variant, rounded=True, tilt=-10):
    v = VARIANTS[variant]
    base = gradient(*v["grad"]).convert("RGBA")
    for color, c, r, a in v["glows"]:
        base.alpha_composite(glow(color, c, r, a))
    # pick with a soft shadow, slightly tilted
    scale = 0.66 * BIG / max(PICK.size)
    p = PICK.resize((round(PICK.width * scale), round(PICK.height * scale)), Image.LANCZOS).rotate(tilt, resample=Image.BICUBIC, expand=True)
    pos = ((BIG - p.width) // 2, (BIG - p.height) // 2 + 6)
    shadow = Image.new("RGBA", (BIG, BIG), (0, 0, 0, 0))
    sh = Image.new("RGBA", p.size, (0, 0, 0, 255)); sh.putalpha(ImageChops.multiply(p.getchannel("A"), Image.new("L", p.size, 120)))
    shadow.alpha_composite(sh, (pos[0] + 8, pos[1] + 26))
    base.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))
    base.alpha_composite(p, pos)
    if v.get("ring"):   # faint light edge so a black tile doesn't vanish on a dark browser tab
        ov = Image.new("RGBA", (BIG, BIG), (0, 0, 0, 0)); ImageDraw.Draw(ov).rounded_rectangle((6, 6, BIG - 7, BIG - 7), radius=int(BIG * 0.22) - 6, outline=(255, 255, 255, 70), width=14)
        base.alpha_composite(ov)
    if rounded:
        m = Image.new("L", (BIG, BIG), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, BIG - 1, BIG - 1), radius=int(BIG * 0.22), fill=255)
        base.putalpha(m)
    return base

def out(variant, size, rounded=True):
    return master(variant, rounded).resize((size, size), Image.LANCZOS)

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "sheet":
        sheet = Image.new("RGBA", (1140, 250), "white"); sheet.paste(Image.new("RGBA", (570, 250), (32, 33, 36, 255)), (570, 0))
        for i, name in enumerate(("deepblue", "blue", "pearl")):
            x = 10 + i * 190
            sheet.alpha_composite(out(name, 128), (x, 15)); sheet.alpha_composite(out(name, 128), (x + 570, 15))
            for j, n in enumerate((48, 32, 16)):
                sheet.alpha_composite(out(name, n), (x + 140 + (0 if j < 1 else 0), 15 + j * 56)); sheet.alpha_composite(out(name, n), (x + 140 + 570, 15 + j * 56))
        sheet.convert("RGB").save(SHEETS / "05_amber_pick_on_tiles.png")
    else:
        name = mode
        out(name, 32).save(f"{D}/img/favicon-32.png"); out(name, 192).save(f"{D}/img/icon-192.png"); out(name, 512).save(f"{D}/img/icon-512.png")
        master(name, rounded=False).resize((180, 180), Image.LANCZOS).convert("RGB").save(f"{D}/img/apple-touch-icon.png")
        blobs = []
        for n in (16, 32, 48):
            b = io.BytesIO(); out(name, n).save(b, "PNG"); blobs.append((n, b.getvalue()))
        off = 6 + 16 * 3; ent = b""
        for n, d in blobs: ent += struct.pack("<BBBBHHII", n, n, 0, 0, 1, 32, len(d), off); off += len(d)
        open(f"{D}/favicon.ico", "wb").write(struct.pack("<HHH", 0, 1, 3) + ent + b"".join(d for _, d in blobs))
