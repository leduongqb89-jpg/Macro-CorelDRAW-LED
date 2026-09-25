"""Lay duong vien chu that tu font -> shapely (mm). Giu lo (O, A...) va dau tieng Viet."""
import os
import matplotlib
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

FONT_DIR = os.path.join(os.path.dirname(matplotlib.__file__), "mpl-data/fonts/ttf")
FONTS = {
    "sans": "DejaVuSans-Bold.ttf",
    "serif": "DejaVuSerif-Bold.ttf",
    "sans_it": "DejaVuSans-BoldOblique.ttf",
}


def glyph(ch, height=600.0, font="sans"):
    fp = FontProperties(fname=os.path.join(FONT_DIR, FONTS[font]))
    tp = TextPath((0, 0), ch, size=100, prop=fp)
    rings = [Polygon(p) for p in tp.to_polygons(closed_only=True) if len(p) >= 4]
    rings = [r.buffer(0) for r in rings if r.area > 1e-3]
    # chan-le: vong nam trong so le vong khac la lo
    rings.sort(key=lambda r: -r.area)
    parts = []
    for i, r in enumerate(rings):
        depth = sum(1 for j in range(i) if rings[j].contains(r.representative_point()))
        parts.append((depth, r))
    shape = None
    for depth, r in parts:
        if shape is None:
            shape = r
        elif depth % 2 == 0:
            shape = shape.union(r)
        else:
            shape = shape.difference(r)
    minx, miny, maxx, maxy = shape.bounds
    k = height / (maxy - miny)
    from shapely.affinity import affine_transform
    shape = affine_transform(shape, [k, 0, 0, k, -minx * k, -miny * k])
    return shape.buffer(0)
