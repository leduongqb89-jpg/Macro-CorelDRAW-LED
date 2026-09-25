"""Quy trinh rai LED: doc chu tu CorelDRAW -> bo may xep -> ve LED, day, lo cat -> bao cao."""
import time, dataclasses
from dataclasses import dataclass
from .engine import Engine
from .geom import rings_to_shape, symmetry_axis
from .wiring import plan
from . import corel


@dataclass
class Options:
    stagger: int = 0          # 0 tu dong, 1 thang hang, 2 so le
    auto_sym: bool = True
    fill_dark: bool = True
    wires: bool = True
    max_per_wire: int = 20
    volt: float = 12.0
    holes: bool = False
    hole_d: float = 9.0


def layout_shape(shape, spec, opts):
    """Chay bo may xep cho 1 hinh shapely -> (leds, engine)."""
    axis = symmetry_axis(shape) if opts.auto_sym else None
    stg = {0: "auto", 1: False, 2: True}.get(opts.stagger, "auto")
    eng = Engine(shape, spec, stagger=stg, fill_dark=opts.fill_dark, sym_axis=axis)
    return eng.run(), eng


def report(n, spec, opts, wires=0, seconds=None):
    w = n * spec.watt
    v = opts.volt if opts.volt > 0 else 12.0
    lines = [f"Số LED: {n}  ({spec.name})",
             f"Công suất: {w:.1f} W  –  Nguồn đề xuất (dư 20%): {w * 1.2:.0f} W (~{w * 1.2 / v:.1f} A @ {v:g} V)",
             f"Thành tiền LED: {n * spec.price:,.0f}".replace(",", ".")]
    if wires:
        lines.append(f"Số dây nối: {wires}")
    if seconds is not None:
        lines.append(f"Thời gian: {seconds:.1f} giây")
    return "\n".join(lines)


def run(app, spec, opts, progress=lambda msg: None):
    t0 = time.time()
    total, nwires = 0, 0
    results = []                              # de ve xem truoc: (shape, leds, paths)
    with corel.Session(app) as ss:
        leaves = ss.selected_shapes()
        smp = ss.sample()
        rot = 0.0
        if smp is not None:
            sw, sh = float(smp.SizeWidth), float(smp.SizeHeight)
            spec = dataclasses.replace(spec, L=max(sw, sh), W=min(sw, sh) if spec.kind != "dot" else max(sw, sh))
            from .library import make
            spec = make(spec.name, spec.kind, spec.L, spec.W, spec.cn, spec.rn, spec.P, spec.margin,
                        spec.min_gap, spec.watt, spec.price)
            rot = -90.0 if sh > sw else 0.0
        lyr_led = ss.layer(corel.LAYER_LED)
        lyr_wire = ss.layer(corel.LAYER_WIRE) if opts.wires else None
        lyr_hole = ss.layer(corel.LAYER_HOLE) if (opts.holes and spec.kind == "dot") else None
        for k, s in enumerate(leaves, 1):
            progress(f"Đang xếp chữ {k}/{len(leaves)}…")
            shape = rings_to_shape(ss.shape_rings(s))
            if shape is None or shape.is_empty:
                continue
            leds, eng = layout_shape(shape, spec, opts)
            if not leds:
                continue
            progress(f"Đang vẽ {len(leds)} LED (chữ {k}/{len(leaves)})…")
            ss.draw_leds(lyr_led, leds, spec, smp, rot)
            total += len(leds)
            if lyr_hole is not None:
                ss.draw_holes(lyr_hole, leds, opts.hole_d if opts.hole_d > 0 else spec.L)
            paths = []
            if lyr_wire is not None:
                wires, paths = plan(leds, spec, eng.pitch_u, max_per=max(1, opts.max_per_wire), inside=eng.inside)
                x0, y0, x1, y1 = shape.bounds
                ss.draw_wires(lyr_wire, paths, [len(w) for w in wires], ((x0 + x1) / 2, y0 - 40), 0.35 * eng.pitch_u)
                nwires += len(wires)
            results.append((shape, leds, paths))
    return total, nwires, report(total, spec, opts, nwires, time.time() - t0), results, spec
