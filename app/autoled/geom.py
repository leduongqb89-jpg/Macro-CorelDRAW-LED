"""Hinh hoc: ghep cac vong kin thanh hinh co lo (chan-le), tim truc doi xung, bezier."""
import numpy as np
from shapely.geometry import Polygon
from shapely.affinity import scale as sscale


def rings_to_shape(rings):
    """rings: list cac list diem (x, y). Vong nam trong so le vong khac la lo."""
    polys = []
    for r in rings:
        if len(r) >= 3:
            p = Polygon(r).buffer(0)
            if p.area > 1e-3:
                polys.append(p)
    if not polys:
        return None
    polys.sort(key=lambda p: -p.area)
    shape = None
    for i, p in enumerate(polys):
        depth = sum(1 for j in range(i) if polys[j].contains(p.representative_point()))
        if shape is None:
            shape = p
        elif depth % 2 == 0:
            shape = shape.union(p)
        else:
            shape = shape.difference(p)
    return shape.buffer(0)


def cubic(p0, p1, p2, p3, n=16):
    out = []
    for k in range(n):
        t = k / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def symmetry_axis(shape, tol=0.985):
    x0, y0, x1, y1 = shape.bounds
    best = None
    for dx in np.linspace(-0.03, 0.03, 25) * (x1 - x0):
        ax = (x0 + x1) / 2 + dx
        m = sscale(shape, xfact=-1, yfact=1, origin=(ax, 0))
        u = shape.union(m).area
        iou = shape.intersection(m).area / u if u > 0 else 0
        if best is None or iou > best[0]:
            best = (iou, ax)
    return best[1] if best and best[0] >= tol else None
