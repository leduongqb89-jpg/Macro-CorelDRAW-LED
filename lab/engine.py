"""
BO MAY XEP LED - phien ban 3 (thu nghiem, Python).
Quy tac rut ra tu cac vong truoc:
  Q1  Khoang cach tinh theo TAM BONG (P), khong theo canh LED.
  Q2  Tach chu thanh cac "doan bien" (cat o goc). Doan dai lam truoc.
  Q3  Moi net: cac "ray" (track) song song canh net, so ray chia deu vua be rong net.
  Q4  Net thang: LED tren cac ray thang hang voi nhau (luoi theo net).
      Net xien 45-85 do: hang LED nam NGANG va dung chung toan chu.
      Net gan nam ngang: ray bam theo hang ngang chung.
  Q5  Net cong: ray dong tam; tren moi ray chia deu, 2 dau ray neo dung mep dau net.
  Q6  Chu doi xung: chi xep nua trai roi lat guong.
  Q7  Khong bao gio chong nhau / lan mep (kiem tra ca than LED).
  Q8  Sau cung: lap cho toi.
Chi dung cac phep co san trong CorelDRAW: kiem tra diem trong chu, lay diem theo
chieu dai duong bien, (tuy chon) duong vien trong (Contour).
"""
import math
from dataclasses import dataclass
from shapely.geometry import Point, Polygon, LineString
from shapely.prepared import prep


# ------------------------------------------------------------------ hinh hoc LED
def corners(cx, cy, hl, hw, ux, uy):
    vx, vy = -uy, ux
    return [(cx + sx * hl * ux + sy * hw * vx, cy + sx * hl * uy + sy * hw * vy)
            for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def sat_close(a, b, hl, hw, clr):
    """2 LED cung kich thuoc cach nhau < clr ?"""
    ax, ay, aux, auy = a
    bx, by, bux, buy = b
    dx, dy = bx - ax, by - ay
    r = 2 * (hl + hw) + clr
    if dx * dx + dy * dy > r * r:
        return False
    for px, py in ((aux, auy), (-auy, aux), (bux, buy), (-buy, bux)):
        ra = hl * abs(aux * px + auy * py) + hw * abs(-auy * px + aux * py)
        rb = hl * abs(bux * px + buy * py) + hw * abs(-buy * px + bux * py)
        if abs(dx * px + dy * py) >= ra + rb + clr - 0.05:
            return False
    return True


@dataclass
class Run:
    pts: list          # [(x, y)]
    tan: list          # [(ux, uy)]
    nrm: list          # [(vx, vy)] huong vao trong
    dep: list          # be rong net tai tung diem
    med: float
    closed: bool
    straight: bool
    length: float


class Engine:
    def __init__(self, shape, t, stagger="auto", fill_dark=True, sym_axis=None, step=2.0):
        self.shape, self.t = shape, t
        self.ps = prep(shape)
        self.stagger, self.do_fill = stagger, fill_dark
        self.axis = sym_axis
        self.step = step
        self.leds = []                                  # (cx, cy, ux, uy)
        self.hl, self.hw = t.L / 2, t.W / 2
        m = t.margin
        self.core_c = prep(shape.buffer(-(m + min(self.hl, self.hw)) + 0.3))  # tam LED hop le (tho)
        self.fit_poly = prep(shape.buffer(-m + 0.4))
        # bong LED trai ra theo 2 truc
        us = [a for a, b in t.bulbs]; vs = [b for a, b in t.bulbs]
        self.spread_u = max(us) - min(us)
        self.spread_v = max(vs) - min(vs)
        # buoc tam LED de khoang cach bong qua khe = P
        self.pitch_u = max(t.L + t.min_gap, self.spread_u + t.P)
        self.pitch_v = max(t.W + t.min_gap, self.spread_v + t.P)
        if t.kind == "dot":
            self.pitch_u = self.pitch_v = max(t.L + t.min_gap, t.P)
        x0, y0, x1, y1 = shape.bounds
        self.bounds = (x0, y0, x1, y1)
        # Q4: hang ngang chung toan chu (cho LED hat)
        e = m + self.hw
        H = y1 - y0 - 2 * e
        n = max(1, round(H / self.pitch_v) + 1)
        self.rows_y = [y0 + e + (k * H / (n - 1) if n > 1 else H / 2) for k in range(n)]

    # ------------------------------------------------------------ kiem tra
    def inside(self, x, y):
        return self.ps.contains(Point(x, y))

    def fits(self, led):
        cx, cy, ux, uy = led
        if not self.core_c.contains(Point(cx, cy)):
            return False
        if self.t.kind == "dot":
            return self.fit_poly.contains(Point(cx, cy).buffer(self.hl, 12))
        return self.fit_poly.contains(Polygon(corners(cx, cy, self.hl, self.hw, ux, uy)))

    def free(self, led, leds=None):
        leds = self.leds if leds is None else leds
        if self.t.kind == "dot":
            lim = max(self.t.L + self.t.min_gap, 0.88 * self.t.P) ** 2
            return all((led[0] - o[0]) ** 2 + (led[1] - o[1]) ** 2 >= lim for o in leds)
        return all(not sat_close(o, led, self.hl, self.hw, self.t.min_gap) for o in leds)

    def side_ok(self, led):
        return self.axis is None or led[0] <= self.axis + 0.3 * self.pitch_u

    def add(self, led):
        if self.axis is not None and abs(led[0] - self.axis) < 0.3 * self.pitch_u:
            # dat dung truc doi xung; module tren truc phai nam ngang hoac dung
            ux, uy = led[2], led[3]
            if abs(ux) > abs(uy):
                ux, uy = 1.0, 0.0
            else:
                ux, uy = 0.0, 1.0
            led = (self.axis, led[1], ux, uy)
        if not self.side_ok(led) or not self.free(led) or not self.fits(led):
            return False
        self.leds.append(led)
        return True

    # ------------------------------------------------------------ doan bien
    def depth(self, x, y, vx, vy):
        lo, hi = 0.0, 4.0
        while hi < 6000 and self.inside(x + vx * hi, y + vy * hi):
            lo, hi = hi, hi + 4.0
        for _ in range(5):
            mid = (lo + hi) / 2
            if self.inside(x + vx * mid, y + vy * mid):
                lo = mid
            else:
                hi = mid
        return lo

    def runs(self):
        out = []
        polys = getattr(self.shape, "geoms", [self.shape])
        for poly in polys:
            for ring in [poly.exterior, *poly.interiors]:
                line = LineString(ring.coords)
                Lt = line.length
                n = max(12, int(round(Lt / self.step)))
                pts = [line.interpolate(i * Lt / n).coords[0] for i in range(n)]
                ang = [math.atan2(pts[(i + 1) % n][1] - pts[i - 1][1], pts[(i + 1) % n][0] - pts[i - 1][0])
                       for i in range(n)]
                w = 2
                turn = [abs(math.degrees(math.remainder(ang[(i + w) % n] - ang[i - w], 2 * math.pi))) for i in range(n)]
                cut = [i for i in range(n) if turn[i] > 28 and turn[i] >= max(turn[(i + d) % n] for d in range(-w, w + 1))]
                cs = []
                for c in cut:
                    if not cs or c - cs[-1] > 2 * w:
                        cs.append(c)
                if len(cs) > 1 and cs[0] + n - cs[-1] <= 2 * w:
                    cs.pop()
                segs = []
                if not cs:
                    segs.append((list(range(n)), True))
                else:
                    for a, b in zip(cs, cs[1:] + [cs[0] + n]):
                        idx = [k % n for k in range(a, b + 1)]
                        if len(idx) >= 4:
                            segs.append((idx, False))
                for idx, closed in segs:
                    out.append(self.make_run([pts[k] for k in idx], closed))
        out = [r for r in out if r is not None]
        # Q2: doan thang dai truoc, roi doan cong dai
        out.sort(key=lambda r: -r.length * (1.15 if r.straight else 1.0))
        return out

    def make_run(self, pts, closed):
        n = len(pts)
        tan, nrm, dep = [], [], []
        for i in range(n):
            a = pts[(i - 2) % n] if closed else pts[max(0, i - 2)]
            b = pts[(i + 2) % n] if closed else pts[min(n - 1, i + 2)]
            ux, uy = b[0] - a[0], b[1] - a[1]
            d = math.hypot(ux, uy) or 1
            ux, uy = ux / d, uy / d
            vx, vy = -uy, ux
            if not self.inside(pts[i][0] + vx * 0.8, pts[i][1] + vy * 0.8):
                vx, vy = -vx, -vy
            tan.append((ux, uy)); nrm.append((vx, vy))
            dep.append(self.depth(pts[i][0], pts[i][1], vx, vy))
        s = sorted(dep)
        med = s[int(len(s) * 0.3)]            # be rong that cua net (bo qua cho giao net)
        L = sum(math.dist(pts[i], pts[i + 1]) for i in range(n - 1))
        u0 = tan[n // 2]
        straight = (not closed) and all(u0[0] * u[0] + u0[1] * u[1] > math.cos(math.radians(7)) for u in tan[3:-3])
        return Run(pts, tan, nrm, dep, med, closed, straight, L)

    # ------------------------------------------------------------ chia ray (Q3)
    def tracks(self, D):
        """Vi tri cac ray (khoang cach tu bien) cho net rong D."""
        m = self.t.margin
        e = m + self.hw if self.t.kind == "module" else m + self.hl
        avail = D - 2 * e
        if avail < 0:
            return []
        if avail < 0.5 * self.pitch_v:
            return [D / 2]
        best = None
        for n in range(2, 80):
            p = avail / (n - 1)
            if p < (self.t.W if self.t.kind == "module" else self.t.L) + self.t.min_gap:
                break
            err = abs(p - self.pitch_v)
            if best is None or err < best[0]:
                best = (err, n)
        if best is None:
            return [D / 2]
        n = best[1]
        return [e + k * avail / (n - 1) for k in range(n)]

    def use_stagger(self, ntr):
        if self.t.kind == "dot":
            return False
        if self.stagger == "auto":
            return ntr >= 3 and ntr % 2 == 1
        return bool(self.stagger)

    # ------------------------------------------------------------ net thang
    def straight_run(self, r):
        ux, uy = r.tan[len(r.tan) // 2]
        vx, vy = r.nrm[len(r.nrm) // 2]
        ax, ay = r.pts[len(r.pts) // 2]          # goc = diem giua doan (diem sat goc khong tin cay)
        D = r.med
        offs = self.tracks(D)
        if not offs:
            return
        sn = abs(uy)                       # |sin| goc net so voi phuong ngang
        ext = D                            # cho phep ray chay qua goc vao net ke
        mid = offs[len(offs) // 2]
        # doan hop le cua ray giua
        ss = [s for s in frange(-r.length / 2 - ext, r.length / 2 + ext, 2.0)
              if self.core_c.contains(Point(ax + ux * s + vx * mid, ay + uy * s + vy * mid))]
        if not ss:
            return
        # lay khuc lien tuc chua giua doan
        s_lo, s_hi = contiguous(ss, 2.0, 0.0)
        stg = self.use_stagger(len(offs))
        if self.t.kind == "dot" and sn >= 0.7:
            # Q4: hang ngang chung
            for k, o in enumerate(offs):
                for y in self.rows_y:
                    s = (y - (ay + vy * o)) / uy
                    if s_lo - self.pitch_u <= s <= s_hi + self.pitch_u:
                        self.add((ax + ux * s + vx * o, y, ux, uy))
            return
        if self.t.kind == "dot" and sn < 0.3:
            # net gan nam ngang: moi hang ngang chung nam lot trong net la 1 ray
            m = self.t.margin + self.hl
            ys = [ay + vy * o for o in (m, D - m)]
            lo_y, hi_y = min(ys) - 0.3 * self.pitch_v, max(ys) + 0.3 * self.pitch_v
            inband = [(y - ay) / vy for y in self.rows_y if lo_y <= y <= hi_y]
            if inband:
                offs = inband
            # nguoc lai voi net doc: dung chung COT doc (noi tiep cot cua net doc)
            # doan hop le theo phuong ngang cua net nay
            xa_, xb_ = sorted((ax + ux * s_lo, ax + ux * s_hi))
            cx = self.stroke_columns(xa_, xb_)
            for o in offs:
                for x in cx:
                    s = (x - (ax + vx * o)) / ux if abs(ux) > 1e-6 else None
                    if s is not None:
                        self.add((x, ay + uy * s + vy * o, ux, uy))
            return
        # luoi theo net: cac LED thang hang vuong goc voi net, chia deu doc net
        span = s_hi - s_lo
        pitch = self.pitch_u if self.t.kind == "dot" else self.pitch_u
        if self.t.kind == "module":
            span_c = span - (self.hl - self.hw)     # tam module cach dau net them nua chieu dai
            s0 = s_lo + (self.hl - self.hw) / 2
        else:
            span_c, s0 = span, s_lo
        cnt = max(1, round(span_c / pitch) + 1)
        while cnt > 1 and span_c / (cnt - 1) < (self.t.L + self.t.min_gap if self.t.kind == "module" else pitch * 0.85):
            cnt -= 1
        step = span_c / (cnt - 1) if cnt > 1 else 0
        cols = [s0 + (q * step if cnt > 1 else span_c / 2) for q in range(cnt)]
        slanted_rows = self.t.kind == "module" and 0.7 <= sn <= 0.97
        for k, o in enumerate(offs):
            shift = step / 2 if (stg and k % 2 == 1) else 0
            row = cols if not shift else [c + shift for c in cols[:-1]]
            for s in row:
                if slanted_rows:
                    # hang module nam ngang: dich theo ray de cung do cao voi ray giua
                    s = s + (vy * (mid - o)) / uy
                self.add((ax + ux * s + vx * o, ay + uy * s + vy * o, ux, uy))

    def stroke_columns(self, xa, xb):
        """Cot cho 1 net ngang [xa, xb]: noi tiep cot cua net doc, phan vuon ra ngoai chia deu lai."""
        base = self.columns_x()
        known = getattr(self, "_known_cols", [])
        inside = [x for x in known if xa - 1 <= x <= xb + 1]
        if not inside:
            n = max(1, round((xb - xa) / self.pitch_u) + 1)
            return [xa + (k * (xb - xa) / (n - 1) if n > 1 else (xb - xa) / 2) for k in range(n)]
        cols = list(inside)
        parts = [(max(inside), xb), (xa, min(inside))]
        for a, b in parts:
            span = b - a
            if span <= 0.6 * self.pitch_u:
                continue
            if self.axis is not None and a < self.axis < b + 1e-6 and b > self.axis:
                # Q9: chia deu toi truc: 1 cot dung truc hoac 2 cot cach deu truc
                sp = self.axis - a
                n1 = max(1, round(sp / self.pitch_u))            # cot tren truc
                n2 = max(1, round(sp / self.pitch_u - 0.5))      # cap cot doi xung
                p1, p2 = sp / n1, sp / (n2 + 0.5)
                if abs(p1 - self.pitch_u) <= abs(p2 - self.pitch_u):
                    cols += [a + k * p1 for k in range(1, n1 + 1)]
                else:
                    cols += [a + k * p2 for k in range(1, n2 + 1)] + [self.axis + p2 / 2]
                continue
            n = max(1, round(span / self.pitch_u))
            cols += [a + k * span / n for k in range(1, n + 1)]
        return sorted(set(round(c, 3) for c in cols))

    def columns_x(self):
        """Cot doc chung: noi tiep luoi cua net doc da xep (neu co), nguoc lai chia deu be ngang chu."""
        if getattr(self, "_cols", None) is not None:
            return self._cols
        x0, y0, x1, y1 = self.bounds
        xs = sorted(l[0] for l in self.leds)
        cols = None
        if len(xs) > 4:
            # gom cac cot da co
            groups = []
            for x in xs:
                if groups and x - groups[-1][-1] < 0.3 * self.pitch_u:
                    groups[-1].append(x)
                else:
                    groups.append([x])
            cxs = [sum(g) / len(g) for g in groups if len(g) >= 3]
            self._known_cols = cxs
            if len(cxs) >= 2:
                diffs = sorted(b - a for a, b in zip(cxs, cxs[1:]) if b - a < 1.5 * self.pitch_u)
                if diffs:
                    p = diffs[len(diffs) // 2]
                    a = cxs[0]
                    k0 = int((a - x0) / p) + 1
                    cols = [a - k * p for k in range(k0, 0, -1)] + [a + k * p for k in range(int((x1 - a) / p) + 2)]
        if cols is None:
            e = self.t.margin + self.hl
            Wd = x1 - x0 - 2 * e
            n = max(1, round(Wd / self.pitch_u) + 1)
            cols = [x0 + e + (k * Wd / (n - 1) if n > 1 else Wd / 2) for k in range(n)]
        self._cols = cols
        return cols

    # ------------------------------------------------------------ net cong (Q5)
    def curved_run(self, r):
        n = len(r.pts)
        D = r.med
        offs_med = self.tracks(D)
        if not offs_med:
            return
        ntr = len(offs_med)
        for k in range(ntr):
            line = []
            for i in range(n):
                d = min(r.dep[i], D * 1.05)
                o = self.tracks(d)
                if len(o) != ntr:
                    o = [x * d / D for x in offs_med]      # co gian theo be rong
                ok = o[k]
                line.append((r.pts[i][0] + r.nrm[i][0] * ok, r.pts[i][1] + r.nrm[i][1] * ok))
            # cat thanh cac khuc hop le
            valid = [self.core_c.contains(Point(p)) for p in line]
            pieces, cur = [], []
            for p, v in zip(line, valid):
                if v:
                    cur.append(p)
                elif cur:
                    pieces.append(cur); cur = []
            if cur:
                if pieces and r.closed and valid[0]:
                    pieces[0] = cur + pieces[0]
                else:
                    pieces.append(cur)
            loop = r.closed and all(valid)
            for pc in pieces:
                self.place_on_polyline(pc, loop and len(pieces) == 1, k)

    def place_on_polyline(self, pc, loop, k):
        if len(pc) < 2:
            return
        if loop:
            pc = pc + [pc[0]]
        acc = [0.0]
        for a, b in zip(pc, pc[1:]):
            acc.append(acc[-1] + math.dist(a, b))
        Lp = acc[-1]
        pitch = self.pitch_u
        if self.t.kind == "module":
            end = self.hl - self.hw                    # dau module khong vuot dau khuc
        else:
            end = 0.0
        usable = Lp - (0 if loop else 2 * end)
        if usable < 0:
            usable, end = 0, Lp / 2
        if loop:
            cnt = max(1, round(Lp / pitch))
            ss = [q * Lp / cnt for q in range(cnt)]
        else:
            cnt = max(1, round(usable / pitch) + 1)
            ss = [end + (q * usable / (cnt - 1) if cnt > 1 else usable / 2) for q in range(cnt)]
        for s in ss:
            c = at(pc, acc, s)
            if self.t.kind == "module":
                a = at(pc, acc, max(0, s - self.hl)); b = at(pc, acc, min(Lp, s + self.hl))
                ux, uy = b[0] - a[0], b[1] - a[1]
                c = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            else:
                a = at(pc, acc, max(0, s - 1)); b = at(pc, acc, min(Lp, s + 1))
                ux, uy = b[0] - a[0], b[1] - a[1]
            d = math.hypot(ux, uy) or 1
            self.add((c[0], c[1], ux / d, uy / d))

    # ------------------------------------------------------------ lap cho toi (Q8)
    def fill_dark(self, thr=1.2):
        import numpy as np
        from shapely import contains_xy
        core = self.shape.buffer(-(self.t.margin + min(self.hl, self.hw)))
        if core.is_empty:
            return
        x0, y0, x1, y1 = core.bounds
        g = max(2.0, self.t.P / 6)
        X, Y = np.meshgrid(np.arange(x0, x1, g), np.arange(y0, y1, g))
        msk = contains_xy(core, X, Y)
        if self.axis is not None:
            msk &= X <= self.axis + 0.01
        Pp = np.stack([X[msk], Y[msk]], 1)
        if not len(Pp):
            return

        def bulbs(led):
            cx, cy, ux, uy = led
            return [(cx + ux * a - uy * b, cy + uy * a + ux * b) for a, b in self.t.bulbs]
        d = np.full(len(Pp), 1e9)
        for l in self.leds:
            for bx, by in bulbs(l):
                d = np.minimum(d, np.hypot(Pp[:, 0] - bx, Pp[:, 1] - by))
        tried = np.zeros(len(Pp), bool)
        for _ in range(400):
            cand = np.where(~tried & (d > thr * self.t.P))[0]
            if not len(cand):
                break
            i = cand[np.argmax(d[cand])]
            tried[i] = True
            px, py = Pp[i]
            near = min(self.leds, key=lambda l: (l[0] - px) ** 2 + (l[1] - py) ** 2) if self.leds else (0, 0, 1, 0)
            dirs = [(near[2], near[3]), (-near[3], near[2])] + \
                   [(math.cos(math.radians(a)), math.sin(math.radians(a))) for a in range(0, 180, 30)]
            for ux, uy in dirs:
                led = (px, py, ux, uy)
                if self.add(led):
                    for bx, by in bulbs(self.leds[-1]):
                        d = np.minimum(d, np.hypot(Pp[:, 0] - bx, Pp[:, 1] - by))
                    break

    # ------------------------------------------------------------ chay
    def anchor_rows(self, runs):
        """Q8: hang ngang neo vao moi mep nam ngang (cach mep e), giua 2 neo chia deu."""
        x0, y0, x1, y1 = self.bounds
        e = self.t.margin + self.hw
        anchors = [y0 + e, y1 - e]
        for r in runs:
            if not r.straight or r.length < 0.8 * self.pitch_u:
                continue
            ux, uy = r.tan[len(r.tan) // 2]
            vx, vy = r.nrm[len(r.nrm) // 2]
            if abs(uy) < 0.12 and r.med >= 2 * e:
                yb = sum(p[1] for p in r.pts) / len(r.pts)
                anchors.append(yb + (e if vy > 0 else -e))
        anchors = sorted(a for a in anchors if y0 + e - 1 <= a <= y1 - e + 1)
        merged = []
        for a in anchors:
            if merged and a - merged[-1] < 0.45 * self.pitch_v:
                merged[-1] = (merged[-1] + a) / 2
            else:
                merged.append(a)
        rows = [merged[0]]
        for a, b in zip(merged, merged[1:]):
            n = max(1, round((b - a) / self.pitch_v))
            rows += [a + k * (b - a) / n for k in range(1, n + 1)]
        self.rows_y = rows

    def run(self):
        runs = self.runs()
        if self.t.kind == "dot":
            self.anchor_rows(runs)
        for r in runs:
            if r.length < 1.2 * self.pitch_u and not r.closed:
                continue                      # doan qua ngan: khong tu tao luoi rieng
            if r.straight and r.med > 1.5 * r.length:
                continue                      # mep dau net (dau canh chu E...): khong phai canh ben
            if r.straight:
                self.straight_run(r)
            else:
                self.curved_run(r)
        if self.do_fill:
            self.fill_dark()
        if self.axis is not None:
            left = [l for l in self.leds if l[0] < self.axis - 0.01]
            for x, y, ux, uy in left:
                self.leds.append((2 * self.axis - x, y, -ux, uy))
        return self.leds


# ------------------------------------------------------------------ tien ich
def frange(a, b, st):
    x = a
    while x <= b:
        yield x
        x += st


def contiguous(ss, st, center):
    """Khuc lien tuc (buoc st) gan 'center' nhat."""
    groups, cur = [], [ss[0]]
    for s in ss[1:]:
        if s - cur[-1] > st * 1.5:
            groups.append(cur); cur = []
        cur.append(s)
    groups.append(cur)
    g = min(groups, key=lambda g: 0 if g[0] <= center <= g[-1] else min(abs(g[0] - center), abs(g[-1] - center)))
    return g[0], g[-1]


def at(pc, acc, s):
    import bisect
    j = min(len(acc) - 2, max(0, bisect.bisect_right(acc, s) - 1))
    seg = acc[j + 1] - acc[j] or 1
    f = (s - acc[j]) / seg
    a, b = pc[j], pc[j + 1]
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
