"""
Thuoc do tu cham diem mot ban xep LED.
led = (cx, cy, ux, uy)  - tam va huong truc dai.
"""
import math
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.affinity import scale as sscale
from shapely import contains_xy
from shapely.strtree import STRtree


def led_poly(led, t):
    cx, cy, ux, uy = led
    hl, hw = t.L / 2, t.W / 2
    vx, vy = -uy, ux
    if t.kind == "dot":
        return Point(cx, cy).buffer(hl, 16)
    return Polygon([(cx + sx * hl * ux + sy * hw * vx, cy + sx * hl * uy + sy * hw * vy)
                    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])


def bulb_xy(leds, t):
    out = []
    for cx, cy, ux, uy in leds:
        vx, vy = -uy, ux
        for a, b in t.bulbs:
            out.append((cx + ux * a + vx * b, cy + uy * a + vy * b))
    return np.array(out) if out else np.zeros((0, 2))


def evaluate(shape, leds, t, symmetric_axis=None):
    r = {"n": len(leds)}
    polys = [led_poly(l, t) for l in leds]
    # 1. chong nhau / lan mep
    tree = STRtree(polys)
    over = 0
    for i, p in enumerate(polys):
        for j in tree.query(p.buffer(t.min_gap - 0.5)):
            if j > i and p.distance(polys[j]) < t.min_gap - 0.5:
                over += 1
    r["overlap"] = over
    inner = shape.buffer(-(t.margin - 0.8))
    r["out"] = sum(1 for p in polys if not inner.contains(p))
    B = bulb_xy(leds, t)
    r["bulbs"] = len(B)
    if len(B) < 3:
        return r
    # 2. deu khoang cach: khoang cach toi bong gan nhat THUOC LED KHAC
    owner = np.repeat(np.arange(len(leds)), len(t.bulbs))
    nn = []
    for i, (x, y) in enumerate(B):
        d = np.hypot(B[:, 0] - x, B[:, 1] - y)
        d[owner == owner[i]] = 1e9
        nn.append(d.min())
    nn = np.array(nn)
    r["nn_mean"] = float(nn.mean())
    r["nn_cv"] = float(nn.std() / nn.mean())
    # 3. vung toi lon nhat (trong vung cach mep margin + nua LED)
    core = shape.buffer(-(t.margin + min(t.W, t.L) / 2))
    if not core.is_empty:
        x0, y0, x1, y1 = core.bounds
        g = max(2.0, t.P / 8)
        X, Y = np.meshgrid(np.arange(x0, x1, g), np.arange(y0, y1, g))
        m = contains_xy(core, X, Y)
        Pp = np.stack([X[m], Y[m]], 1)
        if len(Pp):
            d = np.full(len(Pp), 1e9)
            for bx, by in B:
                d = np.minimum(d, np.hypot(Pp[:, 0] - bx, Pp[:, 1] - by))
            r["dark_max"] = float(d.max() / t.P)       # ban kinh vung toi / P
            r["dark_p95"] = float(np.percentile(d, 95) / t.P)
    # 4. LED le loi: it hon 2 LED lan can trong 1.6 buoc LED
    C = np.array([(l[0], l[1]) for l in leds])
    step = max(t.P, t.L - t.cell + t.P) if t.kind == "module" else t.P
    lone = 0
    for x, y in C:
        k = (np.hypot(C[:, 0] - x, C[:, 1] - y) < 1.6 * step).sum() - 1
        lone += k < 2
    r["lone"] = int(lone) if len(C) > 3 else 0
    # 5. do dong nhat huong module
    if t.kind == "module" and len(leds) > 2:
        diffs = []
        for i, (x, y, ux, uy) in enumerate(leds):
            d = np.hypot(C[:, 0] - x, C[:, 1] - y); d[i] = 1e9
            j = int(d.argmin())
            a = abs(math.degrees(math.atan2(ux * leds[j][3] - uy * leds[j][2], ux * leds[j][2] + uy * leds[j][3])))
            diffs.append(min(a, 180 - a))
        r["ang_diff"] = float(np.mean(diffs))
    # 4b. LED lech luoi: khong co it nhat 2 LED lan can dung buoc (+-18%)
    if len(C) > 6:
        dd = [np.sort(np.hypot(C[:, 0] - x, C[:, 1] - y))[1:5] for x, y in C]
        base = float(np.median([d[0] for d in dd]))
        irr = sum(1 for d in dd if ((d > 0.82 * base) & (d < 1.18 * base)).sum() < 2 or d[0] < 0.8 * base)
        r["irregular"] = int(irr)
        r["irr_ratio"] = irr / len(C)
    # 6. doi xung
    if symmetric_axis is not None and len(C):
        M = np.stack([2 * symmetric_axis - C[:, 0], C[:, 1]], 1)
        ok = sum(1 for x, y in M if np.hypot(C[:, 0] - x, C[:, 1] - y).min() < max(2.0, 0.08 * t.P))
        r["sym"] = ok / len(C)
    return r


def score(r, t):
    """Diem 0-10 (tru diem theo loi)."""
    s = 10.0
    s -= 3.0 * min(1, r.get("overlap", 0)) + 0.2 * r.get("overlap", 0)
    s -= 3.0 * min(1, r.get("out", 0)) + 0.2 * r.get("out", 0)
    mod = t.kind == "module"
    # module: bong trong module cach deu san (cell) khac khoang qua khe -> nguong cv cao hon
    s -= min(3.0, max(0.0, r.get("nn_cv", 0) - (0.22 if mod else 0.08)) * 15)
    s -= min(2.5, max(0.0, r.get("dark_max", 0) - (1.15 if mod else 0.85)) * 4)
    s -= min(1.5, 0.3 * r.get("lone", 0))
    s -= min(1.5, max(0.0, r.get("ang_diff", 0) - 3) * 0.08)
    if not mod:
        s -= min(3.0, r.get("irr_ratio", 0) * 25)
    if "sym" in r:
        s -= min(2.0, (1 - r["sym"]) * 6)
    return max(0.0, round(s, 1))


def symmetry_axis(shape, tol=0.985):
    """Truc doi xung doc neu chu doi xung trai-phai, nguoc lai None."""
    x0, y0, x1, y1 = shape.bounds
    best = None
    for dx in np.linspace(-0.03, 0.03, 13) * (x1 - x0):
        ax = (x0 + x1) / 2 + dx
        m = sscale(shape, xfact=-1, yfact=1, origin=(ax, 0))
        iou = shape.intersection(m).area / shape.union(m).area
        if best is None or iou > best[0]:
            best = (iou, ax)
    return best[1] if best[0] >= tol else None
