"""
Diem sang (bong LED) va mo phong do sang.
  - Module L x W co Cn bong theo chieu dai, Rn hang bong theo chieu rong.
  - Do sang tai 1 diem = tong anh huong cac bong (ham Gauss, sigma ~ do sau hop chu).
  - Do deu = do sang thap nhat / do sang trung binh (trong vung cach mep).
"""
import math
import numpy as np
from shapely.geometry import Point
from shapely import contains_xy


def bulbs(leds, cn=3, rn=1):
    out = []
    for cx, cy, hl, hw, ux, uy in leds:
        vx, vy = -uy, ux
        for i in range(cn):
            a = -hl + (i + 0.5) * 2 * hl / cn
            for j in range(rn):
                b = -hw + (j + 0.5) * 2 * hw / rn
                out.append((cx + ux * a + vx * b, cy + uy * a + vy * b))
    return np.array(out) if out else np.zeros((0, 2))


def light_map(poly, pts, sigma, res=3.0):
    x0, y0, x1, y1 = poly.bounds
    xs = np.arange(x0, x1, res); ys = np.arange(y0, y1, res)
    X, Y = np.meshgrid(xs, ys)
    I = np.zeros_like(X)
    for bx, by in pts:
        I += np.exp(-((X - bx) ** 2 + (Y - by) ** 2) / (2 * sigma ** 2))
    mask = contains_xy(poly, X, Y)
    return X, Y, I, mask


def uniformity(poly, pts, sigma, inset):
    X, Y, I, _ = light_map(poly, pts, sigma)
    inner = poly.buffer(-inset)
    m = contains_xy(inner, X, Y)
    v = I[m]
    return (v.min() / v.mean()) if v.size and v.mean() > 0 else 0.0


def fill_dark(lay, pitch, thr=0.8, cn=3, rn=1):
    """Lap cho toi: tim diem xa bong LED nhat, thu dat them LED o do."""
    from led_layout import Cfg
    c = lay.cfg
    inner = lay.poly.buffer(-(c.margin + c.W / 2))
    if inner.is_empty:
        return 0
    x0, y0, x1, y1 = inner.bounds
    g = 5.0
    X, Y = np.meshgrid(np.arange(x0, x1, g), np.arange(y0, y1, g))
    m = contains_xy(inner, X, Y)
    P = np.stack([X[m], Y[m]], 1)
    if not len(P):
        return 0
    B = bulbs(lay.leds, cn, rn)
    d = np.full(len(P), 1e9)
    for b in B:
        d = np.minimum(d, np.hypot(P[:, 0] - b[0], P[:, 1] - b[1]))
    added, tried = 0, np.zeros(len(P), bool)
    while True:
        cand = np.where(~tried & (d > thr * pitch))[0]
        if not len(cand):
            break
        i = cand[np.argmax(d[cand])]
        tried[i] = True
        px, py = P[i]
        # huong uu tien: huong cua LED gan nhat, roi cac goc khac
        near = min(lay.leds, key=lambda l: (l[0] - px) ** 2 + (l[1] - py) ** 2) if lay.leds else None
        dirs = [(near[4], near[5])] if near else []
        dirs += [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in range(0, 180, 15)]
        for ux, uy in dirs:
            led = (px, py, c.L / 2, c.W / 2, ux, uy)
            if lay.try_add(led):
                added += 1
                for b in bulbs([led], cn, rn):
                    d = np.minimum(d, np.hypot(P[:, 0] - b[0], P[:, 1] - b[1]))
                break
    return added
