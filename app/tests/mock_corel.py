"""CorelDRAW gia lap (chi cac doi tuong / lenh ma autoled.corel dung) de thu tren Linux."""
import math


class Coll:
    def __init__(self, items=None):
        self.items = list(items or [])

    @property
    def Count(self):
        return len(self.items)

    def Item(self, i):
        return self.items[i - 1]

    def All(self):
        return ShapeRange(self.items)


class Color:
    def RGBAssign(self, r, g, b):
        self.rgb = (r, g, b)


class Fill:
    def __init__(self):
        self.UniformColor = Color()

    def ApplyNoFill(self):
        self.none = True


class Outline:
    def __init__(self):
        self.Color = Color()

    def SetProperties(self, w):
        self.w = w

    def SetNoOutline(self):
        self.w = 0


class Node:
    def __init__(self, x, y):
        self.PositionX, self.PositionY = x, y


class Segment:
    def __init__(self, a, b, c1=None, c2=None):
        self.StartNode, self.EndNode = Node(*a), Node(*b)
        self.Type = 1 if c1 else 0
        if c1:
            self.StartingControlPointX, self.StartingControlPointY = c1
            self.EndingControlPointX, self.EndingControlPointY = c2


class SubPath:
    def __init__(self, segs=None, x=None, y=None):
        self.Segments = Coll(segs or [])
        self.Closed = True
        self.pts = [(x, y)] if x is not None else []

    def AppendLineSegment(self, x, y):
        self.pts.append((x, y))


class Curve:
    def __init__(self, subpaths=None):
        self.SubPaths = Coll(subpaths or [])

    def CreateSubPath(self, x, y):
        sp = SubPath(x=x, y=y)
        self.SubPaths.items.append(sp)
        return sp


class Shape:
    def __init__(self, typ, layer=None, curve=None, name=""):
        self.Type, self.Layer, self.Curve, self.Name = typ, layer, curve, name
        self.Fill, self.Outline = Fill(), Outline()
        self.CenterX = self.CenterY = 0.0
        self.SizeWidth = self.SizeHeight = 10.0
        self.angle = 0.0
        self.Shapes = Coll()
        self.deleted = False

    def Duplicate(self):
        d = Shape(self.Type, self.Layer, self.Curve, self.Name)
        return d

    def ConvertToCurves(self):
        self.Type = 3

    def Delete(self):
        self.deleted = True
        if self.Layer is not None and self in self.Layer.Shapes.items:
            self.Layer.Shapes.items.remove(self)

    def Rotate(self, a):
        self.angle += a

    def MoveToLayer(self, l):
        self.Layer = l
        l.Shapes.items.append(self)


class ShapeRange(Coll):
    def Add(self, s):
        self.items.append(s)

    def Group(self):
        g = Shape(7, self.items[0].Layer if self.items else None)
        g.Shapes = Coll(self.items)
        lyr = g.Layer
        if lyr is not None:
            for s in self.items:
                if s in lyr.Shapes.items:
                    lyr.Shapes.items.remove(s)
            lyr.Shapes.items.append(g)
        return g

    def Delete(self):
        for s in list(self.items):
            s.Delete()


class Layer:
    def __init__(self, name):
        self.Name, self.Visible, self.Editable = name, True, True
        self.Shapes = ShapeRange()

    def _add(self, s):
        s.Layer = self
        self.Shapes.items.append(s)
        return s

    def CreateEllipse2(self, cx, cy, r):
        s = Shape(2); s.CenterX, s.CenterY = cx, cy; s.r = r
        return self._add(s)

    def CreateRectangle2(self, x, y, w, h):
        s = Shape(1); s.CenterX, s.CenterY = x + w / 2, y + h / 2; s.w, s.h = w, h
        return self._add(s)

    def CreateCurve(self, crv):
        return self._add(Shape(3, curve=crv))

    def CreateLineSegment(self, x1, y1, x2, y2):
        return self._add(Shape(3))

    def CreateArtisticText(self, x, y, text):
        s = Shape(6); s.text = text
        class St: pass
        s.Text = St(); s.Text.Story = St()
        return self._add(s)


class Page:
    def __init__(self):
        self.Layers = Coll([Layer("Layer 1")])

    def CreateLayer(self, name):
        l = Layer(name)
        self.Layers.items.append(l)
        return l

    def FindShape(self, name):
        for l in self.Layers.items:
            for s in l.Shapes.items:
                if s.Name == name:
                    return s
        return None


class Document:
    def __init__(self):
        self.Unit = 1
        self.ActivePage = Page()
        self.groups = 0

    def BeginCommandGroup(self, n):
        self.groups += 1

    def EndCommandGroup(self):
        self.groups -= 1


class App:
    def __init__(self):
        self.ActiveDocument = Document()
        self.ActiveSelectionRange = ShapeRange()
        self.Optimization = False
        class W:
            def Refresh(self): pass
        self.ActiveWindow = W()

    def CreateShapeRange(self):
        return ShapeRange()

    def CreateCurve(self, doc):
        return Curve()

    def Refresh(self):
        pass


def shape_from_polygon(app, poly, as_bezier_circle=False):
    """Tao 1 duong cong Corel gia lap tu shapely polygon (doan thang) + 1 vong bezier tuy chon."""
    lyr = app.ActiveDocument.ActivePage.Layers.Item(1)
    sps = []
    for ring in [poly.exterior, *poly.interiors]:
        c = list(ring.coords)[:-1]
        segs = [Segment(c[i], c[(i + 1) % len(c)]) for i in range(len(c))]
        sps.append(SubPath(segs))
    if as_bezier_circle:
        pass
    s = Shape(3, lyr, Curve(sps), "chu")
    lyr.Shapes.items.append(s)
    return s


def bezier_circle(app, cx, cy, r):
    k = 0.5523 * r
    P = [(cx + r, cy), (cx, cy + r), (cx - r, cy), (cx, cy - r)]
    C = [((cx + r, cy + k), (cx + k, cy + r)), ((cx - k, cy + r), (cx - r, cy + k)),
         ((cx - r, cy - k), (cx - k, cy - r)), ((cx + k, cy - r), (cx + r, cy - k))]
    segs = [Segment(P[i], P[(i + 1) % 4], *C[i]) for i in range(4)]
    lyr = app.ActiveDocument.ActivePage.Layers.Item(1)
    s = Shape(3, lyr, Curve([SubPath(segs)]), "tron")
    lyr.Shapes.items.append(s)
    return s
