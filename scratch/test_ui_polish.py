import sys, os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QColor, QPainter, QImage
from PyQt6.QtCore import QRect, QPoint

app = QApplication.instance()
if not app:
    app = QApplication(sys.argv)

from ui.overlay.canvas_widget import ScreenOverlayCanvas
from ui.overlay.rendering_helper import draw_dimension_badge, draw_magnifier_loupe

# Create a sample pixmap
pm = QPixmap(800, 600)
pm.fill(QColor(100, 150, 200))

# Test ScreenOverlayCanvas initialization
cw = ScreenOverlayCanvas(pm, QRect(0, 0, 800, 600))
cw.resize(800, 600)

# Set selection
cw.selection_rect = QRect(50, 50, 400, 300)
cw.update_toolbar_positions()

# Verify toolbars have graphics effect (shadow)
assert cw.v_toolbar.graphicsEffect() is not None, "v_toolbar should have graphics effect"
assert cw.h_toolbar.graphicsEffect() is not None, "h_toolbar should have graphics effect"
assert cw.sub_toolbar.graphicsEffect() is not None, "sub_toolbar should have graphics effect"
print("[OK] All toolbars have drop shadow effect attached")

# Test show_toast
cw.show_toast("Đã sao chép mã màu #2563EB")
assert cw.toast_message == "Đã sao chép mã màu #2563EB"
print("[OK] Toast message set properly")

# Test draw_magnifier_loupe directly
target_img = QImage(800, 600, QImage.Format.Format_ARGB32_Premultiplied)
target_img.fill(0)
img = pm.toImage()
p = QPainter(target_img)
draw_magnifier_loupe(p, QPoint(100, 100), pm, img, 800, 600, "HEX")
draw_magnifier_loupe(p, QPoint(100, 100), pm, img, 800, 600, "RGB")
draw_dimension_badge(p, QRect(50, 50, 400, 300), 800, 600)
cw.draw_selection_handles(p, QRect(50, 50, 400, 300))
cw._draw_toast(p, 800, 600)
p.end()
print("[OK] Magnifier loupe, dimension badge, handles, and toast rendered successfully in offscreen painter")

print("\n>>> ALL UI MICRO-POLISH CHECKS PASSED PERFECTLY! <<<")
