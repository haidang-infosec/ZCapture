from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPixmap, QIcon, QPainterPath, QFontMetrics
)
from PyQt6.QtWidgets import (
    QWidget, QMenu, QHBoxLayout, QPushButton, QComboBox, QSpinBox, QColorDialog,
    QToolButton, QLabel, QWidgetAction, QFrame, QSlider, QGridLayout, QVBoxLayout
)

from models.annotations import TextItem, TimestampItem, WatermarkItem


def make_divider() -> QFrame:
    d = QFrame()
    d.setFrameShape(QFrame.Shape.VLine)
    d.setFixedSize(1, 24)
    d.setStyleSheet("background: rgba(0,0,0,0.08); border: none;")
    return d


def make_checkerboard_icon(size=16) -> QIcon:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    half = size // 2
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor("#D4D4D8")))
    p.drawRect(0, 0, half, half)
    p.drawRect(half, half, half, half)
    p.setBrush(QBrush(QColor("#FFFFFF")))
    p.drawRect(half, 0, half, half)
    p.drawRect(0, half, half, half)
    p.setPen(QPen(QColor("#A1A1AA"), 1))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRect(0, 0, size - 1, size - 1)
    p.end()
    return QIcon(pm)


def make_simple_icon(draw_func, size=16) -> QIcon:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    draw_func(p, size)
    p.end()
    return QIcon(pm)


def draw_sun(p, s):
    cx, cy, r = s // 2, s // 2, s // 2 - 2
    p.setPen(QPen(QColor("#52525B"), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QPointF(cx, cy), r * 0.45, r * 0.45)
    import math as _m
    for i in range(8):
        a = _m.radians(i * 45)
        x1, y1 = cx + _m.cos(a) * r * 0.65, cy + _m.sin(a) * r * 0.65
        x2, y2 = cx + _m.cos(a) * r, cy + _m.sin(a) * r
        p.drawLine(QPointF(x1, y1), QPointF(x2, y2))


def draw_card(p, s):
    p.setPen(QPen(QColor("#52525B"), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(2, 3, s - 4, s - 6), 3, 3)
    p.drawLine(QPointF(5, s / 2), QPointF(s - 5, s / 2))


COLOR_GRID = [
    "#000000", "#FFFFFF", "#D4D4D8", "#A1A1AA", "#71717A", "#3F3F46",
    "#BE185D", "#E81123", "#FF5A00", "#FFA500", "#FFD000", "#FFF200",
    "#A3E635", "#22E000", "#047857", "#06B6D4", "#0050EF", "#4C1D95",
    "#7C3AED", "#6B21A8", "#F5DEC8", "#B8956A", "#8B5A2B", "#5C4033",
    "#FF80FF", "#FFC080", "#FFFF80", "#80FF9C", "#80D4FF", "#C0C0FF",
]


class ColorSwatchButton(QPushButton):
    """Nút tròn hiển thị màu (nền ca-rô cho màu trong suốt, gạch chéo khi là 'không màu')."""
    def __init__(self, color, size=22, ring=False, parent=None):
        super().__init__(parent)
        self._color = color
        self._ring = ring
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def set_color(self, color):
        self._color = color
        self.update()

    def set_ring(self, ring: bool):
        self._ring = ring
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        no_color = self._color is None or self._color.alpha() == 0
        clip = QPainterPath()
        clip.addEllipse(r)
        p.setClipPath(clip)
        if no_color:
            p.fillRect(r, QColor("#FFFFFF"))
        else:
            if self._color.alpha() < 255:
                step = max(3, int(r.width() // 4))
                for i in range(0, int(r.width()) + step, step):
                    for j in range(0, int(r.height()) + step, step):
                        dark = ((i // step + j // step) % 2 == 0)
                        p.fillRect(QRectF(r.x() + i, r.y() + j, step, step),
                                   QColor("#D4D4D8") if dark else QColor("#FFFFFF"))
            p.fillRect(r, self._color)
        p.setClipping(False)
        p.setBrush(Qt.BrushStyle.NoBrush)
        if no_color:
            p.setPen(QPen(QColor("#71717A"), 1.4))
            p.drawEllipse(r)
            p.drawLine(QPointF(r.left() + r.width() * 0.2, r.bottom() - r.height() * 0.2),
                       QPointF(r.right() - r.width() * 0.2, r.top() + r.height() * 0.2))
        else:
            p.setPen(QPen(QColor(0, 0, 0, 40), 1))
            p.drawEllipse(r)
        if self._ring:
            p.setPen(QPen(QColor("#2563EB"), 2))
            p.drawEllipse(r.adjusted(-1.5, -1.5, 1.5, 1.5))
        p.end()


class ColorGridPicker(QWidget):
    """Bảng chọn màu lưới 6x5 + thanh Opacity (giống Snipping Tool).
    on_change(color_hoac_None) được gọi mỗi khi chọn màu / kéo Opacity (None = không màu)."""
    def __init__(self, current, allow_none: bool, on_change, parent=None):
        super().__init__(parent)
        self._on_change = on_change
        self._allow_none = allow_none
        self._none = current is None or current.alpha() == 0
        base = QColor("#FFC080") if self._none else QColor(current)
        self._base = QColor(base.red(), base.green(), base.blue())
        self._alpha = 255 if self._none else base.alpha()
        self._buttons = []

        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 12)
        lay.setSpacing(8)

        title = QLabel("Màu sắc")
        title.setStyleSheet("color: #18181B; font-size: 12px; font-weight: 600;")
        lay.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(6)
        cells = ([None] + COLOR_GRID[:-1]) if allow_none else list(COLOR_GRID)
        for idx, hex_val in enumerate(cells):
            btn = ColorSwatchButton(None if hex_val is None else QColor(hex_val), size=28)
            btn.setToolTip("Không màu" if hex_val is None else hex_val)
            btn.clicked.connect(lambda _=False, h=hex_val: self._pick(h))
            self._buttons.append((hex_val, btn))
            grid.addWidget(btn, idx // 6, idx % 6)
        lay.addLayout(grid)

        op_lbl = QLabel("Độ trong suốt (Opacity)")
        op_lbl.setStyleSheet("color: #18181B; font-size: 12px; font-weight: 600;")
        lay.addWidget(op_lbl)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(round(self._alpha / 255 * 100))
        self.slider.setStyleSheet(
            "QSlider::groove:horizontal { height: 8px; border-radius: 4px; background: #E4E4E7; }"
            "QSlider::sub-page:horizontal { background: #3B82F6; border-radius: 4px; }"
            "QSlider::handle:horizontal { background: #FFFFFF; border: 2px solid #3B82F6;"
            " width: 14px; height: 14px; margin: -5px 0; border-radius: 9px; }"
        )
        self.slider.valueChanged.connect(self._on_slider)
        lay.addWidget(self.slider)
        self._refresh_rings()

    def _current(self):
        if self._none:
            return None
        return QColor(self._base.red(), self._base.green(), self._base.blue(), self._alpha)

    def _refresh_rings(self):
        for hex_val, btn in self._buttons:
            if hex_val is None:
                btn.set_ring(self._none)
            else:
                btn.set_ring((not self._none) and QColor(hex_val).rgb() == self._base.rgb())

    def _pick(self, hex_val):
        if hex_val is None:
            self._none = True
        else:
            self._none = False
            self._base = QColor(hex_val)
            if self._alpha == 0:
                self._alpha = 255
                self.slider.blockSignals(True)
                self.slider.setValue(100)
                self.slider.blockSignals(False)
        self._refresh_rings()
        self._on_change(self._current())

    def _on_slider(self, val):
        self._alpha = round(val / 100 * 255)
        if self._none and self._allow_none and val > 0:
            self._none = False
        self._refresh_rings()
        self._on_change(self._current())


SPIN_CSS = (
    "QSpinBox { background-color: #FFFFFF; color: #18181B; border: 1px solid rgba(0,0,0,0.15);"
    " border-radius: 6px; padding-left: 6px; padding-right: 22px; font-weight: 600; font-size: 11px; }"
    "QSpinBox:focus { border: 1.5px solid #2563EB; }"
    "QSpinBox::up-button, QSpinBox::down-button { subcontrol-origin: border; width: 18px;"
    " background-color: #F4F4F5; border-left: 1px solid rgba(0,0,0,0.12); }"
    "QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #E4E4E7; }"
    "QSpinBox::up-button { subcontrol-position: top right; border-top-right-radius: 5px; }"
    "QSpinBox::down-button { subcontrol-position: bottom right; border-bottom-right-radius: 5px; }"
    "QSpinBox::up-arrow { width: 7px; height: 7px; }"
    "QSpinBox::down-arrow { width: 7px; height: 7px; }"
)


class StepperSpin(QWidget):
    """Ô nhập số có nút − / + riêng (thay mũi tên mặc định của QSpinBox bị lỗi hiển thị)."""
    def __init__(self, minimum=0, maximum=999, value=0, suffix="", width=96, parent=None):
        super().__init__(parent)
        self._spin = QSpinBox()
        self._spin.setRange(minimum, maximum)
        self._spin.setSuffix(suffix)
        self._spin.setValue(value)
        self._spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self._spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._spin.setStyleSheet(
            "QSpinBox { background-color: #FFFFFF; color: #18181B; border: 1px solid rgba(0,0,0,0.15);"
            " border-radius: 6px; font-weight: 600; font-size: 11px; padding: 0px 2px; }"
            "QSpinBox:focus { border: 1.5px solid #2563EB; }"
        )
        btn_css = (
            "QToolButton { border: 1px solid rgba(0,0,0,0.12); border-radius: 6px; background: #F4F4F5;"
            " color: #18181B; font-size: 14px; font-weight: 700; }"
            "QToolButton:hover { background: #E4E4E7; }"
        )
        self._minus = QToolButton()
        self._minus.setText("−")
        self._minus.setStyleSheet(btn_css)
        self._minus.setAutoRepeat(True)
        self._minus.setCursor(Qt.CursorShape.PointingHandCursor)
        self._plus = QToolButton()
        self._plus.setText("+")
        self._plus.setStyleSheet(btn_css)
        self._plus.setAutoRepeat(True)
        self._plus.setCursor(Qt.CursorShape.PointingHandCursor)
        self._minus.clicked.connect(lambda: self._spin.setValue(self._spin.value() - 1))
        self._plus.clicked.connect(lambda: self._spin.setValue(self._spin.value() + 1))
        for b in (self._minus, self._plus):
            b.setFixedSize(30, 32)
        self._spin.setFixedSize(width - 60 if width > 70 else 40, 32)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(3)
        lay.addWidget(self._minus)
        lay.addWidget(self._spin)
        lay.addWidget(self._plus)
        self.valueChanged = self._spin.valueChanged

    def value(self):
        return self._spin.value()

    def setValue(self, v):
        self._spin.setValue(v)

    def blockSignals(self, b):
        return self._spin.blockSignals(b)
