from led_layout import *
from wiring import build_chains
s = 600 / (775 - 266)
P = lambda pts: [((px - 93) * s, (775 - py) * s) for px, py in pts]
A = Polygon(P([(93, 775), (290, 266), (400, 266), (603, 775), (492, 775),
               (447, 658), (243, 658), (202, 775)]), [P([(344, 385), (275, 573), (414, 573)])])
SQ = Polygon([(0, 0), (500, 0), (500, 420), (0, 420)])
O = Point(0, 0).buffer(300, 64).difference(Point(0, 0).buffer(190, 64))
c = Cfg(); c.gap = 25.0; c.row_gap = 12.0; c.margin = 10.0
colors = ["#e41a1c", "#ff7f00", "#4daf4a", "#984ea3", "#a65628", "#f781bf"]
fig, axs = plt.subplots(1, 3, figsize=(18, 7.5))
for ax, (shape, name) in zip(axs, [(A, "Chu A 600mm"), (SQ, "Hinh vuong 500x420"), (O, "Chu O")]):
    lay = Layout(shape, c); lay.run(mode="along"); draw(ax, lay, name)
    wires = build_chains(lay.leds, lay.tags, max_per_wire=20, inside=lay.inside)
    for w, pts in enumerate(wires):
        col = colors[w % len(colors)]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], "-", color=col, lw=1.3)
        ax.plot(*pts[0], "o", color=col, ms=8)
        ax.annotate(f"IN {w+1}", pts[0], textcoords="offset points", xytext=(4, 4),
                    fontsize=8, color=col, weight="bold")
    ax.set_title(ax.get_title() + f" | {len(wires)} day (toi da 20 LED/day)", fontsize=10)
fig.suptitle("Mo phong duong di day - LED noi tiep, doc net, zic-zac giua cac cot", fontsize=13)
plt.tight_layout(); plt.savefig("preview_wiring.png", dpi=100)
