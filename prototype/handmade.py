"""
Vi du xep LED "bang tay" theo tu duy nguoi thiet ke (chua dung thuat toan tu dong).
Chu A: tach thanh chan trai / chan phai (lat guong) / thanh ngang / dinh.
  - Trong chan chu: cot LED song song canh chan, HANG NAM NGANG (song song chan de).
  - Chia deu khoang du, doi xung trai-phai.
  - Thanh ngang: chi lap phan giua 2 chan, cach LED cua chan dung 1 khoang.
"""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point, LineString
from shapely.affinity import scale as sscale
from led_layout import rect_corners, sat_overlap, Layout, Cfg, draw
from exposed_rows import RowDots
from wiring import build_chains

s = 600 / (775 - 266)
T = lambda p: ((p[0] - 93) * s, (775 - p[1]) * s)
OUT = [T(p) for p in [(93, 775), (290, 266), (400, 266), (603, 775), (492, 775), (447, 658), (243, 658), (202, 775)]]
HOLE = [T(p) for p in [(344, 385), (275, 573), (414, 573)]]
A = Polygon(OUT, [HOLE])
XC = (OUT[0][0] + OUT[3][0]) / 2            # truc doi xung
Y0, Y1 = OUT[0][1], OUT[1][1]               # day, dinh
YCB, YCT = OUT[5][1], HOLE[1][1]            # thanh ngang: day, dinh


def xline(p, q, y):
    return p[0] + (q[0] - p[0]) * (y - p[1]) / (q[1] - p[1])

# canh ngoai chan trai: OUT[0]->OUT[1]; canh trong: canh trai lo tam giac (keo dai)
xo = lambda y: xline(OUT[0], OUT[1], y)
xi = lambda y: xline(HOLE[1], HOLE[0], y)
th = math.atan2(OUT[1][1] - OUT[0][1], OUT[1][0] - OUT[0][0])   # goc chan (~68 do)
ux, uy = math.cos(th), math.sin(th)                               # huong doc chan
leg_w = (xi(0) - xo(0)) * math.sin(th)                            # be rong chan (vuong goc)


def mirror(x, y, dx=None, dy=None):
    return (2 * XC - x, y) if dx is None else (2 * XC - x, y, -dx, dy)


def fits_rect(poly, led, m):
    return poly.buffer(-m + 0.3).contains(Polygon(rect_corners(*led)))


# ---------------------------------------------------------------- 1. LED hat duc lo
def dots_A(P=25.0, D=9.0, m=6.0):
    e = m + D / 2
    pts = []
    inner = A.buffer(-e + 0.2)
    # cot trong chan: chia deu be rong chan
    nc = round((leg_w - 2 * e) / P) + 1
    tcols = [e + k * (leg_w - 2 * e) / (nc - 1) for k in range(nc)]
    # hang ngang: chia deu chieu cao chu
    nr = round((Y1 - Y0 - 2 * e) / P) + 1
    rows = [Y0 + e + k * (Y1 - Y0 - 2 * e) / (nr - 1) for k in range(nr)]
    leg = []
    for y in rows:
        for t in tcols:
            x = xo(y) + t / math.sin(th)
            if x < XC - 0.6 * P / 2 and inner.contains(Point(x, y)):
                leg.append((x, y))
    pts += leg + [mirror(x, y) for x, y in leg]
    # thanh ngang: cac hang nam trong thanh ngang, chia deu giua 2 chan
    for y in [r for r in rows if YCB + e - 0.5 <= r <= YCT - e + 0.5]:   # cung hang voi chan
        xa = xo(y) + (tcols[-1] + P) / math.sin(th)       # cach cot trong cung 1 buoc
        xb = 2 * XC - xa
        n = round((xb - xa) / P) + 1
        for j in range(n):
            pts.append((xa + j * (xb - xa) / (n - 1), y))
    # dinh chu: 1 hang ngang sat canh tren, chia deu
    return pts


# ---------------------------------------------------------------- 2. Module trong hop chu
def modules_A(L=65.0, W=15.0, m=10.0, gap=25.0, cgap=12.0):
    leds = []
    # cot module song song chan, chia deu be rong chan
    nc = int((leg_w - 2 * m + cgap) / (W + cgap))
    used = nc * W + (nc - 1) * cgap
    tcols = [m + (leg_w - 2 * m - used) / 2 + W / 2 + k * (W + cgap) for k in range(nc)]
    hv = L * math.sin(th) + W * math.cos(th)            # chieu cao that cua module nghieng
    pitch = (L + gap) * math.sin(th)                    # buoc hang theo chieu dung
    nr = int((Y1 - Y0 - 2 * m - hv) / pitch) + 1
    y_start = Y0 + m + hv / 2 + ((Y1 - Y0 - 2 * m - hv) - (nr - 1) * pitch) / 2
    left = []
    for r in range(nr):
        y = y_start + r * pitch
        for t in tcols:
            x = xo(y) + t / math.sin(th)
            led = (x, y, L / 2, W / 2, ux, uy)
            cs = rect_corners(*led)
            if max(c[0] for c in cs) > XC - cgap / 2:     # khong vuot truc doi xung
                continue
            if fits_rect(A, led, m):
                left.append(led)
    right = [(2 * XC - x, y, hl, hw, -a, b) for x, y, hl, hw, a, b in left]
    leds += left + right
    # thanh ngang: module nam ngang, xep gach (so le)
    ncb = int((YCT - YCB - 2 * m + cgap) / (W + cgap))
    usedv = ncb * W + (ncb - 1) * cgap
    for k in range(ncb):
        y = YCB + m + (YCT - YCB - 2 * m - usedv) / 2 + W / 2 + k * (W + cgap)
        # gioi han: cach module cua chan >= cgap
        xa = max([max(c[0] for c in rect_corners(*l)) for l in left
                  if min(c[1] for c in rect_corners(*l)) < y + W and max(c[1] for c in rect_corners(*l)) > y - W]
                 + [xi(y)]) + cgap
        xb = 2 * XC - xa
        n = int((xb - xa + cgap) / (L + cgap))
        if k % 2 == 1 and n > 1:
            n -= 1                                        # xep gach: hang le bot 1
        g = ((xb - xa) - n * L) / (n + 1)                 # chia deu khe
        for j in range(n):
            x = xa + g + L / 2 + j * (L + g)
            led = (x, y, L / 2, W / 2, 1.0, 0.0)
            if fits_rect(A, led, m):
                leds.append(led)
    return leds


def draw_poly(ax, poly):
    x, y = poly.exterior.xy; ax.plot(x, y, "k-", lw=1)
    for r in poly.interiors:
        x, y = r.xy; ax.plot(x, y, "k-", lw=1)
    ax.set_aspect("equal"); ax.axis("off")


def ends(l):
    x, y, hl, hw, a, b = l
    return (x - a * hl, y - b * hl), (x + a * hl, y + b * hl)


def order_A(leds):
    """Thu tu noi: chan trai (cot ngoai -> trong, zic-zac), thanh ngang (zic-zac), chan phai (trong -> ngoai)."""
    def tcol(l):
        x, y = l[0], l[1]
        if x < XC:
            return (x - xo(y)) * math.sin(th)
        return (2 * XC - x - xo(y)) * math.sin(th)
    L = [l for l in leds if not (l[4] == 1.0 and l[5] == 0.0) and l[0] < XC]
    R = [l for l in leds if not (l[4] == 1.0 and l[5] == 0.0) and l[0] >= XC]
    B = [l for l in leds if l[4] == 1.0 and l[5] == 0.0]
    def groups(items, key, tol):
        out = []
        for l in sorted(items, key=key):
            if out and abs(key(out[-1][-1]) - key(l)) < tol:
                out[-1].append(l)
            else:
                out.append([l])
        return out
    seq = []
    def push(items, key):
        # bat dau tu dau gan diem cuoi truoc do nhat
        items = sorted(items, key=key)
        last = next((l for l in reversed(seq) if l is not None), None)
        if last is not None and math.dist(last[:2], items[-1][:2]) < math.dist(last[:2], items[0][:2]):
            items.reverse()
        seq.extend(items)
    def push_nearest(cols, first):
        # cot dau tien co dinh, sau do luon chon cot co dau gan nhat
        cols = list(cols)
        push(cols.pop(first), lambda l: l[1])
        while cols:
            last = seq[-1][:2]
            j = min(range(len(cols)), key=lambda i: min(math.dist(last, cols[i][0][:2]),
                                                       math.dist(last, cols[i][-1][:2])))
            push(cols.pop(j), lambda l: l[1])
    def merge_lone(gs):
        # cot chi co 1 module: gop vao cot ben canh
        big = [g for g in gs if len(g) > 1]
        for g in gs:
            if len(g) <= 1 and big:
                j = min(range(len(big)), key=lambda i: abs(tcol(big[i][0]) - tcol(g[0])))
                big[j] = big[j] + g
        return big or gs
    colsL = [sorted(c, key=lambda l: l[1]) for c in merge_lone(groups(L, tcol, 5))]
    push_nearest(colsL, 0)                             # chan trai: bat dau tu cot ngoai
    colsR = [sorted(c, key=lambda l: l[1]) for c in merge_lone(groups(R, tcol, 5))]
    push_nearest(colsR, min(range(len(colsR)), key=lambda i: min(math.dist(seq[-1][:2], colsR[i][0][:2]),
                                                                  math.dist(seq[-1][:2], colsR[i][-1][:2]))))
    seq.append(None)                                   # thanh ngang: day rieng
    for row in groups(B, lambda l: -l[1], 5):
        push(row, lambda l: l[0])
    return seq


def draw_wires(ax, leds, poly, max_per=20):
    seq = order_A(leds)
    wires, cur, prev = [], [], None
    for k, l in enumerate(seq):
        if l is None:                                  # bat dau day moi
            if cur:
                wires.append(cur)
            cur, prev = [], None
            continue
        a, b = ends(l)
        if prev is None:
            nxt = seq[k + 1][:2] if k + 1 < len(seq) and seq[k + 1] is not None else b
            inp, out = (a, b) if math.dist(b, nxt) < math.dist(a, nxt) else (b, a)
        else:
            inp, out = (a, b) if math.dist(prev, a) <= math.dist(prev, b) else (b, a)
        cur += [inp, out]; prev = out
        if len(cur) // 2 >= max_per:
            wires.append(cur); cur, prev = [], None
    if cur:
        wires.append(cur)
    cols = ["#e41a1c", "#ff7f00", "#4daf4a", "#984ea3"]
    for w, pts in enumerate(wires):
        c = cols[w % 4]
        ax.plot([p[0] for p in pts], [p[1] for p in pts], "-", color=c, lw=1.2)
        ax.plot(*pts[0], "o", color=c, ms=7)
        ax.annotate(f"IN{w+1}", pts[0], xytext=(3, 3), textcoords="offset points", color=c, fontsize=8, weight="bold")
    return len(wires)


if __name__ == "__main__":
    fig, axs = plt.subplots(1, 4, figsize=(24, 7.5))
    # 1
    pts = dots_A()
    draw_poly(axs[0], A)
    for x, y in pts:
        axs[0].add_patch(plt.Circle((x, y), 4.5, color="#d62728"))
    axs[0].set_title(f"1. LED hat 9mm duc lo (buoc 25)\n{len(pts)} LED - cot song song chan, hang ngang, doi xung", fontsize=10)
    # 2
    leds = modules_A()
    draw_poly(axs[1], A)
    for l in leds:
        cs = rect_corners(*l)
        axs[1].fill([c[0] for c in cs], [c[1] for c in cs], fc="#4da3ff", ec="#003a80", lw=0.6)
    nw = draw_wires(axs[1], leds, A)
    axs[1].set_title(f"2. Module 65x15 trong hop chu\n{len(leds)} module - doc chan, thanh ngang xep gach, {nw} day", fontsize=10)
    # 3, 4: chu C
    ring = Point(0, 0).buffer(300, 128).difference(Point(0, 0).buffer(165, 128))
    C = ring.difference(Polygon([(0, 0), (400, -250), (400, 250)])).buffer(0)
    d = RowDots(C, P=25, D=9, margin=6); d.rows()
    draw_poly(axs[2], C)
    for x, y in d.pts:
        axs[2].add_patch(plt.Circle((x, y), 4.5, color="#d62728"))
    axs[2].set_title(f"3. Chu C - LED hat duc lo\n{len(d.pts)} LED - dong tam, chia deu be rong net", fontsize=10)
    c = Cfg(); c.gap = 25.0; c.row_gap = 12.0; c.margin = 10.0
    lay = Layout(C, c); lay.run(mode="along")
    draw(axs[3], lay, "")
    wires = build_chains(lay.leds, lay.tags, max_per_wire=20, inside=lay.inside)
    for w, p in enumerate(wires):
        col = ["#e41a1c", "#ff7f00", "#4daf4a"][w % 3]
        axs[3].plot([q[0] for q in p], [q[1] for q in p], "-", color=col, lw=1.2)
        axs[3].plot(*p[0], "o", color=col, ms=7)
    axs[3].set_title(f"4. Chu C - module 65x15 trong hop\n{len(lay.leds)} module - om theo net cong, {len(wires)} day", fontsize=10)
    plt.tight_layout(); plt.savefig("handmade.png", dpi=80)
