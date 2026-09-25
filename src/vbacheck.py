"""Soat loi VBA tho: can bang khoi lenh + bien chua khai bao (Option Explicit)."""
import re, sys
src = open(sys.argv[1], encoding="ascii", errors="replace").read().replace("\r\n", "\n")

def strip(line):
    out, q = "", False
    for i, c in enumerate(line):
        if c == '"':
            q = not q; out += '"'; continue
        if q:
            out += " "; continue
        if c == "'":
            break
        out += c
    return out

# noi dong tiep noi " _"
raw = src.split("\n")
lines, starts = [], []
buf, st = "", None
for no, l in enumerate(raw, 1):
    s = strip(l)
    if st is None: st = no
    if s.rstrip().endswith(" _"):
        buf += s.rstrip()[:-1] + " "; continue
    lines.append(buf + s); starts.append(st); buf, st = "", None

BUILTIN = set("""abs atn cos sin sqr int fix clng cint cdbl csng cstr cbool str val len mid mid$ left left$ right right$ replace split trim trim$ ltrim rtrim
format hex hex$ chrw chr asc ascw iif array ubound lbound environ environ$ dir mkdir freefile eof timer doevents msgbox getsetting savesetting err vba
vbcrlf vbinformation vbexclamation vbmodeless vbdirectory vbquestion vbyesno vbyes vbcritical true false nothing empty not and or mod is new me xor
double long boolean string integer single variant object shape shaperange layer curve subpath node cdrunit collection byte date
activedocument activeselectionrange activepage activewindow application optimization eventsenabled refresh createshaperange createcurve
open for input output as line print close each in to step then else elseif end if next do loop while until wend exit function sub select case
with dim redim preserve private public const type static byval byref optional call set let goto on error resume
option explicit attribute vb_name withevents rgbassign""".split())
CDR = re.compile(r"^cdr\w+$", re.I)

text = "\n".join(lines)
# ten o muc module
mod_names = set()
proc_re = re.compile(r"^\s*(?:Public |Private )?(?:Sub|Function)\s+(\w+)", re.I)
for l in lines:
    m = proc_re.match(l)
    if m: mod_names.add(m.group(1).lower())
    m = re.match(r"^\s*(?:Public|Private|Dim|Const|Public Const|Private Const)\s+(.*)$", l, re.I)
    if m and not proc_re.match(l) and not re.match(r"^\s*(Public|Private)\s+Type\b", l, re.I):
        for part in split_decl(m.group(1)) if False else []:
            pass
# gom khai bao module-level (ngoai thu tuc) va ten Type
in_proc, in_type = False, False
types = set()
fields = set()
def decl_names(s):
    s = re.sub(r"\([^)]*\)", "", s)
    names = []
    for part in s.split(","):
        part = part.strip()
        part = re.sub(r"^(Const|WithEvents|ByVal|ByRef|Optional|ParamArray)\s+", "", part, flags=re.I)
        part = re.sub(r"^(Const|WithEvents|ByVal|ByRef|Optional)\s+", "", part, flags=re.I)
        m = re.match(r"(\w+\$?)", part)
        if m: names.append(m.group(1).lower().rstrip("$"))
    return names
for l in lines:
    t = l.strip()
    if re.match(r"^(Public |Private )?Type\s+\w+", t, re.I):
        types.add(re.match(r"^(?:Public |Private )?Type\s+(\w+)", t, re.I).group(1).lower()); in_type = True; continue
    if in_type:
        if re.match(r"^End Type", t, re.I): in_type = False
        else:
            for sub in t.split(":"):
                n = decl_names(sub)
                fields.update(n)
        continue
    if proc_re.match(l): in_proc = True; continue
    if re.match(r"^\s*End (Sub|Function)", l, re.I): in_proc = False; continue
    if not in_proc:
        m = re.match(r"^\s*(?:Public|Private|Dim)\s+(?:Const\s+)?(.*)$", t, re.I)
        if m: mod_names.update(decl_names(m.group(1)))

# kiem tra tung thu tuc
errs = []
stack = []
cur_proc, local = None, set()
openers = [(r"^If\b.*\bThen\s*$", "if"), (r"^For\b", "for"), (r"^Do\b", "do"), (r"^With\b", "with"), (r"^Select Case\b", "select"),
           (r"^(Public |Private )?(Sub|Function)\b", "proc"), (r"^(Public |Private )?Type\b", "type")]
closers = [(r"^End If\b", "if"), (r"^Next\b", "for"), (r"^Loop\b", "do"), (r"^End With\b", "with"), (r"^End Select\b", "select"),
           (r"^End (Sub|Function)\b", "proc"), (r"^End Type\b", "type")]
for l, no in zip(lines, starts):
    for stmt in [x.strip() for x in l.split(":") if x.strip()] if not re.match(r"^\s*\w+:\s*$", l) else []:
        # dong 'If ... Then x' 1 dong: khong mo khoi
        for pat, k in openers:
            if re.match(pat, stmt, re.I):
                if k == "if" and not re.search(r"\bThen\s*$", stmt, re.I):
                    break
                stack.append((k, no)); break
        for pat, k in closers:
            if re.match(pat, stmt, re.I):
                if not stack or stack[-1][0] != k:
                    errs.append(f"dong {no}: dong khoi '{k}' khong khop (dang mo: {stack[-1] if stack else None})")
                else:
                    stack.pop()
                break
        # 'If ... Then' tren 1 dong co noi dung sau Then -> khong mo khoi
    m = proc_re.match(l)
    if m:
        cur_proc = m.group(1)
        local = set()
        pm = re.search(r"\((.*)\)", l)
        if pm: local.update(decl_names(pm.group(1)))
        continue
    if re.match(r"^\s*End (Sub|Function)", l, re.I):
        cur_proc = None; continue
    if cur_proc is None:
        continue
    for m in re.finditer(r"\b(?:Dim|Static|ReDim(?: Preserve)?)\s+([^:]*)", l, re.I):
        if re.match(r"^\s*ReDim", m.group(0), re.I): continue
        local.update(decl_names(m.group(1)))
    body = re.sub(r"\b(Dim|Static)\s+[^:]*", "", l, flags=re.I)
    body = re.sub(r'"[^"]*"', '""', body)
    for m in re.finditer(r"(?<![\.\w])([A-Za-z_]\w*)\$?", body):
        w = m.group(1).lower()
        after = body[m.end():m.end() + 1]
        if w in BUILTIN or CDR.match(w) or w in mod_names or w in local or w in types:
            continue
        if re.match(r"^\s*\w+:\s*$", l): continue            # nhan GoTo
        if re.search(r"\bGoTo\s+" + re.escape(m.group(1)) + r"\b", body, re.I): continue
        if w in ("u",): continue
        errs.append(f"dong {no} ({cur_proc}): '{m.group(1)}' chua khai bao?")
if stack:
    errs.append(f"khoi chua dong: {stack}")
seen = set()
for e in errs:
    if e not in seen:
        print(e); seen.add(e)
print("TONG:", len(seen), "canh bao")
