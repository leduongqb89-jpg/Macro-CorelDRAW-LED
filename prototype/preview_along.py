from led_layout import *
s = 600 / (775 - 266)
P = lambda pts: [((px - 93) * s, (775 - py) * s) for px, py in pts]
A = Polygon(P([(93, 775), (290, 266), (400, 266), (603, 775), (492, 775),
               (447, 658), (243, 658), (202, 775)]), [P([(344, 385), (275, 573), (414, 573)])])
SQ = Polygon([(0, 0), (500, 0), (500, 420), (0, 420)])
O = Point(0, 0).buffer(300, 64).difference(Point(0, 0).buffer(190, 64))
c = Cfg(); c.gap = 25.0; c.row_gap = 12.0; c.margin = 10.0
fig, axs = plt.subplots(1, 3, figsize=(18, 7))
for ax, (shape, name) in zip(axs, [(A, "Chu A 600mm"), (SQ, "Hinh vuong 500x420"), (O, "Chu O")]):
    lay = Layout(shape, c); lay.run(mode="along"); draw(ax, lay, name)
fig.suptitle("Module 65x15 DOC NET - khe dau module 25mm, khe giua cot 12mm, cach mep 10mm", fontsize=13)
plt.tight_layout(); plt.savefig("preview_along.png", dpi=100)
