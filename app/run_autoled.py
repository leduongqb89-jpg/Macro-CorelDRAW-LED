"""Diem vao AutoLED Pro. Tham so --selftest: tu kiem tra bo may (khong can CorelDRAW), ghi ket qua ra file."""
import sys, os


def selftest():
    from shapely.geometry import Polygon
    from autoled import library, core
    from autoled.geom import symmetry_axis
    from autoled.wiring import plan
    # chu A don gian (mm)
    A = Polygon([(0, 0), (230, 600), (400, 600), (630, 0), (500, 0), (450, 140), (180, 140), (130, 0)],
                [[(220, 250), (315, 520), (410, 250)]])
    lines, ok = [], True
    for spec in library.load()[:5]:
        leds, eng = core.layout_shape(A, spec, core.Options())
        wires, paths = plan(leds, spec, eng.pitch_u, 20, inside=eng.inside)
        lines.append(f"{spec.name}: {len(leds)} LED, {len(wires)} day, truc doi xung {symmetry_axis(A)}")
        ok &= len(leds) > 10
    out = os.path.join(os.environ.get("TEMP", "."), "autoled_selftest.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\nOK\n" if ok else "\nLOI\n"))
    try:
        print("\n".join(lines))
    except Exception:
        pass
    return 0 if ok else 1


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    from autoled.gui import main
    main()
