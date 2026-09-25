"""
Cau noi voi CorelDRAW qua COM (pywin32).
Chi dung thuoc tinh/phuong thuc don gian (khong dung tham so ByRef) de on dinh khi goi tu ngoai:
  - doc duong vien: Curve.SubPaths -> Segments -> StartNode/EndNode.PositionX/Y + diem dieu khien
  - ve: Layer.CreateEllipse2 / CreateRectangle2 / CreateCurve / CreateArtisticText
"""
import math

# Hang so CorelDRAW (dung khi khong co thu vien kieu)
CDR_MM = 3
T_RECT, T_ELLIPSE, T_CURVE, T_POLYGON, T_TEXT, T_GROUP = 1, 2, 3, 4, 6, 7
SEG_LINE, SEG_CURVE = 0, 1

LAYER_LED, LAYER_WIRE, LAYER_HOLE = "LED", "DAY", "LO_CAT"
SAMPLE_NAME = "LED_MAU"


class CorelError(Exception):
    pass


def connect():
    """Ket noi CorelDRAW dang mo (uu tien), neu khong thi mo moi."""
    try:
        import win32com.client as w
    except ImportError as e:
        raise CorelError("Thieu thu vien pywin32") from e
    progids = ["CorelDRAW.Application"] + [f"CorelDRAW.Application.{v}" for v in range(26, 16, -1)]
    for pid in progids:
        try:
            return w.GetActiveObject(pid)
        except Exception:
            pass
    for pid in progids:
        try:
            app = w.Dispatch(pid)
            try:
                app.Visible = True
            except Exception:
                pass
            return app
        except Exception:
            pass
    raise CorelError("Không kết nối được CorelDRAW. Hãy mở CorelDRAW (bản đầy đủ) rồi thử lại.")


def _items(coll):
    """Duyet 1 collection COM (chi so tu 1)."""
    n = int(coll.Count)
    for i in range(1, n + 1):
        yield coll.Item(i)


# ------------------------------------------------------------------ doc hinh
def _seg_points(seg):
    sx, sy = float(seg.StartNode.PositionX), float(seg.StartNode.PositionY)
    ex, ey = float(seg.EndNode.PositionX), float(seg.EndNode.PositionY)
    typ = int(seg.Type)
    if typ != SEG_CURVE:
        return [(sx, sy)]
    from .geom import cubic
    # diem dieu khien: thu X/Y truoc, sau do goc/do dai
    try:
        c1 = (float(seg.StartingControlPointX), float(seg.StartingControlPointY))
        c2 = (float(seg.EndingControlPointX), float(seg.EndingControlPointY))
    except Exception:
        a1, l1 = math.radians(float(seg.StartingControlPointAngle)), float(seg.StartingControlPointLength)
        a2, l2 = math.radians(float(seg.EndingControlPointAngle)), float(seg.EndingControlPointLength)
        c1 = (sx + l1 * math.cos(a1), sy + l1 * math.sin(a1))
        c2 = (ex + l2 * math.cos(a2), ey + l2 * math.sin(a2))
    return cubic((sx, sy), c1, c2, (ex, ey), 16)


def curve_rings(shape):
    """Cac vong kin (list diem mm) cua 1 hinh da la duong cong."""
    rings = []
    crv = shape.Curve
    for sp in _items(crv.SubPaths):
        if not bool(sp.Closed):
            continue
        pts = []
        for seg in _items(sp.Segments):
            pts += _seg_points(seg)
        if len(pts) >= 3:
            rings.append(pts)
    return rings


def collect_leaves(sr, out):
    for s in _items(sr):
        try:
            lname = s.Layer.Name
        except Exception:
            lname = ""
        if lname in (LAYER_LED, LAYER_WIRE, LAYER_HOLE) or s.Name == SAMPLE_NAME:
            continue
        t = int(s.Type)
        if t == T_GROUP:
            collect_leaves(s.Shapes.All(), out)
        elif t not in (0, 5, 8, 9):        # bo qua anh bitmap, vung chon, duong giong
            out.append(s)


class Session:
    """1 lan rai LED tren CorelDRAW: doc hinh, ve ket qua, 1 lenh Undo."""

    def __init__(self, app):
        self.app = app
        self.doc = app.ActiveDocument
        if self.doc is None:
            raise CorelError("Chưa mở file CorelDRAW nào.")
        self.page = self.doc.ActivePage
        self.old_unit = self.doc.Unit

    def __enter__(self):
        self.doc.Unit = CDR_MM
        self.doc.BeginCommandGroup("AutoLED Pro")
        try:
            self.app.Optimization = True
        except Exception:
            pass
        return self

    def __exit__(self, *exc):
        for f in (lambda: setattr(self.app, "Optimization", False),
                  lambda: self.doc.EndCommandGroup(),
                  lambda: setattr(self.doc, "Unit", self.old_unit),
                  lambda: self.app.ActiveWindow.Refresh(),
                  lambda: self.app.Refresh()):
            try:
                f()
            except Exception:
                pass
        return False

    # ------------------------------------------------------------ doc vung chon
    def selected_shapes(self):
        sr = self.app.ActiveSelectionRange
        if sr is None or int(sr.Count) == 0:
            raise CorelError("Hãy chọn chữ cần rải LED trong CorelDRAW trước.")
        leaves = []
        collect_leaves(sr, leaves)
        if not leaves:
            raise CorelError("Không tìm thấy chữ / đường cong kín trong vùng chọn.")
        return leaves

    def shape_rings(self, s):
        tmp = None
        try:
            if int(s.Type) != T_CURVE:
                tmp = s.Duplicate()
                tmp.ConvertToCurves()
                return curve_rings(tmp)
            return curve_rings(s)
        finally:
            if tmp is not None:
                try:
                    tmp.Delete()
                except Exception:
                    pass

    def sample(self):
        try:
            return self.page.FindShape(SAMPLE_NAME)
        except Exception:
            return None

    # ------------------------------------------------------------ layer
    def layer(self, name):
        for l in _items(self.page.Layers):
            if l.Name == name:
                l.Visible = True
                l.Editable = True
                return l
        return self.page.CreateLayer(name)

    def group(self, shapes, name):
        if not shapes:
            return None
        sr = self.app.CreateShapeRange()
        for s in shapes:
            sr.Add(s)
        if len(shapes) == 1:
            shapes[0].Name = name
            return shapes[0]
        g = sr.Group()
        g.Name = name
        return g

    # ------------------------------------------------------------ ve
    def draw_leds(self, lyr, leds, t, sample=None, sample_rot=0.0):
        out = []
        for cx, cy, ux, uy in leds:
            ang = math.degrees(math.atan2(uy, ux))
            while ang > 90:
                ang -= 180
            while ang <= -90:
                ang += 180
            if sample is not None:
                s = sample.Duplicate()
                s.MoveToLayer(lyr)
                s.CenterX = cx
                s.CenterY = cy
                if abs(ang + sample_rot) > 0.01:
                    s.Rotate(ang + sample_rot)
            elif t.kind == "dot":
                s = lyr.CreateEllipse2(cx, cy, t.L / 2)
                s.Fill.UniformColor.RGBAssign(230, 30, 30)
                s.Outline.SetNoOutline()
            else:
                s = lyr.CreateRectangle2(cx - t.L / 2, cy - t.W / 2, t.L, t.W)
                if abs(ang) > 0.01:
                    s.Rotate(ang)
                s.Fill.UniformColor.RGBAssign(60, 150, 240)
                s.Outline.SetProperties(0.15)
                s.Outline.Color.RGBAssign(0, 40, 110)
            s.Name = "LED"
            out.append(s)
        return self.group(out, f"LED x {len(out)}")

    def draw_holes(self, lyr, leds, d):
        out = []
        for cx, cy, ux, uy in leds:
            s = lyr.CreateEllipse2(cx, cy, d / 2)
            s.Fill.ApplyNoFill()
            s.Outline.SetProperties(0.1)
            s.Outline.Color.RGBAssign(0, 0, 0)
            s.Name = "LO"
            out.append(s)
        return self.group(out, f"LO CAT x {len(out)}")

    WIRE_COLORS = [(228, 26, 28), (255, 127, 0), (44, 160, 44), (148, 103, 189), (140, 86, 75), (227, 119, 194)]

    def draw_wires(self, lyr, paths, counts, feed, label_mm):
        out = []
        fx, fy = feed
        psu = lyr.CreateRectangle2(fx - 20, fy - 10, 40, 20)
        psu.Fill.UniformColor.RGBAssign(40, 40, 40)
        psu.Name = "NGUON"
        out.append(psu)
        for w, (pts, n) in enumerate(zip(paths, counts)):
            if not pts:
                continue
            r, g, b = self.WIRE_COLORS[w % len(self.WIRE_COLORS)]
            if len(pts) >= 2:
                crv = self.app.CreateCurve(self.doc)
                sp = crv.CreateSubPath(pts[0][0], pts[0][1])
                for x, y in pts[1:]:
                    sp.AppendLineSegment(x, y)
                s = lyr.CreateCurve(crv)
                s.Outline.SetProperties(0.5)
                s.Outline.Color.RGBAssign(r, g, b)
                s.Name = f"DAY {w + 1} ({n} LED)"
                out.append(s)
            s = lyr.CreateLineSegment(fx, fy + 10, pts[0][0], pts[0][1])
            s.Outline.SetProperties(0.25)
            s.Outline.Color.RGBAssign(r, g, b)
            out.append(s)
            try:
                tx = lyr.CreateArtisticText(pts[0][0] + 2, pts[0][1] + 2, f"IN{w + 1}")
                try:
                    tx.Text.Story.Size = max(6.0, label_mm * 2.835)
                except Exception:
                    pass
                tx.Fill.UniformColor.RGBAssign(r, g, b)
                out.append(tx)
            except Exception:
                pass
        return self.group(out, f"DAY x {len(paths)}")

    def clear(self):
        n = 0
        for name in (LAYER_LED, LAYER_WIRE, LAYER_HOLE):
            for l in _items(self.page.Layers):
                if l.Name == name:
                    n += int(l.Shapes.Count)
                    if int(l.Shapes.Count):
                        l.Shapes.All().Delete()
        return n

    def count_leds(self):
        def cnt(sr):
            k = 0
            for s in _items(sr):
                if int(s.Type) == T_GROUP:
                    k += cnt(s.Shapes.All())
                elif s.Name == "LED":
                    k += 1
            return k
        for l in _items(self.page.Layers):
            if l.Name == LAYER_LED:
                return cnt(l.Shapes.All())
        return 0
