"""Mo cua so that tren man hinh ao, chay rai LED voi CorelDRAW gia lap, chup anh."""
import sys, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..")); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "..", "lab"))
from glyphs import glyph
from mock_corel import App as MockApp, shape_from_polygon
from autoled import gui, corel

mock = MockApp()
mock.ActiveSelectionRange.items = [shape_from_polygon(mock, glyph("A", 600))]
corel.connect = lambda: mock
w = gui.App()
w.geometry("1150x700+0+0")
w.update()
w.load_led(2)
w.after(500, w.do_run)
def shot():
    from PIL import ImageGrab
    ImageGrab.grab(xdisplay=os.environ.get("DISPLAY")).save(os.path.join(HERE, "..", "assets", "gui_screenshot.png"))
    w.destroy()
w.after(6000, shot)
w.mainloop()
