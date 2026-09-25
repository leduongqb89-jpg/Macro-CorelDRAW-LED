"""
DI DAY (ban 2) - chi dung danh sach LED cuoi cung (de chuyen sang VBA de dang).
  D1  Moi LED co huong truc u. Noi 2 LED lien tiep "theo huong truc" (lech <= 30 do,
      khoang cach <= 1.7 buoc) -> thanh cac CHUOI (cot / vong).
  D2  Sap thu tu chuoi kieu zic-zac: tu diem nguon, luon di toi dau chuoi gan nhat;
      phat nang doan day chay ra ngoai chu.
  D3  Chia day CAN BANG: k = tran(N / toi_da) day, moi day ~ N/k LED, uu tien cat o DAU chuoi.
  D4  Diem nguon chung: ve day cap nguon tu nguon toi dau vao (IN) cua tung day.
"""
import math


def ends(led, t):
    cx, cy, ux, uy = led
    if t.kind == "dot":
        return (cx, cy), (cx, cy)
    return (cx - ux * t.L / 2, cy - uy * t.L / 2), (cx + ux * t.L / 2, cy + uy * t.L / 2)


def build_chains(leds, t, step):
    n = len(leds)
    nxt, prv = [-1] * n, [-1] * n
    cand = []
    for i in range(n):
        xi, yi, ui, vi = leds[i]
        for j in range(n):
            if i == j:
                continue
            dx, dy = leds[j][0] - xi, leds[j][1] - yi
            d = math.hypot(dx, dy)
            if d < 1e-6 or d > 1.7 * step:
                continue
            c = abs(dx * ui + dy * vi) / d                  # lech so voi truc
            if c < math.cos(math.radians(30)):
                continue
            # 2 LED phai cung huong (module)
            if t.kind != "dot" and abs(ui * leds[j][2] + vi * leds[j][3]) < math.cos(math.radians(35)):
                continue
            cand.append((d * (2 - c), i, j, dx * ui + dy * vi > 0))
    cand.sort()
    for _, i, j, fwd in cand:
        a, b = (i, j) if fwd else (j, i)
        if nxt[a] == -1 and prv[b] == -1:
            # tranh vong kin
            k = b
            while nxt[k] != -1:
                k = nxt[k]
            if k == a:
                continue
            nxt[a], prv[b] = b, a
    chains = []
    for i in range(n):
        if prv[i] == -1:
            ch = [i]
            while nxt[ch[-1]] != -1:
                ch.append(nxt[ch[-1]])
            chains.append(ch)
    seen = {i for c in chains for i in c}
    for i in range(n):                                    # vong kin con sot
        if i not in seen:
            ch = [i]
            while nxt[ch[-1]] != -1 and nxt[ch[-1]] not in seen and nxt[ch[-1]] != i:
                ch.append(nxt[ch[-1]]); seen.add(ch[-1])
            seen.add(i)
            chains.append(ch)
    return chains


def order_chains(chains, leds, feed, inside=None):
    left = list(range(len(chains)))
    order, cur = [], feed
    def seg_out(a, b):
        if inside is None:
            return 0.0
        bad = sum(1 for k in range(1, 8) if not inside(a[0] + (b[0] - a[0]) * k / 8, a[1] + (b[1] - a[1]) * k / 8))
        return bad / 7
    while left:
        best = None
        for ci in left:
            ch = chains[ci]
            for rev, end in ((False, ch[0]), (True, ch[-1])):
                p = leds[end][:2]
                d = math.dist(cur, p) * (1 + 20 * seg_out(cur, p))   # phat nang day chay ra ngoai chu
                if best is None or d < best[0]:
                    best = (d, ci, rev)
        _, ci, rev = best
        left.remove(ci)
        ch = chains[ci][::-1] if rev else chains[ci]
        order.append(ch)
        cur = leds[ch[-1]][:2]
    return order


def split_wires(order, max_per, leds=None, step=None, inside=None):
    N = sum(len(c) for c in order)
    k = max(1, math.ceil(N / max_per))
    target = N / k
    wires, cur = [], []
    for ch in order:
        # K29: noi qua xa / chay ra ngoai chu -> keo day moi tu nguon
        if cur and leds is not None:
            a, b = leds[cur[-1]][:2], leds[ch[0]][:2]
            far = math.dist(a, b) > 3 * step
            out = inside is not None and any(not inside(a[0] + (b[0] - a[0]) * q / 8, a[1] + (b[1] - a[1]) * q / 8)
                                             for q in range(1, 8))
            if far or out:
                wires.append(cur); cur = []
        if cur and len(cur) + len(ch) > target * 1.12 and len(wires) < k - 1:
            wires.append(cur); cur = []
        for i in ch:
            cur.append(i)
            if len(cur) >= max_per:
                wires.append(cur); cur = []
    if cur:
        wires.append(cur)
    return wires


def wire_paths(wires, leds, t):
    paths = []
    for w in wires:
        pts, prev = [], None
        for q, i in enumerate(w):
            a, b = ends(leds[i], t)
            if prev is None:
                nx = leds[w[q + 1]][:2] if q + 1 < len(w) else b
                inp, out = (a, b) if math.dist(b, nx) <= math.dist(a, nx) else (b, a)
            else:
                inp, out = (a, b) if math.dist(prev, a) <= math.dist(prev, b) else (b, a)
            pts += [inp, out] if inp != out else [inp]
            prev = out
        paths.append(pts)
    return paths


def plan(leds, t, step, max_per=20, feed=None, inside=None):
    if not leds:
        return [], []
    if feed is None:                                          # mac dinh: goc duoi trai
        feed = min((l[:2] for l in leds), key=lambda p: p[1] + 0.5 * p[0])
    chains = build_chains(leds, t, step)
    order = order_chains(chains, leds, feed, inside)
    wires = split_wires(order, max_per, leds, step, inside)
    return wires, wire_paths(wires, leds, t)
