"""Thu quy trinh AutoLED tren CorelDRAW gia lap."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "lab"))
from glyphs import glyph
from mock_corel import App, shape_from_polygon, bezier_circle
from autoled import library, core, corel
from shapely.geometry import Point

lib = library.load()
app = App()
A = shape_from_polygon(app, glyph("A", 600))
O = shape_from_polygon(app, glyph("O", 600))
C = bezier_circle(app, 1000, 300, 250)
# nhom chua O + hinh tron bezier
grp = __import__("mock_corel").Shape(7, app.ActiveDocument.ActivePage.Layers.Item(1))
grp.Shapes = __import__("mock_corel").Coll([O, C])
app.ActiveSelectionRange.items = [A, grp]

for spec in (lib[0], lib[2], lib[4]):
    opts = core.Options(holes=True, hole_d=10)
    n, w, rep, res, sp_ = core.run(app, spec, opts, progress=lambda m: None)
    print(f"--- {spec.name}: {n} LED, {w} day")
    print(rep)
    assert n > 0 and w > 0
    assert app.ActiveDocument.groups == 0, "BeginCommandGroup/EndCommandGroup khong can"
    assert app.ActiveDocument.Unit == 1, "khong tra lai don vi"
    ss = corel.Session(app)
    cnt = ss.count_leds()
    assert cnt == n, (cnt, n)
    # hinh tron bezier: LED phai nam trong vong tron
    print("dem LED:", cnt, "xoa:", ss.clear())
    assert ss.count_leds() == 0
# doc hinh tron bezier dung ban kinh
from autoled.geom import rings_to_shape
shp = rings_to_shape(corel.curve_rings(C))
print("tron bezier dien tich %.0f (ly thuyet %.0f)" % (shp.area, 3.14159 * 250 ** 2))
assert abs(shp.area - 3.14159 * 250 ** 2) / (3.14159 * 250 ** 2) < 0.01
print("TAT CA OK")
