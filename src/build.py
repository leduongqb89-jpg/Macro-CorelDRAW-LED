"""Dong goi macro: ma hoa chu co dau -> \\uXXXX (chi trong U("...")), xuong dong CRLF, kiem tra ASCII."""
import re, sys, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
src = (root / "src" / "AutoLEDPro.src.bas").read_text(encoding="utf-8")
out_lines, errors = [], []
for no, line in enumerate(src.splitlines(), 1):
    if any(ord(c) > 126 for c in line):
        # chi cho phep ky tu co dau nam trong U("...")
        def enc(m):
            return 'U("' + "".join(c if ord(c) <= 126 else "\\u%04X" % ord(c) for c in m.group(1)) + '")'
        new = re.sub(r'U\("((?:[^"]|"")*)"\)', enc, line)
        if any(ord(c) > 126 for c in new):
            errors.append((no, line))
        line = new
    out_lines.append(line)
if errors:
    for no, l in errors:
        print(f"LOI dong {no}: ky tu co dau nam ngoai U(\"...\"): {l.strip()}")
    sys.exit(1)
text = "\r\n".join(out_lines) + "\r\n"
(root / "AutoLEDPro.bas").write_bytes(text.encode("ascii"))
print("OK ->", root / "AutoLEDPro.bas", len(out_lines), "dong")
