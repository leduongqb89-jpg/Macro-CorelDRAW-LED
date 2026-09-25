import json
from bench import sheet
from ledtypes import F9, M65, M35
GROUPS = [("net_thang", "ILTHEF"), ("net_xien", "AVNKMZ"), ("net_cong", "OCSGUJ"), ("thang_cong", "BRDP"), ("co_dau", "ĐƠƯ")]
res = {}
for t, tag in [(F9, "F9"), (M65, "M65"), (M35, "M35")]:
    for gname, chars in GROUPS:
        r = sheet(chars, 600, t, f"../ket_qua/{tag}_{gname}_600mm.png")
        res[f"{tag}/{gname}/600"] = {ch: v["score"] for ch, v in r.items()}
        print(tag, gname, round(sum(v["score"] for v in r.values()) / len(r), 2), flush=True)
for size in (1000, 300):
    for gname, chars in GROUPS[:3]:
        r = sheet(chars, size, F9, f"../ket_qua/F9_{gname}_{size}mm.png")
        res[f"F9/{gname}/{size}"] = {ch: v["score"] for ch, v in r.items()}
        print("F9", gname, size, round(sum(v["score"] for v in r.values()) / len(r), 2), flush=True)
json.dump(res, open("../ket_qua/diem.json", "w"), ensure_ascii=False, indent=1)
