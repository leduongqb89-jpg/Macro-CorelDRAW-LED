"""Chay bo thu: nhieu chu x nhieu co x nhieu loai LED. Xuat anh + bang diem."""
import sys, json, time, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Circle
from glyphs import glyph
from ledtypes import TYPES, F9, M65, M35
from metrics import evaluate, score, symmetry_axis, bulb_xy
from engine import Engine, corners

GROUPS = {
    "thang": "ILTHEF",
    "xien": "AVNKMZ",
    "cong": "OCSGUJ",
    "tron": "BRDP",
    "dau": "ĐƠƯ",
}


def layout(ch, size, t, font="sans", **kw):
    shp = glyph(ch, size, font)
    ax = symmetry_axis(shp)
    t0 = time.time()
    eng = Engine(shp, t, sym_axis=ax, **kw)
    leds = eng.run()
    r = evaluate(shp, leds, t, ax)
    r["time"] = time.time() - t0
    r["score"] = score(r, t)
    return shp, leds, r


def draw(ax, shp, leds, t, title):
    for poly in getattr(shp, "geoms", [shp]):
        ax.add_patch(MPoly(list(poly.exterior.coords), closed=True, fc="#f2f2f2", ec="#333", lw=0.8))
        for h in poly.interiors:
            ax.add_patch(MPoly(list(h.coords), closed=True, fc="white", ec="#333", lw=0.8))
    for cx, cy, ux, uy in leds:
        if t.kind == "dot":
            ax.add_patch(Circle((cx, cy), t.L / 2, color="#d62728"))
        else:
            ax.add_patch(MPoly(corners(cx, cy, t.L / 2, t.W / 2, ux, uy), closed=True, fc="#4da3ff", ec="#003a80", lw=0.5))
    if t.kind != "dot":
        B = bulb_xy(leds, t)
        if len(B):
            ax.plot(B[:, 0], B[:, 1], "o", ms=1.6, color="#ffd400")
    x0, y0, x1, y1 = shp.bounds
    ax.set_xlim(x0 - 10, x1 + 10); ax.set_ylim(y0 - 10, y1 + 10)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, fontsize=8)


def sheet(chars, size, t, fname, font="sans", cols=6, **kw):
    rows = math.ceil(len(chars) / cols)
    fig, axs = plt.subplots(rows, cols, figsize=(3.6 * cols, 4.2 * rows))
    axs = axs.flatten() if hasattr(axs, "flatten") else [axs]
    res = {}
    for ax, ch in zip(axs, chars):
        shp, leds, r = layout(ch, size, t, font, **kw)
        res[ch] = r
        draw(ax, shp, leds, t, f"{ch}  {r['score']}/10  ({r['n']} LED)\n"
             f"cv {r.get('nn_cv', 0):.2f} toi {r.get('dark_max', 0):.2f} le {r.get('lone', 0)} lech {r.get('irregular', 0)}"
             f"{' dx %.0f%%' % (100 * r['sym']) if 'sym' in r else ''}"
             f"{' goc %.0f' % r['ang_diff'] if 'ang_diff' in r else ''}"
             f"{' CHONG %d' % r['overlap'] if r['overlap'] else ''}{' LAN %d' % r['out'] if r['out'] else ''}")
    for ax in axs[len(chars):]:
        ax.axis("off")
    fig.suptitle(f"{t.name} – chữ cao {size:.0f}mm – bước tâm bóng {t.P:.0f}mm, cách mép {t.margin:.0f}mm", fontsize=12)
    plt.tight_layout(); plt.savefig(fname, dpi=80); plt.close(fig)
    return res


if __name__ == "__main__":
    chars = sys.argv[1] if len(sys.argv) > 1 else "ILTHEFAVNKMZ"
    size = float(sys.argv[2]) if len(sys.argv) > 2 else 600
    tname = sys.argv[3] if len(sys.argv) > 3 else "F9"
    t = {"F9": F9, "M65": M65, "M35": M35}[tname]
    out = sys.argv[4] if len(sys.argv) > 4 else f"out_{tname}_{int(size)}.png"
    res = sheet(chars, size, t, out)
    avg = sum(r["score"] for r in res.values()) / len(res)
    print(f"{tname} {size:.0f}mm  diem TB {avg:.2f}")
    for ch, r in res.items():
        print(ch, r["score"], {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items() if k != 'score'})
