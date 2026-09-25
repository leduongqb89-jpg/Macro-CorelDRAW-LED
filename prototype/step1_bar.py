"""
BUOC 1 - THANH THANG. Quy tac:
  - Cach mep bang nhau o 4 phia.
  - So cot / so hang chia deu vua khit (khoang du chia deu).
  - Module nam doc theo thanh.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

LEN = 600.0


def layout_dots(W, P=25.0, D=9.0, m=6.0):
    e = m + D / 2
    nx = round((LEN - 2 * e) / P) + 1
    ny = max(1, round((W - 2 * e) / P) + 1)
    px = (LEN - 2 * e) / (nx - 1)
    py = (W - 2 * e) / (ny - 1) if ny > 1 else 0
    ys = [W / 2] if ny == 1 else [e + j * py for j in range(ny)]
    return [(e + i * px, y) for i in range(nx) for y in ys], px, py


def layout_mod(W, L=65.0, Wm=15.0, m=10.0, gap=25.0, cgap=12.0):
    nc = max(1, int((W - 2 * m + cgap) / (Wm + cgap)))
    nr = max(1, int((LEN - 2 * m + gap) / (L + gap)))
    gy = (W - 2 * m - nc * Wm) / (nc - 1) if nc > 1 else 0
    gx = (LEN - 2 * m - nr * L) / (nr - 1) if nr > 1 else 0
    y0 = m if nc > 1 else (W - Wm) / 2
    x0 = m if nr > 1 else (LEN - L) / 2
    return [(x0 + i * (L + gx), y0 + j * (Wm + gy)) for i in range(nr) for j in range(nc)], gx, gy


widths = [60, 90, 120, 160]
fig, axs = plt.subplots(len(widths), 2, figsize=(16, 9))
for r, W in enumerate(widths):
    pts, px, py = layout_dots(W)
    ax = axs[r][0]
    ax.add_patch(Rectangle((0, 0), LEN, W, fill=False, ec="#444", lw=1))
    for x, y in pts:
        ax.add_patch(Circle((x, y), 4.5, color="#d62728"))
    ax.set_title(f"LED hạt 9mm – nét rộng {W}mm: {len(pts)} LED, bước ngang {px:.1f}, bước dọc {py:.1f}" if py else
                 f"LED hạt 9mm – nét rộng {W}mm: {len(pts)} LED, 1 hàng giữa, bước {px:.1f}", fontsize=10, loc="left")
    mods, gx, gy = layout_mod(W)
    ax = axs[r][1]
    ax.add_patch(Rectangle((0, 0), LEN, W, fill=False, ec="#444", lw=1))
    for x, y in mods:
        ax.add_patch(Rectangle((x, y), 65, 15, fc="#4da3ff", ec="#003a80", lw=0.8))
    nc = len({round(y, 3) for _, y in mods})
    ax.set_title(f"Module 65×15 – nét rộng {W}mm: {len(mods)} module, {nc} cột, khe đầu {gx:.1f}, khe cột {gy:.1f}",
                 fontsize=10, loc="left")
for r, W in enumerate(widths):
    for ax in axs[r]:
        ax.set_xlim(-10, LEN + 10); ax.set_ylim(-10, max(widths) + 10)
        ax.set_aspect("equal"); ax.axis("off")
fig.suptitle("Bước 1 – Thanh thẳng dài 600mm (cách mép: LED hạt 6mm, module 10mm)", fontsize=13)
plt.tight_layout(); plt.savefig("step1_bar.png", dpi=90)
