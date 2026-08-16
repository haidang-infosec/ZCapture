from PyQt6.QtCore import Qt, QPoint, QPointF, QRectF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPixmap, QIcon, QPainterPath, QFontMetrics
)
from PyQt6.QtWidgets import (
    QWidget, QMenu, QHBoxLayout, QPushButton, QComboBox, QSpinBox, QColorDialog,
    QToolButton, QLabel, QWidgetAction, QFrame
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
