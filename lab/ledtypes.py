"""Thu vien LED dung de thu. Toa do bong LED tinh theo tam LED (truc u = chieu dai)."""
from dataclasses import dataclass, field


@dataclass
class LedType:
    name: str
    kind: str            # "dot" (hat tron) | "module"
    L: float             # chieu dai (mm)
    W: float             # chieu rong (mm)
    bulbs: list          # [(a, b)] vi tri bong theo (doc, ngang) so voi tam
    P: float             # khoang cach tam bong muc tieu (mm)
    margin: float        # cach mep chu (mm)
    min_gap: float = 5.0 # khe toi thieu giua 2 LED (mm)

    @property
    def cell(self):      # buoc bong trong module theo chieu dai
        xs = sorted({a for a, b in self.bulbs})
        return (xs[1] - xs[0]) if len(xs) > 1 else 0.0

    @property
    def end_off(self):   # khoang cach tu bong ngoai cung toi dau module
        return self.L / 2 - max(abs(a) for a, b in self.bulbs)


def module(name, L, W, cn, rn, P, margin):
    bulbs = [(-L / 2 + (i + 0.5) * L / cn, -W / 2 + (j + 0.5) * W / rn) for i in range(cn) for j in range(rn)]
    return LedType(name, "module", L, W, bulbs, P, margin)


F9 = LedType("LED tròn F9", "dot", 9, 9, [(0, 0)], 25.0, 6.0)
M65 = module("Module 15×65 (3 bóng)", 65, 15, 3, 1, 35.0, 10.0)
M35 = module("Module vuông 35×35 (4 bóng)", 35, 35, 2, 2, 35.0, 8.0)
TYPES = [F9, M65, M35]
