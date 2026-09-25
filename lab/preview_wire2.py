import sys, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from glyphs import glyph
from ledtypes import F9, M65, M35
from metrics import symmetry_axis
from engine import Engine
from bench import draw
from wiring2 import plan

cases = [("A", M65, 16), ("O", M65, 16), ("E", F9, 60), ("S", M35, 20)]
fig, axs = plt.subplots(1, len(cases), figsize=(6 * len(cases), 7))
cols = ["#e41a1c", "#ff7f00", "#2ca02c", "#9467bd", "#8c564b", "#e377c2", "#17becf"]
for ax, (ch, t, mx) in zip(axs, cases):
    shp = glyph(ch, 600)
    eng = Engine(shp, t, sym_axis=symmetry_axis(shp))
    leds = eng.run()
    step = eng.pitch_u
    wires, paths = plan(leds, t, step, max_per=mx, inside=eng.inside)
    draw(ax, shp, leds, t, "")
    x0, y0, x1, y1 = shp.bounds
    feed = ((x0 + x1) / 2, y0 - 60)
    ax.plot(*feed, "ks", ms=10); ax.annotate("NGUỒN", feed, xytext=(8, -4), textcoords="offset points", fontsize=9, weight="bold")
    for w, p in enumerate(paths):
        c = cols[w % len(cols)]
        ax.plot([q[0] for q in p], [q[1] for q in p], "-", color=c, lw=1.4)
        ax.plot([feed[0], p[0][0]], [feed[1], p[0][1]], ":", color=c, lw=1)
        ax.plot(*p[0], "o", color=c, ms=7)
        ax.annotate(f"IN{w+1}", p[0], xytext=(4, 4), textcoords="offset points", color=c, fontsize=8, weight="bold")
    ax.set_ylim(y0 - 80, y1 + 10)
    counts = [len(w) for w in wires]
    ax.set_title(f"{ch} – {t.name}\n{len(leds)} LED – {len(wires)} dây: {counts} (tối đa {mx}/dây)", fontsize=10)
plt.tight_layout(); plt.savefig("preview_wire2.png", dpi=75)
