"""
Mo phong duong di day LED noi tiep.
  - Moi "chuoi" = cac LED cung 1 hang tren 1 doan net, xep theo thu tu doc net.
  - Noi cac chuoi: tu diem hien tai, di toi dau chuoi gan nhat (tu nhien thanh zic-zac).
  - Moi LED co 2 dau (dau vao / dau ra) o 2 dau canh dai; tu chon chieu de day ngan nhat.
  - Tach day moi khi du so LED toi da tren 1 day.
"""
import math


def led_ends(led):
    cx, cy, hl, hw, ux, uy = led
    return (cx - ux * hl, cy - uy * hl), (cx + ux * hl, cy + uy * hl)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def outside_ratio(inside, a, b, n=10):
    """Ti le doan day a-b nam ngoai chu."""
    bad = sum(1 for k in range(1, n) if not inside(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
    return bad / (n - 1)


def build_chains(leds, tags, max_per_wire=30, inside=None):
    seqs = {}
    for n, (key, idx) in enumerate(tags):
        seqs.setdefault(key, []).append((idx, n))
    seqs = [[n for _, n in sorted(v)] for v in seqs.values()]
    # tach chuoi neu 2 LED lien tiep qua xa (vi du bi ngat o giao net)
    parts = []
    for s in seqs:
        cur = [s[0]]
        for a, b in zip(s, s[1:]):
            if dist(leds[a][:2], leds[b][:2]) > 3 * (leds[a][2] + leds[a][3]):
                parts.append(cur); cur = []
            cur.append(b)
        parts.append(cur)

    # diem bat dau: LED thap nhat ben trai (goc duoi trai chu)
    order, used = [], [False] * len(parts)
    start = min(range(len(parts)), key=lambda i: min(leds[n][1] + 0.3 * leds[n][0] for n in parts[i]))
    cur_pt = None
    i = start
    rev = False
    while i is not None:
        used[i] = True
        seq = parts[i][::-1] if rev else parts[i]
        order.extend(seq)
        cur_pt = leds[seq[-1]][:2]
        best, i, rev = None, None, False
        for j, p in enumerate(parts):
            if used[j]:
                continue
            for r, end in ((False, p[0]), (True, p[-1])):
                d = dist(cur_pt, leds[end][:2])
                if inside is not None:          # phat day chay ra ngoai chu
                    d *= 1 + 5 * outside_ratio(inside, cur_pt, leds[end][:2])
                if best is None or d < best:
                    best, i, rev = d, j, r

    # chon dau vao/dau ra cho tung LED va chia day
    wires, pts = [], []
    prev_out = None
    for k, n in enumerate(order):
        a, b = led_ends(leds[n])
        if prev_out is None:
            nxt = leds[order[k + 1]][:2] if k + 1 < len(order) else b
            inp, out = (a, b) if dist(b, nxt) < dist(a, nxt) else (b, a)
        else:
            inp, out = (a, b) if dist(prev_out, a) <= dist(prev_out, b) else (b, a)
        if len(pts) // 2 >= max_per_wire:
            wires.append(pts); pts = []; prev_out = None
            nxt = leds[order[k + 1]][:2] if k + 1 < len(order) else b
            inp, out = (a, b) if dist(b, nxt) < dist(a, nxt) else (b, a)
        pts += [inp, out]
        prev_out = out
    if pts:
        wires.append(pts)
    return wires
