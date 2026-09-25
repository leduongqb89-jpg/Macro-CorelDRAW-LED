"""Ve icon AutoLED Pro: chu A phat sang voi cac bong LED xep bang chinh thuat toan AutoLED."""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lab"))
from PIL import Image, ImageDraw, ImageFilter
from glyphs import glyph
from ledtypes import LedType
from engine import Engine
from metrics import symmetry_axis

S = 1024
OUT = os.path.join(os.path.dirname(__file__), "assets")


def rounded_bg(size):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    # nen gradient xanh dam -> tim
    grad = Image.new("RGBA", (size, size))
    gd = ImageDraw.Draw(grad)
    for y in range(size):
        t = y / size
        c = (int(18 + 30 * t), int(32 + 10 * t), int(84 + 40 * t), 255)
        gd.line([(0, y), (size, y)], fill=c)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255)
    img.paste(grad, (0, 0), mask)
    return img, mask


def letter_layer(size, dots=True):
    H = 600.0
    shp = glyph("A", H)
    x0, y0, x1, y1 = shp.bounds
    sc = size * (0.66 if dots else 0.78) / (y1 - y0)
    ox = (size - (x1 - x0) * sc) / 2 - x0 * sc
    oy = size * (0.84 if dots else 0.89)   # day chu
    tf = lambda x, y: (ox + x * sc, oy - y * sc)
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    # than chu: xam dam (mat hop chu)
    for poly in getattr(shp, "geoms", [shp]):
        d.polygon([tf(*p) for p in poly.exterior.coords], fill=((52, 66, 130, 255) if dots else (255, 205, 70, 255)), outline=(150, 175, 255, 255))
        for h in poly.interiors:
            d.polygon([tf(*p) for p in h.coords], fill=(0, 0, 0, 0))
    # vien sang
    for poly in getattr(shp, "geoms", [shp]):
        lw = max(2, size // 90) if dots else max(3, size // 40)
        lc = (170, 200, 255, 255) if dots else (255, 245, 200, 255)
        d.line([tf(*p) for p in poly.exterior.coords], fill=lc, width=lw, joint="curve")
        for h in poly.interiors:
            d.line([tf(*p) for p in h.coords], fill=lc, width=lw, joint="curve")
    if not dots:
        return base, []
    t = LedType("icon", "dot", 22, 22, [(0, 0)], 52.0, 12.0)
    eng = Engine(shp, t, sym_axis=symmetry_axis(shp))
    leds = eng.run()
    return base, [(tf(l[0], l[1]), t.L / 2 * sc) for l in leds]


def render(size, dots=True):
    bg, mask = rounded_bg(size)
    letter, pts = letter_layer(size, dots)
    img = Image.alpha_composite(bg, letter)
    if pts:
        glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        for (x, y), r in pts:
            gd.ellipse([x - r * 3.0, y - r * 3.0, x + r * 3.0, y + r * 3.0], fill=(255, 200, 60, 120))
        glow = glow.filter(ImageFilter.GaussianBlur(size / 45))
        img = Image.alpha_composite(img, glow)
        dd = ImageDraw.Draw(img)
        for (x, y), r in pts:
            dd.ellipse([x - r, y - r, x + r, y + r], fill=(255, 236, 150, 255))
            dd.ellipse([x - r * 0.45, y - r * 0.45, x + r * 0.45, y + r * 0.45], fill=(255, 255, 240, 255))
    # cat theo nen bo goc
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


big = render(S)
big.save(os.path.join(OUT, "autoled_1024.png"))
# co nho: chu dac, it chi tiet hon de van ro
small = render(256, dots=True)
tiny = render(256, dots=False)
sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
frames = []
for w, h in sizes:
    src = big if w >= 128 else tiny
    frames.append(src.resize((w, h), Image.LANCZOS))
frames[-1].save(os.path.join(OUT, "autoled.ico"), sizes=sizes, append_images=frames[:-1])
# anh xem truoc cac co
prev = Image.new("RGBA", (1024 + 40 + 256 + 20 + 128 + 20 + 64 + 20 + 48 + 20 + 32 + 20 + 16 + 40, 1064), (240, 240, 240, 255))
x = 20
for im in [big] + [big.resize((s, s), Image.LANCZOS) for s in (256, 128, 64)] + [tiny.resize((s, s), Image.LANCZOS) for s in (48, 32, 16)]:
    prev.paste(im, (x, 1044 - im.size[1]), im)
    x += im.size[0] + 20
prev.save(os.path.join(OUT, "icon_preview.png"))
print("ok")
