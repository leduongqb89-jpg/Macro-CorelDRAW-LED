import numpy as np
from led_layout import *
from lighting import bulbs, light_map, uniformity, fill_dark
s = 600 / (775 - 266)
P = lambda pts: [((px - 93) * s, (775 - py) * s) for px, py in pts]
A = Polygon(P([(93, 775), (290, 266), (400, 266), (603, 775), (492, 775),
               (447, 658), (243, 658), (202, 775)]), [P([(344, 385), (275, 573), (414, 573)])])
sigma = 30.0

def panel(ax_led, ax_map, lay, title):
    B = bulbs(lay.leds, 3, 1)
    draw(ax_led, lay, title)
    ax_led.plot(B[:, 0], B[:, 1], "o", color="yellow", ms=3, mec="k", mew=0.3)
    X, Y, I, mask = light_map(lay.poly, B, sigma)
    Im = np.where(mask, I / I[mask].mean(), np.nan)
    ax_map.pcolormesh(X, Y, Im, cmap="inferno", vmin=0, vmax=1.6, shading="auto")
    ax_map.set_aspect("equal"); ax_map.axis("off")
    u = uniformity(lay.poly, B, sigma, lay.cfg.margin)
    ax_map.set_title(f"Do sang - do deu {u*100:.0f}%", fontsize=10)
    return u

fig, axs = plt.subplots(1, 4, figsize=(22, 7))
c1 = Cfg(); c1.gap = 25.0; c1.row_gap = 12.0; c1.stagger = False
lay1 = Layout(A, c1); lay1.run(mode="along")
u1 = panel(axs[0], axs[1], lay1, "TRUOC: theo cum, khe thang hang")

c2 = Cfg(); c2.gap = 10.0
pitch = (c2.L + c2.gap) / c2.cn           # buoc bong trung binh doc net
c2.row_gap = max(3.0, pitch - c2.W)       # cot cach deu bang buoc bong
lay2 = Layout(A, c2); lay2.run(mode="along")
n_add = fill_dark(lay2, pitch)
u2 = panel(axs[2], axs[3], lay2, f"SAU: deu diem sang, so le, lap cho toi (+{n_add})")
fig.suptitle(f"Module 65x15 (3 bong) - buoc diem sang ~{pitch:.0f}mm", fontsize=13)
plt.tight_layout(); plt.savefig("preview_light.png", dpi=90)
print(len(lay1.leds), u1, len(lay2.leds), u2, n_add, pitch, c2.row_gap)
