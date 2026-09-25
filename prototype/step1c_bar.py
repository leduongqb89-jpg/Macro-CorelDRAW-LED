"""
BUOC 1 (theo quy tac xuong): khoang cach TAM BONG ~ P (mac dinh 35mm).
Module L x Wm, Cn bong theo chieu dai (bong o tam moi o L/Cn).
  - Giua 2 cot: tam hang bong cach nhau ~P (chia deu vua be rong).
  - Giua 2 dau module: bong cuoi -> bong dau module ke ~P.
  - So le: cot le lech nua buoc module.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle

LEN = 600.0


def modules(W, P=35.0, L=65.0, Wm=15.0, cn=3, m=10.0, stagger="auto", min_gap=5.0):
    cell = L / cn                                   # buoc bong trong module
    # --- cot (ngang net)
    avail_c = W - 2 * (m + Wm / 2)
    # chon so cot cho tam bong gan P nhat (khong duoc chat hon Wm + min_gap)
    cands = [1] + [n for n in range(2, 60) if avail_c / (n - 1) >= Wm + min_gap]
    nc = min(cands, key=lambda n: abs((avail_c / (n - 1) if n > 1 else avail_c + Wm + 2 * m) - P))
    pc = avail_c / (nc - 1) if nc > 1 else 0
    ys = [W / 2] if nc == 1 else [m + Wm / 2 + j * pc for j in range(nc)]
    # --- doc net: buoc module sao cho bong-bong qua khe ~ P
    pm_target = L - cell + P
    avail_m = LEN - 2 * (m + L / 2)
    cands = [1] + [n for n in range(2, 200) if avail_m / (n - 1) >= L + min_gap]
    nm = min(cands, key=lambda n: abs((avail_m / (n - 1) - (L - cell) if n > 1 else 1e9) - P))
    pm = avail_m / (nm - 1) if nm > 1 else 0
    xs = [LEN / 2] if nm == 1 else [m + L / 2 + i * pm for i in range(nm)]
    st = (nc >= 3 and nc % 2 == 1) if stagger == "auto" else stagger   # so le chi khi so cot le (doi xung)
    out = []
    for j, y in enumerate(ys):
        if st and j % 2 == 1 and nm > 1:
            # cot le: lech nua buoc, dat them 1 module neu dau thanh du cho
            xs2 = [x + pm / 2 for x in xs[:-1]]
            out += [(x, y) for x in xs2]
        else:
            out += [(x, y) for x in xs]
    junction = pm - (L - cell) if nm > 1 else 0     # khoang cach bong qua khe
    return out, dict(nc=nc, pc=pc, nm=nm, pm=pm, junction=junction, cell=cell, stagger=st)


def draw(ax, W, res, P):
    out, info = res
    ax.add_patch(Rectangle((0, 0), LEN, W, fill=False, ec="#444"))
    for x, y in out:
        ax.add_patch(Rectangle((x - 32.5, y - 7.5), 65, 15, fc="#4da3ff", ec="#003a80", lw=0.8))
        for b in range(3):
            ax.add_patch(Circle((x - 32.5 + info["cell"] * (b + 0.5), y), 2.3, color="#ffe14d", ec="#8a6d00", lw=0.4))
    kind = "so le" if info["stagger"] else "thẳng hàng"
    ax.set_title(f"Nét rộng {W}mm – {len(out)} module, {info['nc']} cột ({kind}) – tâm bóng: giữa cột "
                 f"{info['pc']:.1f}, qua khe đầu {info['junction']:.1f}, trong module {info['cell']:.1f}",
                 loc="left", fontsize=10)
    ax.set_xlim(-10, LEN + 10); ax.set_ylim(-8, 168); ax.set_aspect("equal"); ax.axis("off")


if __name__ == "__main__":
    P = 35.0
    cases = [(60, "auto"), (90, "auto"), (120, False), (120, "auto"), (160, "auto")]
    fig, axs = plt.subplots(len(cases), 1, figsize=(11, 13))
    for ax, (W, st) in zip(axs, cases):
        draw(ax, W, modules(W, P, stagger=st), P)
    fig.suptitle("Bước 1 – Thanh 600mm, module 65×15 (3 bóng), tâm bóng cách nhau ~35mm, cách mép 10mm", fontsize=12)
    plt.tight_layout(); plt.savefig("step1c_bar.png", dpi=90)
