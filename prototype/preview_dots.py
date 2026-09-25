from led_layout import *
s = 600 / (775 - 266)
P = lambda pts: [((px - 93) * s, (775 - py) * s) for px, py in pts]
A = Polygon(P([(93, 775), (290, 266), (400, 266), (603, 775), (492, 775),
               (447, 658), (243, 658), (202, 775)]), [P([(344, 385), (275, 573), (414, 573)])])
c = Cfg(); c.L = c.W = 9.0; c.gap = 11.0; c.row_gap = 11.0; c.margin = 6.0
fig, axs = plt.subplots(1, 2, figsize=(13, 7))
lay = Layout(A, Cfg()); lay.run(); draw(axs[0], lay, "Module 65x15 - cach mep 10, khe ho 10")
lay = Layout(A, c); lay.run(); draw(axs[1], lay, "LED hat 9mm - buoc 20mm, cach mep 6")
fig.suptitle("AutoLED Pro - thuat toan moi (mo phong)", fontsize=13)
plt.tight_layout(); plt.savefig("preview_A.png", dpi=110)
