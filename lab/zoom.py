import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from bench import layout, draw
from ledtypes import F9, M65, M35
ch, size, tn = sys.argv[1], float(sys.argv[2]), sys.argv[3]
t = {"F9": F9, "M65": M65, "M35": M35}[tn]
kw = {}
if len(sys.argv) > 5:
    kw["fill_dark"] = sys.argv[5] == "1"
shp, leds, r = layout(ch, size, t, **kw)
fig, ax = plt.subplots(figsize=(8, 8))
draw(ax, shp, leds, t, f"{ch} {r['score']} {r}")
plt.tight_layout(); plt.savefig(sys.argv[4] if len(sys.argv) > 4 else "zoom.png", dpi=80)
