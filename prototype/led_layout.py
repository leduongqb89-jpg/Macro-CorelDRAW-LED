"""
Mo phong thuat toan rai LED module (ban Python) - dung de kiem tra thuat toan
truoc khi chuyen sang VBA cho CorelDRAW. Chi dung cac phep tuong duong voi API
CorelDRAW: kiem tra diem trong chu (Curve.IsOnCurve), lay diem theo chieu dai
duong (SubPath.GetPointPositionAt).

Nguyen tac:
  1. Chia duong bao chu thanh cac "doan" (cat tai goc gay).
  2. Doan dai lam truoc. Moi doan sinh cac hang LED song song voi doan do,
     LED nam ngang net (canh dai vuong goc voi doan). Neu khong vua thi thu
     LED nam doc net.
  3. Moi LED chi duoc dat khi: nam tron trong chu va cach mep >= margin,
     VA khong cham LED nao da dat (cach >= gap). => KHONG BAO GIO CHONG NHAU.
"""
import math
from shapely.geometry import Polygon, Point, LineString
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


class Cfg:
    L = 65.0        # chieu dai module (mm)
    W = 15.0        # chieu rong module (mm)
    margin = 10.0   # cach mep chu
    gap = 10.0      # khe ho giua 2 LED canh nhau
    row_gap = 10.0  # khe ho giua 2 hang
    step = 2.0      # buoc do duong bao
    corner = 25.0   # goc (do) coi la goc gay
    stagger = True  # so le kieu gach
    cn, rn = 3, 1   # so bong LED: theo chieu dai x chieu rong


# ---------- Hinh chu nhat xoay ----------
def rect_corners(cx, cy, hl, hw, ux, uy):
    """(ux,uy) = huong canh dai. hl, hw = nua dai / nua rong."""
    vx, vy = -uy, ux
    return [(cx + sx * hl * ux + sy * hw * vx, cy + sx * hl * uy + sy * hw * vy)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def sat_overlap(a, b, clearance):
    """a, b = (cx, cy, hl, hw, ux, uy). True neu 2 hinh cach nhau < clearance."""
    ax, ay, ahl, ahw, aux, auy = a
    bx, by, bhl, bhw, bux, buy = b
    dx, dy = bx - ax, by - ay
    r = ahl + ahw + bhl + bhw + clearance
    if dx * dx + dy * dy > r * r:
        return False
    for px, py in ((aux, auy), (-auy, aux), (bux, buy), (-buy, bux)):
        ra = ahl * abs(aux * px + auy * py) + ahw * abs(-auy * px + aux * py)
        rb = bhl * abs(bux * px + buy * py) + bhw * abs(-buy * px + bux * py)
        if abs(dx * px + dy * py) >= ra + rb + clearance - 0.05:   # dung sai 0.05mm
            return False
    return True


class Layout:
    def __init__(self, poly, cfg):
        self.poly, self.cfg, self.leds = poly, cfg, []
        self.clear = min(cfg.gap, cfg.row_gap)
        self.tags = []
        self.nodes = [c for ring in [poly.exterior, *poly.interiors] for c in ring.coords]

    def inside(self, x, y):                      # = Curve.IsOnCurve(...) = cdrInsideShape
        return self.poly.contains(Point(x, y))

    def fits_shape(self, led):
        """Ca LED (noi rong them margin) nam trong chu."""
        cx, cy, hl, hw, ux, uy = led
        m = self.cfg.margin - 0.3          # dung sai lam tron
        cs = rect_corners(cx, cy, hl + m, hw + m, ux, uy)
        for i in range(4):                        # lay mau chu vi, moi ~3mm
            (x1, y1), (x2, y2) = cs[i], cs[(i + 1) % 4]
            n = max(2, int(math.hypot(x2 - x1, y2 - y1) / 3) + 1)
            for k in range(n):
                t = k / n
                if not self.inside(x1 + t * (x2 - x1), y1 + t * (y2 - y1)):
                    return False
        # dinh nhon cua chu khong duoc dam vao LED
        vx, vy = -uy, ux
        for nx, ny in self.nodes:
            dx, dy = nx - cx, ny - cy
            if abs(dx * ux + dy * uy) < hl + m and abs(dx * vx + dy * vy) < hw + m:
                return False
        return True

    def try_add(self, led, idx=0):
        for o in self.leds:
            if sat_overlap(o, led, self.clear):
                return False
        if not self.fits_shape(led):
            return False
        self.leds.append(led)
        self.tags.append((getattr(self, "cur_seq", (0, 0)), idx))
        return True

    # ---------- Chia duong bao thanh cac doan ----------
    def runs(self, step=None):
        step = step or self.cfg.step
        out = []
        for ring in [self.poly.exterior, *self.poly.interiors]:
            line = LineString(ring.coords)
            Ltot = line.length
            n = int(round(Ltot / step))
            pts = [line.interpolate(i * Ltot / n) for i in range(n)]
            ang = []
            for i in range(n):
                a, b = pts[i - 1], pts[(i + 1) % n]
                ang.append(math.atan2(b.y - a.y, b.x - a.x))
            cut = [i for i in range(n)
                   if abs(math.degrees(math.remainder(ang[(i + 2) % n] - ang[i - 2], 2 * math.pi))) > self.cfg.corner]
            if not cut:
                out.append(pts)
                continue
            # gom cac diem cat lien nhau
            groups, cur = [], [cut[0]]
            for c in cut[1:]:
                if c - cur[-1] <= 3:
                    cur.append(c)
                else:
                    groups.append(cur); cur = [c]
            groups.append(cur)
            if len(groups) > 1 and groups[0][0] + n - groups[-1][-1] <= 3:
                groups[0] = groups[-1] + groups[0]; groups.pop()
            cps = [g[len(g) // 2] for g in groups]
            for i, s in enumerate(cps):
                e = cps[(i + 1) % len(cps)]
                idx = list(range(s, e)) if e > s else list(range(s, n)) + list(range(0, e))
                if len(idx) > 3:
                    out.append([pts[j] for j in idx])
        out.sort(key=len, reverse=True)          # doan dai lam truoc
        return out

    def depth(self, x, y, vx, vy):
        """Be rong net tu diem bien (x,y) theo huong (vx,vy): buoc 5mm roi chia doi."""
        lo, hi = 0.0, 5.0
        while hi < 5000 and self.inside(x + vx * hi, y + vy * hi):
            lo, hi = hi, hi + 5.0
        for _ in range(4):
            mid = (lo + hi) / 2
            if self.inside(x + vx * mid, y + vy * mid):
                lo = mid
            else:
                hi = mid
        return lo

    def normals(self, pts):
        """Tiep tuyen + phap tuyen huong vao trong tai tung diem."""
        out = []
        for i, p in enumerate(pts):
            q, r = pts[max(0, i - 3)], pts[min(len(pts) - 1, i + 3)]
            ux, uy = r.x - q.x, r.y - q.y
            dd = math.hypot(ux, uy) or 1
            ux, uy = ux / dd, uy / dd
            vx, vy = -uy, ux
            if not self.inside(p.x + vx * 1.0, p.y + vy * 1.0):
                vx, vy = -vx, -vy
            out.append((ux, uy, vx, vy))
        return out

    def fill_run(self, pts, across, ps):
        """ps = so buoc do giua 2 LED lien tiep trong 1 hang."""
        c = self.cfg
        m = c.margin
        hl, hw = c.L / 2, c.W / 2
        size_n = c.L if across else c.W        # kich thuoc LED theo chieu ngang net
        nrm = self.normals(pts)
        step = math.hypot(pts[1].x - pts[0].x, pts[1].y - pts[0].y) if len(pts) > 1 else 1
        closed = math.hypot(pts[-1].x - pts[0].x, pts[-1].y - pts[0].y) < 2 * step
        half = max(1, int(round(hl / step)))
        depths = [self.depth(p.x, p.y, v[2], v[3]) for p, v in zip(pts, nrm)]
        med = sorted(depths)[len(depths) // 2]
        rows = {}
        for i, (p, (ux, uy, vx, vy), D) in enumerate(zip(pts, nrm, depths)):
            if D > med:                         # tia xuyen sang net khac: giu so cot deu
                D = med
            avail = D - 2 * m
            if avail < size_n:
                continue
            n = int((avail + c.row_gap) / (size_n + c.row_gap))
            start = m + (avail - (n * size_n + (n - 1) * c.row_gap)) / 2
            for k in range(n):
                off = start + size_n / 2 + k * (size_n + c.row_gap)
                cx, cy = p.x + vx * off, p.y + vy * off
                if across:
                    led = (cx, cy, hl, hw, vx, vy)
                else:
                    # LED doc net: dat theo day cung cua duong chay (om theo net cong)
                    ia, ib = i - half, i + half
                    if closed:
                        ia, ib = ia % len(pts), ib % len(pts)
                    if 0 <= ia < len(pts) and 0 <= ib < len(pts):
                        pa, pb = pts[ia], pts[ib]
                        ax_, ay_ = pa.x + nrm[ia][2] * off, pa.y + nrm[ia][3] * off
                        bx_, by_ = pb.x + nrm[ib][2] * off, pb.y + nrm[ib][3] * off
                        dx_, dy_ = bx_ - ax_, by_ - ay_
                        dd = math.hypot(dx_, dy_) or 1
                        led = ((ax_ + bx_) / 2, (ay_ + by_) / 2, hl, hw, dx_ / dd, dy_ / dd)
                    else:
                        led = (cx, cy, hl, hw, ux, uy)
                rows.setdefault(k, []).append((i, led))
        self.run_id = getattr(self, "run_id", 0) + 1
        phase0 = None
        for k in sorted(rows):
            self.cur_seq = (self.run_id, k)
            ph = None if phase0 is None else phase0 + (k % 2) * (ps // 2 if self.cfg.stagger else 0)
            used = self.place_row(rows[k], ps, ph)
            if phase0 is None and used is not None:
                phase0 = used - (k % 2) * (ps // 2 if self.cfg.stagger else 0)

    def ok(self, led):
        return all(not sat_overlap(o, led, self.clear) for o in self.leds) and self.fits_shape(led)

    def place_row(self, cands, ps, phase):
        """Dat LED cach deu ps buoc. Hang dau tien: can giua khoang trong va
        tra ve 'pha'; cac hang sau dung cung pha de LED thang cot."""
        valid = [(i, led) for i, led in cands if self.ok(led)]
        segs, cur = [], []
        for i, led in valid:
            if cur and i - cur[-1][0] > 1:
                segs.append(cur); cur = []
            cur.append((i, led))
        if cur:
            segs.append(cur)
        for seg in segs:
            a, b = seg[0][0], seg[-1][0]
            by_idx = dict(seg)
            if phase is None:
                cnt = (b - a) // ps + 1
                phase = a + ((b - a) - (cnt - 1) * ps) // 2
            l0 = seg[0][1]
            straight = all(l0[4] * l[4] + l0[5] * l[5] > math.cos(math.radians(10)) for _, l in seg)
            if straight:                     # doan thang: cach deu, thang cot
                first = a + (phase - a) % ps
                for i in range(first, b + 1, ps):
                    if i in by_idx:
                        self.try_add(by_idx[i])
            # Doan cong: lap cho trong con lai (doan thang da kin nen khong them gi)
            for i, led in seg:
                self.try_add(led, i)
        return phase

    def run(self, mode="auto", fill_gaps=True):
        c = self.cfg
        self.seq_key = None
        passes = []
        if mode in ("auto", "across"):
            passes.append((True, c.W + c.gap))       # LED nam ngang net
        if (mode == "along" or (mode == "auto" and fill_gaps)) and not (mode == "auto" and c.L == c.W):
            passes.append((False, c.L + c.gap))      # LED nam doc net
        for across, pitch in passes:
            ps = max(1, math.ceil(pitch / c.step))
            step = pitch / ps                        # buoc do chia het buoc LED
            for pts in self.runs(step):
                self.fill_run(pts, across, ps)
        return self.leds


def check(lay):
    bad = sum(1 for i, a in enumerate(lay.leds) for b in lay.leds[i + 1:] if sat_overlap(a, b, 0))
    out = sum(1 for l in lay.leds if not lay.poly.contains(Polygon(rect_corners(*l))))
    return bad, out


def draw(ax, lay, title):
    x, y = lay.poly.exterior.xy
    ax.plot(x, y, "k-", lw=1.2)
    for ring in lay.poly.interiors:
        x, y = ring.xy
        ax.plot(x, y, "k-", lw=1.2)
    for l in lay.leds:
        cs = rect_corners(*l)
        ax.fill([p[0] for p in cs], [p[1] for p in cs], fc="#4da3ff", ec="#003a80", lw=0.6)
    bad, out = check(lay)
    ax.set_title(f"{title}\n{len(lay.leds)} LED | chong nhau: {bad} | lan ra ngoai: {out}", fontsize=10)
    ax.set_aspect("equal"); ax.axis("off")


if __name__ == "__main__":
    s = 600 / (775 - 266)   # do tu anh chup: chu A cao 600mm
    P = lambda pts: [((px - 93) * s, (775 - py) * s) for px, py in pts]
    A = Polygon(P([(93, 775), (290, 266), (400, 266), (603, 775), (492, 775),
                   (447, 658), (243, 658), (202, 775)]),
                [P([(344, 385), (275, 573), (414, 573)])])
    SQ = Polygon([(0, 0), (500, 0), (500, 420), (0, 420)])
    O = Point(0, 0).buffer(300, 64).difference(Point(0, 0).buffer(190, 64))

    fig, axs = plt.subplots(1, 3, figsize=(18, 7))
    for ax, (shape, name) in zip(axs, [(A, "Chu A cao 600mm"), (SQ, "Hinh vuong 500x420"), (O, "Chu O (thu net cong)")]):
        lay = Layout(shape, Cfg())
        lay.run()
        draw(ax, lay, name)
        print(name, len(lay.leds), check(lay))
    fig.suptitle("AutoLED Pro - module 65x15mm, cach mep 10mm, khe ho 10mm", fontsize=13)
    plt.tight_layout()
    plt.savefig("preview.png", dpi=110)
