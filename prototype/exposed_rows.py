"""
Kieu 'hang song song vien, chia deu theo be rong net' cho LED hat / duc lo.
  - Chia duong bao thanh cac doan (cat o goc). Doan dai lam truoc.
  - Tai moi diem bien: do be rong net D. So hang n = round((D-2e)/P)+1,
    cac hang CHIA DEU trong be rong (khong co khe du o giua net).
  - Tren moi hang: LED chia deu tu goc den goc (co LED dung goc).
"""
import math
from led_layout import Layout, Cfg
from exposed import Dots, fits


class RowDots(Dots):
    def rows(self):
        lay = Layout(self.poly, Cfg())          # dung lai: chia doan, do be rong net
        lay.cfg.margin = self.m
        e = self.m + self.D / 2                  # tam LED cach mep
        runs = lay.runs(2.0)
        for pts in runs:
            nrm = lay.normals(pts)
            dep = [lay.depth(p.x, p.y, v[2], v[3]) for p, v in zip(pts, nrm)]
            med = sorted(dep)[len(dep) // 2]
            nrow = {}
            for p, v, d in zip(pts, nrm, dep):
                d = min(d, med)
                avail = d - 2 * e
                n = 1 if avail < 0.5 * self.P else round(avail / self.P) + 1
                for k in range(n):
                    off = e + (avail / 2 if n == 1 else k * avail / (n - 1))
                    nrow.setdefault(k, []).append((p.x + v[2] * off, p.y + v[3] * off))
            # Net thang: luoi nghieng theo net (LED thang hang ca 2 chieu)
            ux0, uy0 = nrm[0][0], nrm[0][1]
            straight = all(ux0 * v[0] + uy0 * v[1] > math.cos(math.radians(8)) for v in nrm)
            if straight and len(pts) > 2:
                a, b = pts[0], pts[-1]
                Lb = math.hypot(b.x - a.x, b.y - a.y)
                tx, ty = (b.x - a.x) / Lb, (b.y - a.y) / Lb
                vx, vy = nrm[len(nrm) // 2][2], nrm[len(nrm) // 2][3]
                cols = max(1, round(Lb / self.P))
                Pc = Lb / cols                      # buoc doc net, chia deu vua doan
                for q in range(cols):
                    s = (q + 0.5) * Pc
                    i = min(len(pts) - 1, int(s / Lb * (len(pts) - 1) + 0.5))
                    d = min(dep[i], med)
                    avail = d - 2 * e
                    n = 1 if avail < 0.5 * self.P else round(avail / self.P) + 1
                    for k in range(n):
                        off = e + (avail / 2 if n == 1 else k * avail / (n - 1))
                        self.add(a.x + tx * s + vx * off, a.y + ty * s + vy * off)
                continue
            for k, line in nrow.items():
                # chia deu tren hang theo chieu dai that cua hang
                acc = [0.0]
                for a, b in zip(line, line[1:]):
                    acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
                Lr = acc[-1]
                cnt = max(1, round(Lr / self.P))
                j = 0
                for q in range(cnt + 1):
                    t = q * Lr / cnt
                    while j < len(acc) - 2 and acc[j + 1] < t:
                        j += 1
                    seg = acc[j + 1] - acc[j] or 1
                    f = (t - acc[j]) / seg
                    a, b = line[j], line[min(j + 1, len(line) - 1)]
                    self.add(a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from shapely.geometry import Polygon, Point
    s = 600 / (775 - 266)
    T = lambda pts: [((px - 93) * s, (775 - py) * s) for px, py in pts]
    A = Polygon(T([(93, 775), (290, 266), (400, 266), (603, 775), (492, 775),
                   (447, 658), (243, 658), (202, 775)]), [T([(344, 385), (275, 573), (414, 573)])])
    ring = Point(0, 0).buffer(300, 128).difference(Point(0, 0).buffer(165, 128))
    C = ring.difference(Polygon([(0, 0), (400, -250), (400, 250)])).buffer(0)
    fig, axs = plt.subplots(1, 4, figsize=(22, 7))
    for ax, (shape, title, cls) in zip(axs, [(A, "CU: dong tam (khe giua net)", "rings"),
                                             (A, "MOI: chia deu theo be rong net", "rows"),
                                             (C, "CU: dong tam", "rings"),
                                             (C, "MOI: chia deu theo be rong net", "rows")]):
        d = RowDots(shape, P=25, D=9, margin=6)
        getattr(d, cls)()
        x, y = shape.exterior.xy; ax.plot(x, y, "k-", lw=1)
        for r in shape.interiors:
            x, y = r.xy; ax.plot(x, y, "k-", lw=1)
        for px, py in d.pts:
            ax.add_patch(plt.Circle((px, py), 4.5, color="#d62728"))
        ax.set_title(f"{title} - {len(d.pts)} LED", fontsize=11)
        ax.set_aspect("equal"); ax.axis("off")
    plt.tight_layout(); plt.savefig("preview_rows.png", dpi=85)
