"""Cua so AutoLED Pro (Tkinter) - luon noi canh CorelDRAW."""
import os, sys, math, traceback, dataclasses
import tkinter as tk
from tkinter import ttk, messagebox
from . import __version__, library, core, corel

KINDS = [("dot", "LED tròn (hạt)"), ("module", "Module chữ nhật / vuông")]
STAGGER = ["Tự động", "Thẳng hàng", "So le"]
WIRE_COLORS = ["#e41a1c", "#ff7f00", "#2ca02c", "#9467bd", "#8c564b", "#e377c2"]


def resource(name):
    base = getattr(sys, "_MEIPASS", os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    return os.path.join(base, "assets", name)


def log_error(e):
    try:
        with open(os.path.join(library.data_dir(), "loi.txt"), "a", encoding="utf-8") as f:
            f.write(traceback.format_exc() + "\n")
    except Exception:
        pass


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"AutoLED Pro {__version__} – Rải LED tự động cho CorelDRAW")
        try:
            self.iconbitmap(resource("autoled.ico"))
        except Exception:
            pass
        self.lib = library.load()
        self.st = library.load_settings()
        self.corel_app = None
        self.attributes("-topmost", bool(self.st.get("topmost", True)))
        self.resizable(True, True)
        self.minsize(900, 560)
        style = ttk.Style(self)
        try:
            style.theme_use("vista")
        except Exception:
            pass
        style.configure("Big.TButton", font=("Segoe UI", 12, "bold"), padding=8)
        style.configure("H.TLabel", font=("Segoe UI", 10, "bold"))
        self.vars = {}
        self.build()
        self.load_led(int(self.st.get("led", 2)) % len(self.lib))
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------------------------------------------------ giao dien
    def var(self, key, val, kind=tk.StringVar):
        v = kind(value=val)
        self.vars[key] = v
        return v

    def row(self, parent, r, text, key, val, width=9):
        ttk.Label(parent, text=text).grid(row=r, column=0, sticky="w", padx=6, pady=2)
        e = ttk.Entry(parent, textvariable=self.var(key, val), width=width)
        e.grid(row=r, column=1, sticky="we", padx=6, pady=2)
        return e

    def build(self):
        left = ttk.Frame(self, padding=8)
        left.grid(row=0, column=0, sticky="nsw")
        right = ttk.Frame(self, padding=8)
        right.grid(row=0, column=1, sticky="nsew")
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        f1 = ttk.LabelFrame(left, text=" 1. Chọn loại LED ", padding=6)
        f1.grid(row=0, column=0, sticky="we")
        self.cbo = ttk.Combobox(f1, state="readonly", width=34, values=[t.name for t in self.lib])
        self.cbo.grid(row=0, column=0, columnspan=2, sticky="we", padx=6, pady=4)
        self.cbo.bind("<<ComboboxSelected>>", lambda e: self.load_led(self.cbo.current()))
        self.row(f1, 1, "Tên LED", "name", "", 22)
        ttk.Label(f1, text="Kiểu").grid(row=2, column=0, sticky="w", padx=6)
        self.kind = ttk.Combobox(f1, state="readonly", values=[k[1] for k in KINDS], width=22)
        self.kind.grid(row=2, column=1, sticky="we", padx=6, pady=2)
        self.row(f1, 3, "Dài (mm)", "L", "")
        self.row(f1, 4, "Rộng (mm)", "W", "")
        self.row(f1, 5, "Số bóng theo chiều dài", "cn", "")
        self.row(f1, 6, "Số bóng theo chiều rộng", "rn", "")
        self.row(f1, 7, "Công suất 1 LED (W)", "watt", "")
        self.row(f1, 8, "Đơn giá 1 LED", "price", "")
        bf = ttk.Frame(f1)
        bf.grid(row=9, column=0, columnspan=2, pady=4)
        ttk.Button(bf, text="Thêm mới", command=self.lib_new).pack(side="left", padx=2)
        ttk.Button(bf, text="Lưu LED", command=self.lib_save).pack(side="left", padx=2)
        ttk.Button(bf, text="Xóa LED", command=self.lib_del).pack(side="left", padx=2)

        f2 = ttk.LabelFrame(left, text=" 2. Thông số xếp ", padding=6)
        f2.grid(row=1, column=0, sticky="we", pady=6)
        self.row(f2, 0, "Khoảng cách tâm bóng (mm)", "P", "")
        self.row(f2, 1, "Cách mép chữ (mm)", "margin", "")
        self.row(f2, 2, "Khe tối thiểu giữa 2 LED (mm)", "gap", "")
        ttk.Label(f2, text="Xếp module").grid(row=3, column=0, sticky="w", padx=6)
        self.stg = ttk.Combobox(f2, state="readonly", values=STAGGER, width=12)
        self.stg.current(int(self.st.get("stagger", 0)))
        self.stg.grid(row=3, column=1, sticky="we", padx=6, pady=2)
        ttk.Checkbutton(f2, text="Tự nhận chữ đối xứng (lật gương)",
                        variable=self.var("sym", self.st.get("sym", True), tk.BooleanVar)).grid(row=4, column=0, columnspan=2, sticky="w", padx=6)
        ttk.Checkbutton(f2, text="Lấp chỗ tối (LED tròn)",
                        variable=self.var("fill", self.st.get("fill", True), tk.BooleanVar)).grid(row=5, column=0, columnspan=2, sticky="w", padx=6)

        f3 = ttk.LabelFrame(left, text=" 3. Đi dây & đục lỗ ", padding=6)
        f3.grid(row=2, column=0, sticky="we")
        ttk.Checkbutton(f3, text="Vẽ đường đi dây (layer DAY)",
                        variable=self.var("wires", self.st.get("wires", True), tk.BooleanVar)).grid(row=0, column=0, columnspan=2, sticky="w", padx=6)
        self.row(f3, 1, "Tối đa LED trên 1 dây", "maxw", str(self.st.get("maxw", 20)))
        self.row(f3, 2, "Điện áp nguồn (V)", "volt", str(self.st.get("volt", 12)))
        ttk.Checkbutton(f3, text="Tạo lỗ cắt (LED tròn), đường kính (mm):",
                        variable=self.var("holes", self.st.get("holes", False), tk.BooleanVar)).grid(row=3, column=0, sticky="w", padx=6)
        ttk.Entry(f3, textvariable=self.var("hole_d", str(self.st.get("hole_d", 9))), width=9).grid(row=3, column=1, padx=6)

        # ---- ben phai: nut + xem truoc + trang thai
        bar = ttk.Frame(right)
        bar.pack(fill="x")
        ttk.Button(bar, text="RẢI LED", style="Big.TButton", command=self.do_run).pack(side="left", padx=(0, 6))
        ttk.Button(bar, text="Đếm / Báo giá", command=self.do_count).pack(side="left", padx=3)
        ttk.Button(bar, text="Xóa LED + dây", command=self.do_clear).pack(side="left", padx=3)
        ttk.Button(bar, text="Dùng hình đang chọn làm LED", command=self.do_sample).pack(side="left", padx=3)
        self.top = self.var("top", bool(self.st.get("topmost", True)), tk.BooleanVar)
        ttk.Checkbutton(bar, text="Luôn nổi trên cùng", variable=self.top,
                        command=lambda: self.attributes("-topmost", self.top.get())).pack(side="right")
        self.canvas = tk.Canvas(right, bg="white", highlightthickness=1, highlightbackground="#bbb")
        self.canvas.pack(fill="both", expand=True, pady=6)
        self.canvas.create_text(20, 20, anchor="nw", fill="#666", font=("Segoe UI", 11),
                                text="Chọn chữ trong CorelDRAW rồi bấm RẢI LED.\nKết quả xem trước sẽ hiện ở đây.\n"
                                     "Bấm Ctrl+Z trong CorelDRAW một lần để hủy cả lần rải.")
        self.status = tk.Text(right, height=6, font=("Segoe UI", 10), wrap="word", bg="#f7f7f7", relief="flat")
        self.status.pack(fill="x")

    # ------------------------------------------------------------ thu vien
    def load_led(self, i):
        if not (0 <= i < len(self.lib)):
            return
        t = self.lib[i]
        self.cbo.current(i)
        v = self.vars
        v["name"].set(t.name)
        self.kind.current(0 if t.kind == "dot" else 1)
        for k, val in (("L", t.L), ("W", t.W), ("cn", t.cn), ("rn", t.rn), ("watt", t.watt), ("price", t.price),
                       ("P", t.P), ("margin", t.margin), ("gap", t.min_gap)):
            v[k].set(f"{val:g}")

    def num(self, key, default=0.0):
        try:
            return float(str(self.vars[key].get()).replace(",", "."))
        except Exception:
            return default

    def read_spec(self):
        kind = KINDS[max(0, self.kind.current())][0]
        return library.make(self.vars["name"].get().strip() or "LED", kind, self.num("L", 9), self.num("W", 9),
                            int(self.num("cn", 1)), int(self.num("rn", 1)), self.num("P", 25) or 25,
                            self.num("margin", 6), self.num("gap", 5) or 5, self.num("watt"), self.num("price"))

    def read_opts(self):
        o = core.Options(stagger=max(0, self.stg.current()), auto_sym=self.vars["sym"].get(),
                         fill_dark=self.vars["fill"].get(), wires=self.vars["wires"].get(),
                         max_per_wire=int(self.num("maxw", 20)) or 20, volt=self.num("volt", 12) or 12,
                         holes=self.vars["holes"].get(), hole_d=self.num("hole_d", 9))
        self.st.update(led=self.cbo.current(), stagger=o.stagger, sym=o.auto_sym, fill=o.fill_dark, wires=o.wires,
                       maxw=o.max_per_wire, volt=o.volt, holes=o.holes, hole_d=o.hole_d, topmost=self.top.get())
        library.save_settings(self.st)
        return o

    def lib_new(self):
        t = self.read_spec()
        self.lib.append(t)
        library.save(self.lib)
        self.cbo["values"] = [x.name for x in self.lib]
        self.load_led(len(self.lib) - 1)
        self.say(f"Đã thêm LED “{t.name}” vào thư viện.")

    def lib_save(self):
        i = self.cbo.current()
        if i < 0:
            return self.lib_new()
        self.lib[i] = self.read_spec()
        library.save(self.lib)
        self.cbo["values"] = [x.name for x in self.lib]
        self.cbo.current(i)
        self.say("Đã lưu thư viện LED.")

    def lib_del(self):
        i = self.cbo.current()
        if i < 0 or len(self.lib) <= 1:
            return
        if messagebox.askyesno("AutoLED Pro", f"Xóa “{self.lib[i].name}” khỏi thư viện?"):
            del self.lib[i]
            library.save(self.lib)
            self.cbo["values"] = [x.name for x in self.lib]
            self.load_led(0)

    # ------------------------------------------------------------ CorelDRAW
    def say(self, msg):
        self.status.delete("1.0", "end")
        self.status.insert("end", msg)
        self.update()

    def app_corel(self):
        if self.corel_app is not None:
            try:
                _ = self.corel_app.ActiveDocument
                return self.corel_app
            except Exception:
                self.corel_app = None
        self.corel_app = corel.connect()
        return self.corel_app

    def guarded(self, fn):
        try:
            fn()
        except corel.CorelError as e:
            self.say(str(e))
        except Exception as e:
            log_error(e)
            self.say(f"Lỗi: {e}\n(Chi tiết đã ghi vào {os.path.join(library.data_dir(), 'loi.txt')} – gửi file này để được hỗ trợ.)")

    def do_run(self):
        def job():
            spec, opts = self.read_spec(), self.read_opts()
            self.say("Đang kết nối CorelDRAW…")
            app = self.app_corel()
            n, w, rep, results, used = core.run(app, spec, opts, progress=self.say)
            self.say(rep)
            self.preview(results, used)
        self.guarded(job)

    def do_count(self):
        def job():
            spec, opts = self.read_spec(), self.read_opts()
            n = corel.Session(self.app_corel()).count_leds()
            self.say(core.report(n, spec, opts))
        self.guarded(job)

    def do_clear(self):
        def job():
            app = self.app_corel()
            with corel.Session(app) as ss:
                n = ss.clear()
            self.say(f"Đã xóa {n} đối tượng trên các layer LED / DAY / LO_CAT.")
        self.guarded(job)

    def do_sample(self):
        def job():
            app = self.app_corel()
            sr = app.ActiveSelectionRange
            if sr is None or int(sr.Count) != 1:
                return self.say("Hãy chọn đúng 1 hình (có thể là nhóm) trong CorelDRAW rồi bấm lại.")
            sr.Item(1).Name = corel.SAMPLE_NAME
            self.say("Đã lưu hình tùy chỉnh (tên LED_MAU). Khi rải, hình này sẽ được nhân bản làm LED.\n"
                     "Muốn bỏ: xóa hoặc đổi tên hình LED_MAU.")
        self.guarded(job)

    # ------------------------------------------------------------ xem truoc
    def preview(self, results, spec):
        c = self.canvas
        c.delete("all")
        if not results:
            return
        from shapely.ops import unary_union
        allb = unary_union([r[0] for r in results]).bounds
        x0, y0, x1, y1 = allb
        y0 -= 50
        W, H = max(50, c.winfo_width()), max(50, c.winfo_height())
        k = min((W - 20) / (x1 - x0), (H - 20) / (y1 - y0))
        tf = lambda x, y: (10 + (x - x0) * k, H - 10 - (y - y0) * k)
        for shape, leds, paths in results:
            for poly in getattr(shape, "geoms", [shape]):
                c.create_polygon([v for p in poly.exterior.coords for v in tf(*p)], fill="#f0f0f0", outline="#333")
                for h in poly.interiors:
                    c.create_polygon([v for p in h.coords for v in tf(*p)], fill="white", outline="#333")
            for cx, cy, ux, uy in leds:
                if spec.kind == "dot":
                    r = max(1.5, spec.L / 2 * k)
                    X, Y = tf(cx, cy)
                    c.create_oval(X - r, Y - r, X + r, Y + r, fill="#e6261f", outline="")
                else:
                    vx, vy = -uy, ux
                    hl, hw = spec.L / 2, spec.W / 2
                    pts = [tf(cx + sx * hl * ux + sy * hw * vx, cy + sx * hl * uy + sy * hw * vy)
                           for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
                    c.create_polygon([v for p in pts for v in p], fill="#3c96f0", outline="#00286e")
            for i, p in enumerate(paths):
                if len(p) >= 2:
                    c.create_line([v for q in p for v in tf(*q)], fill=WIRE_COLORS[i % len(WIRE_COLORS)], width=1.5)

    def on_close(self):
        try:
            self.read_opts()
        except Exception:
            pass
        self.destroy()


def main():
    App().mainloop()
