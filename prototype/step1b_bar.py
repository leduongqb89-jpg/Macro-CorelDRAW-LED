"""BUOC 1 (sua): luoi vuong cho LED hat; module lam tron gan nhat + kieu so le."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

LEN = 600.0


def dots(W, P=25.0, D=9.0, m=6.0):
    e = m + D / 2
    ny = max(1, round((W - 2 * e) / P) + 1)
    py = (W - 2 * e) / (ny - 1) if ny > 1 else P
    pitch = py if 0.75 * P <= py <= 1.25 * P else P        # luoi vuong neu duoc
    nx = round((LEN - 2 * e) / pitch) + 1
    px = (LEN - 2 * e) / (nx - 1)
    ys = [W / 2] if ny == 1 else [e + j * py for j in range(ny)]
    return [(e + i * px, y) for i in range(nx) for y in ys], px, (py if ny > 1 else 0)


def mods(W, stagger, L=65.0, Wm=15.0, m=10.0, gap=25.0, cgap=12.0):
    nc = max(1, int((W - 2 * m + cgap) / (Wm + cgap)))
    gy = (W - 2 * m - nc * Wm) / (nc - 1) if nc > 1 else 0
    y0 = m if nc > 1 else (W - Wm) / 2
    nr = max(1, round((LEN - 2 * m + gap) / (L + gap)))    # lam tron GAN NHAT
    gx = (LEN - 2 * m - nr * L) / (nr - 1) if nr > 1 else 0
    out = []
    for j in range(nc):
        y = y0 + j * (Wm + gy)
        if stagger and j % 2 == 1 and nr > 1:
            # cot le: bot 1 module, chia deu lai de lech nua buoc
            k = nr - 1
            g2 = (LEN - 2 * m - k * L) / (k + 1)
            out += [(m + g2 + i * (L + g2), y) for i in range(k)]
        else:
            out += [(m + i * (L + gx), y) for i in range(nr)]
    return out, gx, gy


W = 120
fig, axs = plt.subplots(3, 1, figsize=(11, 8.5))
pts, px, py = dots(W)
axs[0].add_patch(Rectangle((0, 0), LEN, W, fill=False, ec="#444"))
for x, y in pts:
    axs[0].add_patch(Circle((x, y), 4.5, color="#d62728"))
axs[0].set_title(f"LED hạt 9mm – {len(pts)} LED – lưới vuông: bước ngang {px:.1f}, bước dọc {py:.1f}", loc="left", fontsize=11)
for ax, st, name in [(axs[1], False, "thẳng hàng"), (axs[2], True, "so le kiểu gạch")]:
    ms, gx, gy = mods(W, st)
    ax.add_patch(Rectangle((0, 0), LEN, W, fill=False, ec="#444"))
    for x, y in ms:
        ax.add_patch(Rectangle((x, y), 65, 15, fc="#4da3ff", ec="#003a80", lw=0.8))
        for b in range(3):
            ax.add_patch(Circle((x + 65 / 6 + b * 65 / 3, y + 7.5), 2.2, color="#ffe14d", ec="#8a6d00", lw=0.4))
    ax.set_title(f"Module 65×15 (3 bóng) – {name} – {len(ms)} module, khe đầu {gx:.1f}, khe cột {gy:.1f}", loc="left", fontsize=11)
for ax in axs:
    ax.set_xlim(-10, LEN + 10); ax.set_ylim(-8, W + 8); ax.set_aspect("equal"); ax.axis("off")
fig.suptitle("Bước 1 (sửa) – Thanh 600 × 120mm", fontsize=13)
plt.tight_layout(); plt.savefig("step1b_bar.png", dpi=95)
