"""Thu vien LED: luu JSON trong %APPDATA%/AutoLEDPro/thu_vien_led.json."""
import json, os
from dataclasses import dataclass, asdict, field


@dataclass
class LedType:
    name: str
    kind: str              # "dot" (LED tron) | "module"
    L: float               # chieu dai (mm)
    W: float               # chieu rong (mm)
    bulbs: list            # [(a, b)] vi tri bong so voi tam LED
    P: float               # khoang cach tam bong muc tieu (mm)
    margin: float          # cach mep chu (mm)
    min_gap: float = 5.0   # khe toi thieu giua 2 LED (mm)
    watt: float = 0.0
    price: float = 0.0
    cn: int = 1
    rn: int = 1

    @property
    def cell(self):
        xs = sorted({a for a, b in self.bulbs})
        return (xs[1] - xs[0]) if len(xs) > 1 else 0.0

    @property
    def end_off(self):
        return self.L / 2 - max(abs(a) for a, b in self.bulbs)


def make(name, kind, L, W, cn, rn, P, margin, min_gap=5.0, watt=0.0, price=0.0):
    if kind == "dot":
        W, cn, rn = L, 1, 1
    cn, rn = max(1, int(cn)), max(1, int(rn))
    bulbs = [(-L / 2 + (i + 0.5) * L / cn, -W / 2 + (j + 0.5) * W / rn) for i in range(cn) for j in range(rn)]
    return LedType(name, kind, float(L), float(W), bulbs, float(P), float(margin), float(min_gap),
                   float(watt), float(price), cn, rn)


DEFAULTS = [
    ("LED tròn F9", "dot", 9, 9, 1, 1, 25, 6, 5, 0.2, 500),
    ("LED tròn F12", "dot", 12, 12, 1, 1, 30, 8, 5, 0.3, 800),
    ("Module 15x65 (3 bóng)", "module", 65, 15, 3, 1, 35, 10, 5, 0.72, 3000),
    ("Module 12x45 (2 bóng)", "module", 45, 12, 2, 1, 30, 8, 5, 0.48, 2000),
    ("Module vuông 35x35 (4 bóng)", "module", 35, 35, 2, 2, 35, 8, 5, 1.0, 5000),
]


def data_dir():
    d = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "AutoLEDPro")
    os.makedirs(d, exist_ok=True)
    return d


def lib_path():
    return os.path.join(data_dir(), "thu_vien_led.json")


def load():
    try:
        with open(lib_path(), encoding="utf-8") as f:
            rows = json.load(f)
        out = [make(r["name"], r["kind"], r["L"], r["W"], r.get("cn", 1), r.get("rn", 1), r["P"], r["margin"],
                    r.get("min_gap", 5), r.get("watt", 0), r.get("price", 0)) for r in rows]
        if out:
            return out
    except Exception:
        pass
    out = [make(*d) for d in DEFAULTS]
    save(out)
    return out


def save(items):
    rows = [{k: v for k, v in asdict(t).items() if k != "bulbs"} for t in items]
    with open(lib_path(), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)


def load_settings():
    try:
        with open(os.path.join(data_dir(), "cai_dat.json"), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(d):
    with open(os.path.join(data_dir(), "cai_dat.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
