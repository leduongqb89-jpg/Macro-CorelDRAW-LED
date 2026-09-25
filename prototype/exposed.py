"""
Kieu xep LED lo (duc lo ton, LED hat lo ra ngoai) - uu tien tham my.
  grid    : ma tran thang tuyet doi, can giua theo chu
  rings   : cac hang dong tam theo vien; moi doan giua 2 goc chia deu, co LED dung goc
  border  : 1-2 hang vien + ma tran ben trong
Moi lo tron (duong kinh D) phai nam tron trong chu va cach mep >= margin,
2 lo bat ky cach nhau >= 0.75 * buoc.
"""
import math
import numpy as np
from shapely.geometry import Polygon, Point, LineString, MultiPolygon
from shapely import contains_xy


def fits(poly, x, y, r):
    if not poly.contains(Point(x, y)):
        return False
    return all(poly.contains(Point(x + r * math.cos(a), y + r * math.sin(a)))
               for a in np.linspace(0, 2 * math.pi, 12, endpoint=False))


class Dots:
    def __init__(self, poly, P=25.0, D=9.0, margin=6.0):
        self.poly, self.P, self.D, self.m = poly, P, D, margin
        self.pts = []

    def ok_dist(self, x, y, k=0.75):
        lim = (k * self.P) ** 2
        return all((x - a) ** 2 + (y - b) ** 2 >= lim for a, b in self.pts)

    def add(self, x, y):
        if fits(self.poly, x, y, self.D / 2 + self.m - 0.3) and self.ok_dist(x, y):
            self.pts.append((x, y))
            return True
        return False

    # ---- ma tran thang ----
    def grid(self, region=None, stagger=False):
        region = region or self.poly
        x0, y0, x1, y1 = region.bounds
        P = self.P
        nx, ny = int((x1 - x0) / P) + 2, int((y1 - y0) / P) + 2
        cx0 = (x0 + x1) / 2 - (nx - 1) * P / 2
        cy0 = (y0 + y1) / 2 - (ny - 1) * P / 2
        for j in range(ny):
            for i in range(nx):
                x = cx0 + i * P + (P / 2 if stagger and j % 2 else 0)
                y = cy0 + j * P
                if region is self.poly or region.contains(Point(x, y)):
                    self.add(x, y)

    # ---- dong tam theo vien ----
    def ring_points(self, ring, corner=35.0):
        line = LineString(ring.coords)
        L = line.length
        n = max(8, int(L / 1.0))
        s = np.linspace(0, L, n, endpoint=False)
        pts = [line.interpolate(t) for t in s]
        ang = [math.atan2(pts[(i + 1) % n].y - pts[i - 1].y, pts[(i + 1) % n].x - pts[i - 1].x) for i in range(n)]
        w = 3
        turn = [abs(math.degrees(math.remainder(ang[(i + w) % n] - ang[i - w], 2 * math.pi))) for i in range(n)]
        corners = [i for i in range(n) if turn[i] > corner and turn[i] >= max(turn[(i + d) % n] for d in range(-w, w + 1))]
        # gop goc qua gan
        cs = []
        for c in corners:
            if not cs or c - cs[-1] > 2 * w:
                cs.append(c)
        if len(cs) > 1 and cs[0] + n - cs[-1] <= 2 * w:
            cs.pop()
        out = []
        if not cs:
            k = max(1, round(L / self.P))
            return [line.interpolate(i * L / k) for i in range(k)]
        for a, b in zip(cs, cs[1:] + [cs[0] + n]):
            sa, sb = s[a], (s[b % n] + (L if b >= n else 0))
            seg = sb - sa
            k = max(1, round(seg / self.P))
            for i in range(k):                      # co LED dung goc a, chia deu toi goc b
                out.append(line.interpolate((sa + i * seg / k) % L))
        return out

    def rings(self, max_rings=100):
        k = 0
        while k < max_rings:
            off = self.m + self.D / 2 + k * self.P
            inner = self.poly.buffer(-off, join_style=2)     # ~ Contour trong CorelDRAW
            if inner.is_empty:
                break
            geoms = inner.geoms if isinstance(inner, MultiPolygon) else [inner]
            for g in geoms:
                for ring in [g.exterior, *g.interiors]:
                    for p in self.ring_points(ring):
                        self.add(p.x, p.y)
            k += 1
        return k

    def border(self, n_rings=1, stagger=False):
        self.rings(n_rings)
        off = self.m + self.D / 2 + (n_rings - 1) * self.P + 0.8 * self.P
        inner = self.poly.buffer(-off, join_style=2)
        if not inner.is_empty:
            self.grid(region=inner, stagger=stagger)


if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    s = 600 / (775 - 266)
    T = lambda pts: [((px - 93) * s, (775 - py) * s) for px, py in pts]
    A = Polygon(T([(93, 775), (290, 266), (400, 266), (603, 775), (492, 775),
                   (447, 658), (243, 658), (202, 775)]), [T([(344, 385), (275, 573), (414, 573)])])
    ring = Point(0, 0).buffer(300, 128).difference(Point(0, 0).buffer(165, 128))
    wedge = Polygon([(0, 0), (400, -250), (400, 250)])
    C = ring.difference(wedge).buffer(0)

    fig, axs = plt.subplots(2, 3, figsize=(17, 11))
    for row, (shape, nm) in enumerate([(A, "A"), (C, "C")]):
        for col, (mode, title) in enumerate([("grid", "Ma tran thang"), ("rings", "Dong tam theo vien"),
                                             ("border", "Vien + ma tran")]):
            d = Dots(shape, P=25, D=9, margin=6)
            getattr(d, mode)()
            ax = axs[row][col]
            x, y = shape.exterior.xy; ax.plot(x, y, "k-", lw=1)
            for r in shape.interiors:
                x, y = r.xy; ax.plot(x, y, "k-", lw=1)
            for px, py in d.pts:
                ax.add_patch(plt.Circle((px, py), 4.5, color="#d62728"))
            ax.set_title(f"{title} - {len(d.pts)} LED", fontsize=11)
            ax.set_aspect("equal"); ax.axis("off")
    fig.suptitle("LED lo / duc lo - LED hat 9mm, buoc 25mm, cach mep 6mm", fontsize=14)
    plt.tight_layout(); plt.savefig("preview_exposed.png", dpi=85)
