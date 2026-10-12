import os, math, time
from PyQt6.QtCore import Qt, QPoint, QPointF, QRect, QRectF, QSize, QTimer, QThread
from PyQt6.QtGui import (
    QPixmap, QPainter, QAction, QColor, QKeySequence, QShortcut, QGuiApplication,
    QPen, QBrush, QFont, QCursor, QPolygonF, QPainterPath, QIcon, QFontMetrics, QTransform
)
from PyQt6.QtWidgets import (
    QWidget, QMenu, QFileDialog, QHBoxLayout, QLabel, QToolButton, QVBoxLayout,
    QGraphicsDropShadowEffect, QLineEdit, QSlider, QPushButton, QWidgetAction,
    QColorDialog, QFrame
)

from models.annotations import PathItem, ArrowItem, TextItem
from ui import pin_manager

_HEADER_ICON_QSS = """
    QToolButton {
        background-color: transparent;
        color: #52525B;
        border: none;
        border-radius: 8px;
        font-size: 14px;
    }
    QToolButton:hover {
        background-color: #F4F4F5;
        color: #18181B;
    }
    QToolButton:checked {
        background-color: #DBEAFE;
        color: #2563EB;
    }
"""


class _HoverToolButton(QToolButton):
    """QToolButton phát tín hiệu khi chuột hover vào / rời khỏi (dùng cho popup Opacity)."""
    def __init__(self, on_hover_change=None, parent=None):
        super().__init__(parent)
        self._on_hover_change = on_hover_change

    def enterEvent(self, event):
        super().enterEvent(event)
        if self._on_hover_change:
            self._on_hover_change(True)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if self._on_hover_change:
            self._on_hover_change(False)


class _OpacityPopup(QWidget):
    """Popup nhỏ chứa Slider chỉnh độ mờ, hiện khi hover vào icon Opacity trên title bar."""
    def __init__(self, pin_window):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.pin_window = pin_window

        container = QWidget(self)
        container.setObjectName("opacityPopupBox")
        container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        container.setStyleSheet("""
            #opacityPopupBox {
                background-color: rgba(255, 255, 255, 0.98);
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 10px;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        container.setGraphicsEffect(shadow)

        box_layout = QVBoxLayout(container)
        box_layout.setContentsMargins(12, 10, 12, 10)
        box_layout.setSpacing(4)

        lbl = QLabel("Độ mờ cửa sổ")
        lbl.setStyleSheet("color: #52525B; font-size: 11px; font-weight: 600; background: transparent;")
        box_layout.addWidget(lbl)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(40, 100)
        self.slider.setValue(int(pin_window.opacity_val * 100))
        self.slider.setFixedWidth(120)
        self.slider.valueChanged.connect(lambda v: pin_window.set_opacity(v / 100.0))
        box_layout.addWidget(self.slider)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)
        outer.addWidget(container)

    def enterEvent(self, event):
        self.pin_window._opacity_hide_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.pin_window._opacity_hide_timer.start(250)
        super().leaveEvent(event)


# -------------------------------------------------------------------------
# Vector Icon Helpers
# -------------------------------------------------------------------------
def make_opacity_icon(size=18, color="#4B5563") -> QIcon:
    """Tạo Icon Opacity ◐ dạng mảng vòng tròn đôi tương phản nét cao."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    rect = QRectF(2, 2, size - 4, size - 4)
    p.setPen(QPen(QColor(color), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(rect)
    path = QPainterPath()
    path.moveTo(size / 2.0, 2)
    path.arcTo(rect, 90, 180)
    path.closeSubpath()
    p.setBrush(QBrush(QColor(color)))
    p.drawPath(path)
    p.end()
    return QIcon(pm)


def make_scale_reset_icon(size=18, color="#4B5563") -> QIcon:
    """Tạo Icon ⤢ Rescale / Reset Zoom 100% hai mũi tên chéo nét cao."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor(color), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(3, size - 3), QPointF(size - 3, 3))
    p.drawLine(QPointF(size - 8, 3), QPointF(size - 3, 3))
    p.drawLine(QPointF(size - 3, 3), QPointF(size - 3, 8))
    p.drawLine(QPointF(8, size - 3), QPointF(3, size - 3))
    p.drawLine(QPointF(3, size - 3), QPointF(3, size - 8))
    p.end()
    return QIcon(pm)


def make_copy_icon(size=18, color="#4B5563") -> QIcon:
    """Tạo Icon Copy ⧉ chuẩn MS Paint / Windows Fluent Icon."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor(color), 1.5))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(size * 0.28, size * 0.08, size * 0.62, size * 0.62), 2.5, 2.5)
    p.setBrush(QBrush(QColor(255, 255, 255)))
    p.drawRoundedRect(QRectF(size * 0.08, size * 0.28, size * 0.62, size * 0.62), 2.5, 2.5)
    p.end()
    return QIcon(pm)


def make_save_icon(size=18, accent_color="#2563EB") -> QIcon:
    """Tạo Icon Save / Download MS Paint Fluent Style (Nút xanh accent nổi bật)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(accent_color)))
    p.drawRoundedRect(QRectF(1, 1, size - 2, size - 2), 4, 4)
    p.setPen(QPen(QColor(255, 255, 255), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.drawLine(QPointF(size / 2.0, 4), QPointF(size / 2.0, size - 6))
    arrow_head = QPolygonF([
        QPointF(size / 2.0 - 3.5, size - 9),
        QPointF(size / 2.0, size - 5.5),
        QPointF(size / 2.0 + 3.5, size - 9)
    ])
    p.drawPolyline(arrow_head)
    p.end()
    return QIcon(pm)


def make_pencil_icon(size=18, color="#4B5563") -> QIcon:
    """Tạo Icon Bút Vẽ / Markup ✎ MS Paint Ribbon Style."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor(color), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(size * 0.72, size * 0.12)
    path.lineTo(size * 0.88, size * 0.28)
    path.lineTo(size * 0.36, size * 0.80)
    path.lineTo(size * 0.16, size * 0.84)
    path.lineTo(size * 0.20, size * 0.64)
    path.closeSubpath()
    p.drawPath(path)
    p.drawLine(QPointF(size * 0.58, size * 0.26), QPointF(size * 0.74, size * 0.42))
    p.end()
    return QIcon(pm)


def make_highlighter_icon(size=18, color="#F59E0B") -> QIcon:
    """Tạo Icon Highlighter marker MS Paint style."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor(color), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(QBrush(QColor(color)))
    poly = QPolygonF([
        QPointF(size * 0.3, size * 0.8),
        QPointF(size * 0.2, size * 0.6),
        QPointF(size * 0.65, size * 0.15),
        QPointF(size * 0.85, size * 0.35)
    ])
    p.drawPolygon(poly)
    p.end()
    return QIcon(pm)


def make_arrow_draw_icon(size=18, color="#374151") -> QIcon:
    """Tạo Icon Mũi Tên Chỉ Nét Cao."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor(color), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.drawLine(QPointF(3, size - 3), QPointF(size - 3, 3))
    head = QPolygonF([QPointF(size - 8, 3), QPointF(size - 3, 3), QPointF(size - 3, 8)])
    p.setBrush(QBrush(QColor(color)))
    p.drawPolygon(head)
    p.end()
    return QIcon(pm)


def make_text_draw_icon(size=18, color="#374151") -> QIcon:
    """Tạo Icon Chữ A Text Note."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor(color)))
    font = QFont("Segoe UI", int(size * 0.6), QFont.Weight.Bold)
    p.setFont(font)
    p.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "A")
    p.end()
    return QIcon(pm)


def make_eraser_icon(size=18, color="#374151") -> QIcon:
    """Tạo Icon Cục Tẩy (Eraser)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor(color), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(Qt.BrushStyle.NoBrush)
    poly = QPolygonF([
        QPointF(size * 0.4, size * 0.15),
        QPointF(size * 0.85, size * 0.55),
        QPointF(size * 0.55, size * 0.85),
        QPointF(size * 0.15, size * 0.45)
    ])
    p.drawPolygon(poly)
    p.drawLine(QPointF(size * 0.35, size * 0.65), QPointF(size * 0.65, size * 0.35))
    p.end()
    return QIcon(pm)


def make_undo_icon(size=18, color="#374151") -> QIcon:
    """Tạo Icon Undo ↩."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor(color), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(size * 0.8, size * 0.75)
    path.arcTo(QRectF(size * 0.25, size * 0.25, size * 0.55, size * 0.55), 0, 180)
    p.drawPath(path)
    head = QPolygonF([QPointF(size * 0.45, size * 0.12), QPointF(size * 0.22, size * 0.25), QPointF(size * 0.45, size * 0.38)])
    p.setBrush(QBrush(QColor(color)))
    p.drawPolygon(head)
    p.end()
    return QIcon(pm)


def make_redo_icon(size=18, color="#374151") -> QIcon:
    """Tạo Icon Redo ↪."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor(color), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    p.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(size * 0.2, size * 0.75)
    path.arcTo(QRectF(size * 0.2, size * 0.25, size * 0.55, size * 0.55), 180, -180)
    p.drawPath(path)
    head = QPolygonF([QPointF(size * 0.55, size * 0.12), QPointF(size * 0.78, size * 0.25), QPointF(size * 0.55, size * 0.38)])
    p.setBrush(QBrush(QColor(color)))
    p.drawPolygon(head)
    p.end()
    return QIcon(pm)


class PinnedWindow(QWidget):
    """
    Cửa sổ ghim ảnh nổi trên màn hình (Always-On-Top Pin Window).
    Title bar phong cách macOS đồng bộ theme sáng, hỗ trợ vẽ ghi chú trực tiếp lên ảnh,
    kéo mép/góc co giãn kích thước, thu nhỏ về icon chip nổi.
    """
    def __init__(self, pixmap: QPixmap, config_data: dict = None, parent=None, **kwargs):
        super().__init__(parent)
        self.original_pixmap = pixmap
        self.current_scale = 1.0
        self.drag_position = QPoint()
        self.opacity_val = 1.0
        self.config_data = config_data or {}

        # Resizing state
        self.resizing_edge = None
        self.initial_geo = QRect()
        self.drag_start_global = QPoint()
        self.resize_margin = 10

        # Draw mode / annotation layer state
        self.draw_mode = False
        self.draw_tool = "pencil"
        self.current_draw_color = QColor("#EB3232")
        self.annotations = []
        self.redo_stack = []
        self.current_drawing_item = None
        self.annotations_visible = True

        self.label_text = pin_manager.next_pin_label()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setMouseTracking(True)

        self.border_width = 1
        self.header_height = 40

        # Layout Setup
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(self.border_width, self.border_width, self.border_width, self.border_width)
        main_layout.setSpacing(0)

        self._build_header_bar()
        main_layout.addWidget(self.header_bar)

        self.image_container = QWidget()
        main_layout.addWidget(self.image_container)

        init_w = pixmap.width() + self.border_width * 2
        init_h = pixmap.height() + self.header_height + self.border_width * 2
        self.resize(max(280, init_w), max(200, init_h))

        self.esc_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Escape), self)
        self.esc_shortcut.activated.connect(self.close)
        QShortcut(QKeySequence(Qt.Key.Key_Delete), self).activated.connect(self._undo_draw)
        QShortcut(QKeySequence(Qt.Key.Key_Backspace), self).activated.connect(self._undo_draw)
        QShortcut(QKeySequence("Ctrl+Z"), self).activated.connect(self._undo_draw)
        QShortcut(QKeySequence("Ctrl+Y"), self).activated.connect(self._redo_draw)

        self._build_mini_toolbar()

        self._opacity_popup = None
        self._opacity_hide_timer = QTimer(self)
        self._opacity_hide_timer.setSingleShot(True)
        self._opacity_hide_timer.timeout.connect(self._hide_opacity_popup)

        pin_manager.register_pin_window(self)

    # -------------------------------------------------------------------------
    # Title Bar (MS Paint Fluent Ribbon Style, Light Theme)
    # -------------------------------------------------------------------------
    def _build_header_bar(self):
        self.header_bar = QWidget()
        self.header_bar.setObjectName("pinHeaderBar")
        self.header_bar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.header_bar.setFixedHeight(self.header_height)
        self.header_bar.setStyleSheet("""
            #pinHeaderBar {
                background-color: #FFFFFF;
                border-top-left-radius: 12px;
                border-top-right-radius: 12px;
                border-bottom: 1px solid rgba(0,0,0,0.08);
            }
            QToolButton {
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 4px;
            }
            QToolButton:hover {
                background-color: #F3F4F6;
            }
            QToolButton:pressed, QToolButton:checked {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
            }
        """)

        header_layout = QHBoxLayout(self.header_bar)
        header_layout.setContentsMargins(10, 0, 10, 0)
        header_layout.setSpacing(6)

        # Traffic Lights (macOS style)
        traffic_box = QHBoxLayout()
        traffic_box.setSpacing(6)

        red_dot = QPushButton("✕")
        red_dot.setFixedSize(12, 12)
        red_dot.setCursor(Qt.CursorShape.PointingHandCursor)
        red_dot.setToolTip("Đóng ghim (Esc)")
        red_dot.setStyleSheet("""
            QPushButton { background-color: #FF5F57; border: none; border-radius: 6px; color: transparent; font-size: 8px; padding: 0px; }
            QPushButton:hover { color: #800000; font-weight: bold; }
        """)
        red_dot.clicked.connect(self.close)
        traffic_box.addWidget(red_dot)

        yellow_dot = QPushButton("−")
        yellow_dot.setFixedSize(12, 12)
        yellow_dot.setCursor(Qt.CursorShape.PointingHandCursor)
        yellow_dot.setToolTip("Thu nhỏ thành icon chip nổi")
        yellow_dot.setStyleSheet("""
            QPushButton { background-color: #FEBC2E; border: none; border-radius: 6px; color: transparent; font-size: 9px; padding: 0px; }
            QPushButton:hover { color: #5C3C00; font-weight: bold; }
        """)
        yellow_dot.clicked.connect(self._minimize)
        traffic_box.addWidget(yellow_dot)

        green_dot = QPushButton("+")
        green_dot.setFixedSize(12, 12)
        green_dot.setCursor(Qt.CursorShape.PointingHandCursor)
        green_dot.setToolTip("Về tỷ lệ 100%")
        green_dot.setStyleSheet("""
            QPushButton { background-color: #28C840; border: none; border-radius: 6px; color: transparent; font-size: 9px; padding: 0px; }
            QPushButton:hover { color: #004D10; font-weight: bold; }
        """)
        green_dot.clicked.connect(self._reset_zoom)
        traffic_box.addWidget(green_dot)

        header_layout.addLayout(traffic_box)

        # Pin icon & Title Label
        pin_icon_lbl = QLabel()
        pin_icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        pin_icon_lbl.setPixmap(self._make_outline_pin_pixmap(14, "#4B5563"))
        header_layout.addWidget(pin_icon_lbl)

        title_lbl = QLabel(self.label_text)
        title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        title_lbl.setStyleSheet("color: #374151; font-size: 12px; font-weight: 600; background: transparent;")
        header_layout.addWidget(title_lbl)

        header_layout.addStretch()

        def add_divider():
            div = QFrame()
            div.setFrameShape(QFrame.Shape.VLine)
            div.setFixedSize(1, 16)
            div.setStyleSheet("background-color: rgba(0,0,0,0.1); border: none;")
            header_layout.addWidget(div)

        # 1. Opacity Toggle Button (Hover)
        self.opacity_btn = _HoverToolButton(self._on_opacity_hover)
        self.opacity_btn.setIcon(make_opacity_icon(18, "#4B5563"))
        self.opacity_btn.setIconSize(QSize(18, 18))
        self.opacity_btn.setToolTip("Chỉnh độ mờ cửa sổ (hover)")
        self.opacity_btn.setFixedSize(30, 30)
        self.opacity_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        header_layout.addWidget(self.opacity_btn)

        # 2. Scale Reset Button
        reset_zoom_btn = QToolButton()
        reset_zoom_btn.setIcon(make_scale_reset_icon(18, "#4B5563"))
        reset_zoom_btn.setIconSize(QSize(18, 18))
        reset_zoom_btn.setToolTip("Về tỷ lệ kích thước 100%")
        reset_zoom_btn.setFixedSize(30, 30)
        reset_zoom_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_zoom_btn.clicked.connect(self._reset_zoom)
        header_layout.addWidget(reset_zoom_btn)

        add_divider()

        # 3. Copy Button (MS Paint Ribbon Style)
        copy_btn = QToolButton()
        copy_btn.setIcon(make_copy_icon(18, "#4B5563"))
        copy_btn.setIconSize(QSize(18, 18))
        copy_btn.setToolTip("Sao chép ảnh vào Clipboard (Ctrl+C)")
        copy_btn.setFixedSize(30, 30)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self.copy_to_clipboard)
        header_layout.addWidget(copy_btn)

        # 4. Save Button (MS Paint Blue Accent Button)
        save_btn = QToolButton()
        save_btn.setIcon(make_save_icon(18, "#2563EB"))
        save_btn.setIconSize(QSize(18, 18))
        save_btn.setToolTip("Lưu file ảnh (Ctrl+S)")
        save_btn.setFixedSize(30, 30)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.save_to_file)
        header_layout.addWidget(save_btn)

        add_divider()

        # 5. Pencil / Draw Mode Toggle Button
        self.draw_toggle_btn = QToolButton()
        self.draw_toggle_btn.setIcon(make_pencil_icon(18, "#4B5563"))
        self.draw_toggle_btn.setIconSize(QSize(18, 18))
        self.draw_toggle_btn.setToolTip("Bật/Tắt chế độ vẽ ghi chú")
        self.draw_toggle_btn.setCheckable(True)
        self.draw_toggle_btn.setFixedSize(30, 30)
        self.draw_toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.draw_toggle_btn.clicked.connect(lambda checked: self.set_draw_mode(checked))
        header_layout.addWidget(self.draw_toggle_btn)

    @staticmethod
    def _make_outline_pin_pixmap(size: int, color: str) -> QPixmap:
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setPen(QPen(QColor(color), 1.4))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(size * 0.18, size * 0.04, size * 0.64, size * 0.64))
        path = QPainterPath()
        path.moveTo(size * 0.34, size * 0.55)
        path.lineTo(size * 0.5, size * 0.96)
        path.lineTo(size * 0.66, size * 0.55)
        path.closeSubpath()
        p.setPen(QPen(QColor(color), 1.2))
        p.drawPath(path)
        p.end()
        return pm

    # -------------------------------------------------------------------------
    # Mini Draw Toolbar (Pill nổi ở đáy ảnh, chỉ hiện khi Draw mode bật)
    # -------------------------------------------------------------------------
    def _build_mini_toolbar(self):
        self.mini_toolbar = QWidget(self)
        self.mini_toolbar.setObjectName("miniDrawToolbar")
        self.mini_toolbar.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.mini_toolbar.setStyleSheet("""
            #miniDrawToolbar {
                background-color: rgba(255, 255, 255, 0.98);
                border: 1px solid rgba(0, 0, 0, 0.08);
                border-radius: 20px;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                border-radius: 15px;
                padding: 4px;
                min-width: 30px;
                min-height: 30px;
            }
            QToolButton:hover {
                background-color: #F3F4F6;
            }
            QToolButton:checked {
                background-color: #DBEAFE;
                border: 1px solid #93C5FD;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self.mini_toolbar)
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.mini_toolbar.setGraphicsEffect(shadow)

        layout = QHBoxLayout(self.mini_toolbar)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        self._tool_buttons = {}

        def add_tool_btn(tool_id, icon, tooltip):
            btn = QToolButton()
            btn.setIcon(icon)
            btn.setIconSize(QSize(18, 18))
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setFixedSize(30, 30)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda: self._select_draw_tool(tool_id))
            layout.addWidget(btn)
            self._tool_buttons[tool_id] = btn

        add_tool_btn("pencil", make_pencil_icon(18, "#2563EB"), "Bút vẽ tự do")
        add_tool_btn("highlighter", make_highlighter_icon(18, "#F59E0B"), "Highlight marker")
        add_tool_btn("arrow", make_arrow_draw_icon(18, "#374151"), "Mũi tên chỉ")
        add_tool_btn("text", make_text_draw_icon(18, "#374151"), "Text note (click vào ảnh để đặt ghi chú)")

        self.mini_color_btn = QPushButton()
        self.mini_color_btn.setFixedSize(22, 22)
        self.mini_color_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mini_color_btn.setToolTip("Đổi màu vẽ")
        self.mini_color_btn.clicked.connect(self._open_color_menu)
        layout.addWidget(self.mini_color_btn)
        self._update_mini_color_btn()

        add_tool_btn("eraser", make_eraser_icon(18, "#374151"), "Tẩy (xoá nét vừa vẽ)")

        div = QFrame()
        div.setFrameShape(QFrame.Shape.VLine)
        div.setFixedSize(1, 18)
        div.setStyleSheet("background: rgba(0,0,0,0.1); border: none;")
        layout.addWidget(div)

        undo_btn = QToolButton()
        undo_btn.setIcon(make_undo_icon(18, "#374151"))
        undo_btn.setIconSize(QSize(18, 18))
        undo_btn.setToolTip("Undo (Ctrl+Z)")
        undo_btn.setFixedSize(30, 30)
        undo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        undo_btn.clicked.connect(self._undo_draw)
        layout.addWidget(undo_btn)

        redo_btn = QToolButton()
        redo_btn.setIcon(make_redo_icon(18, "#374151"))
        redo_btn.setIconSize(QSize(18, 18))
        redo_btn.setToolTip("Redo (Ctrl+Y)")
        redo_btn.setFixedSize(30, 30)
        redo_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        redo_btn.clicked.connect(self._redo_draw)
        layout.addWidget(redo_btn)

        self._tool_buttons["pencil"].setChecked(True)
        self.mini_toolbar.adjustSize()
        self.mini_toolbar.hide()

        self._mini_toolbar_timer = QTimer(self)
        self._mini_toolbar_timer.setSingleShot(True)
        self._mini_toolbar_timer.timeout.connect(self.mini_toolbar.hide)

    def _select_draw_tool(self, tool_id):
        self.draw_tool = tool_id
        for tid, btn in self._tool_buttons.items():
            btn.setChecked(tid == tool_id)
        self._show_mini_toolbar()

    def _update_mini_color_btn(self):
        c = self.current_draw_color.name()
        self.mini_color_btn.setStyleSheet(
            f"background-color: {c}; border-radius: 12px; border: 2px solid #FFFFFF;"
        )

    def _open_color_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #FFFFFF; border: 1px solid rgba(0,0,0,0.1); border-radius: 10px; padding: 6px; }
        """)
        swatch_widget = QWidget()
        row = QHBoxLayout(swatch_widget)
        row.setContentsMargins(4, 2, 4, 2)
        row.setSpacing(6)

        presets = ["#EB3232", "#F59E0B", "#22C55E", "#3B82F6", "#8B5CF6", "#18181B"]
        for hex_code in presets:
            b = QPushButton()
            b.setFixedSize(18, 18)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setStyleSheet(f"background-color: {hex_code}; border-radius: 9px; border: 1.5px solid rgba(0,0,0,0.15);")
            b.clicked.connect(lambda _, h=hex_code: self._pick_draw_color(QColor(h), menu))
            row.addWidget(b)

        custom_btn = QPushButton("+")
        custom_btn.setFixedSize(18, 18)
        custom_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        custom_btn.setStyleSheet("""
            QPushButton { background-color: #F4F4F5; color: #3F3F46; border: 1px solid rgba(0,0,0,0.15); border-radius: 9px; font-weight: bold; }
            QPushButton:hover { background-color: #DBEAFE; color: #2563EB; }
        """)
        custom_btn.clicked.connect(lambda: self._pick_custom_draw_color(menu))
        row.addWidget(custom_btn)

        action = QWidgetAction(menu)
        action.setDefaultWidget(swatch_widget)
        menu.addAction(action)

        pos = self.mini_color_btn.mapToGlobal(QPoint(-20, -46))
        menu.exec(pos)

    def _pick_draw_color(self, color, menu):
        self.current_draw_color = color
        self._update_mini_color_btn()
        menu.close()

    def _pick_custom_draw_color(self, menu):
        menu.close()
        col = QColorDialog.getColor(self.current_draw_color, self, "Chọn màu vẽ")
        if col.isValid():
            self.current_draw_color = col
            self._update_mini_color_btn()

    def _show_mini_toolbar(self):
        if not self.draw_mode:
            return
        self.mini_toolbar.show()
        self._position_mini_toolbar()
        self.mini_toolbar.raise_()
        self._mini_toolbar_timer.start(3000)

    def _position_mini_toolbar(self):
        self.mini_toolbar.adjustSize()
        tw, th = self.mini_toolbar.width(), self.mini_toolbar.height()
        x = (self.width() - tw) // 2
        y = self.height() - th - 14
        self.mini_toolbar.move(max(8, x), max(self.header_height + 8, y))

    # -------------------------------------------------------------------------
    # Draw Mode
    # -------------------------------------------------------------------------
    def set_draw_mode(self, enabled: bool):
        self.draw_mode = enabled
        self.draw_toggle_btn.setChecked(enabled)
        self.current_drawing_item = None
        if enabled:
            self.setCursor(Qt.CursorShape.CrossCursor)
            self._show_mini_toolbar()
        else:
            self.mini_toolbar.hide()
            self._mini_toolbar_timer.stop()
            self.setCursor(Qt.CursorShape.ArrowCursor)
        self.update()

    def _undo_draw(self):
        if self.annotations:
            item = self.annotations.pop()
            self.redo_stack.append(item)
            self.update()

    def _redo_draw(self):
        if self.redo_stack:
            item = self.redo_stack.pop()
            self.annotations.append(item)
            self.update()

    def _toggle_annotations_visible(self):
        self.annotations_visible = not self.annotations_visible
        self.update()

    def _clear_annotations(self):
        self.annotations.clear()
        self.redo_stack.clear()
        self.update()

    def _start_drawing(self, img_pos: QPointF):
        p = img_pos.toPoint()
        width = 4
        if self.draw_tool == "pencil":
            self.current_drawing_item = PathItem([p], self.current_draw_color, width)
        elif self.draw_tool == "highlighter":
            item = PathItem([p], self.current_draw_color, width)
            item.tool_type = "highlighter"
            self.current_drawing_item = item
        elif self.draw_tool == "arrow":
            self.current_drawing_item = ArrowItem(p, p, self.current_draw_color, width)

    def _continue_drawing(self, img_pos: QPointF):
        item = self.current_drawing_item
        if not item:
            return
        p = img_pos.toPoint()
        if isinstance(item, PathItem):
            item.points.append(p)
        elif isinstance(item, ArrowItem):
            item.end_p = p

    def _erase_at(self, img_pos: QPointF):
        pt = img_pos.toPoint()
        for item in reversed(self.annotations):
            if item.get_bounding_rect().adjusted(-6, -6, 6, 6).contains(pt):
                self.annotations.remove(item)
                self.redo_stack.append(item)
                self.update()
                return

    def _open_text_note(self, img_pos: QPointF, target_item=None):
        tx, ty, scale = self._image_display_rect()

        if target_item:
            img_pos = QPointF(target_item.pos.x(), target_item.pos.y())
            initial_txt = target_item.text
        else:
            initial_txt = ""

        widget_x = int(img_pos.x() * scale + tx)
        widget_y = int(img_pos.y() * scale + ty)

        edit = QLineEdit(self)
        font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        edit.setFont(font)

        text_col = self.current_draw_color if not target_item else target_item.color
        color_hex = text_col.name()

        edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                color: {color_hex};
                border: 1.5px dashed #2563EB;
                border-radius: 6px;
                padding: 4px 8px;
                selection-background-color: #2563EB;
                selection-color: #FFFFFF;
            }}
        """)

        metrics = QFontMetrics(font)
        w = max(140, metrics.horizontalAdvance(initial_txt if initial_txt else "Ghi chú...") + 24)
        h = max(30, metrics.height() + 8)

        edit.setGeometry(widget_x, widget_y, w, h)
        edit.setText(initial_txt)
        edit.setPlaceholderText("Nhập ghi chú...")
        edit.show()
        edit.raise_()
        edit.setFocus()

        def update_edit_size(txt):
            if edit:
                m = QFontMetrics(font)
                nw = max(140, m.horizontalAdvance(txt if txt else "Ghi chú...") + 24)
                nh = max(30, m.height() + 8)
                edit.resize(nw, nh)

        edit.textChanged.connect(update_edit_size)

        state = {"done": False}

        def commit():
            if state["done"]:
                return
            state["done"] = True
            txt = edit.text().strip()
            edit.deleteLater()

            if target_item:
                if txt:
                    target_item.text = txt
                    target_item.color = text_col
                    target_item.calc_rect()
                else:
                    if target_item in self.annotations:
                        self.annotations.remove(target_item)
            else:
                if txt:
                    item = TextItem(
                        img_pos.toPoint(), txt, font, text_col,
                        bg_color=QColor(16, 16, 24), bg_mode="none", bg_opacity=0.9
                    )
                    self.annotations.append(item)
                    self.redo_stack.clear()
            self.update()

        edit.returnPressed.connect(commit)
        edit.editingFinished.connect(commit)

    def _draw_annotation_item(self, painter: QPainter, item):
        if isinstance(item, PathItem):
            if len(item.points) < 2:
                return
            if getattr(item, "tool_type", "pencil") == "highlighter":
                col = QColor(item.color)
                col.setAlpha(110)
                pen = QPen(col, item.stroke_width * 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            else:
                pen = QPen(item.color, item.stroke_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            path = QPainterPath()
            path.moveTo(QPointF(item.points[0]))
            for i in range(1, len(item.points) - 1):
                p1, p2 = item.points[i], item.points[i + 1]
                mid = QPointF((p1.x() + p2.x()) / 2.0, (p1.y() + p2.y()) / 2.0)
                path.quadTo(QPointF(p1), mid)
            if len(item.points) > 1:
                path.lineTo(QPointF(item.points[-1]))
            painter.drawPath(path)

        elif isinstance(item, ArrowItem):
            pen = QPen(item.color, item.stroke_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawLine(item.start_p, item.end_p)
            angle = math.atan2(item.end_p.y() - item.start_p.y(), item.end_p.x() - item.start_p.x())
            arrow_len = 14
            p1 = item.end_p - QPoint(int(arrow_len * math.cos(angle - math.pi / 6)), int(arrow_len * math.sin(angle - math.pi / 6)))
            p2 = item.end_p - QPoint(int(arrow_len * math.cos(angle + math.pi / 6)), int(arrow_len * math.sin(angle + math.pi / 6)))
            painter.setBrush(QBrush(item.color))
            painter.drawPolygon(QPolygonF([QPointF(item.end_p), QPointF(p1), QPointF(p2)]))

        elif isinstance(item, TextItem):
            painter.setFont(item.font)
            rect = item.get_bounding_rect()
            if getattr(item, "bg_mode", "none") in ("badge", "color"):
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QBrush(getattr(item, "bg_color", QColor(16, 16, 24))))
                painter.drawRoundedRect(rect, 6, 6)
                painter.setPen(QPen(item.color))
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, item.text)
            else:
                # bg_mode == "none": Chữ vector nguyên bản sắc nét không bóng đen trùng lặp
                painter.setPen(QPen(item.color))
                painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, item.text)

    def get_merged_pixmap(self) -> QPixmap:
        """Ghép layer ghi chú vào ảnh gốc thành 1 ảnh phẳng duy nhất (dùng khi Copy/Save)."""
        if not self.annotations:
            return self.original_pixmap
        result = QPixmap(self.original_pixmap)
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        for item in self.annotations:
            self._draw_annotation_item(painter, item)
        painter.end()
        return result

    # -------------------------------------------------------------------------
    # Toạ độ: ánh xạ giữa vùng hiển thị trên widget <-> pixel ảnh gốc
    # -------------------------------------------------------------------------
    def _image_display_rect(self):
        img_area = QRect(
            self.border_width,
            self.header_height + self.border_width,
            max(1, self.width() - self.border_width * 2),
            max(1, self.height() - self.header_height - self.border_width * 2)
        )
        ow, oh = max(1, self.original_pixmap.width()), max(1, self.original_pixmap.height())
        scale = max(0.01, min(img_area.width() / ow, img_area.height() / oh))
        disp_w, disp_h = ow * scale, oh * scale
        tx = img_area.left() + (img_area.width() - disp_w) / 2.0
        ty = img_area.top() + (img_area.height() - disp_h) / 2.0
        return tx, ty, scale

    def widget_to_image_pos(self, pos: QPoint) -> QPointF:
        tx, ty, scale = self._image_display_rect()
        return QPointF((pos.x() - tx) / scale, (pos.y() - ty) / scale)

    # -------------------------------------------------------------------------
    # Resize theo mép/góc cửa sổ
    # -------------------------------------------------------------------------
    def get_resize_edge_at(self, pos: QPoint) -> str:
        """Xác định mép hoặc góc kéo co giãn kích thước cửa sổ."""
        w, h = self.width(), self.height()
        m = self.resize_margin

        x, y = pos.x(), pos.y()

        top = y <= m
        bottom = y >= h - m
        left = x <= m
        right = x >= w - m

        if top and left: return "tl"
        if top and right: return "tr"
        if bottom and left: return "bl"
        if bottom and right: return "br"
        if top: return "t"
        if bottom: return "b"
        if left: return "l"
        if right: return "r"

        return None

    def update_cursor_icon(self, edge: str):
        if edge in ("tl", "br"):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif edge in ("tr", "bl"):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif edge in ("t", "b"):
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        elif edge in ("l", "r"):
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    # -------------------------------------------------------------------------
    # Paint (Vẽ ảnh trực tiếp 1:1 Subpixel resolution sắc nét 100%)
    # -------------------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        if hasattr(QPainter.RenderHint, "LosslessImageRendering"):
            painter.setRenderHint(QPainter.RenderHint.LosslessImageRendering, True)
        painter.setOpacity(self.opacity_val)

        w, h = self.width(), self.height()

        # Nền cửa sổ bo góc 12px với viền xám mờ nổi bật bao quanh
        painter.setPen(QPen(QColor(0, 0, 0, 48), 1.4))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.drawRoundedRect(QRectF(0.7, 0.7, w - 1.4, h - 1.4), 12, 12)

        tx, ty, scale = self._image_display_rect()
        ow, oh = max(1, self.original_pixmap.width()), max(1, self.original_pixmap.height())
        disp_w, disp_h = ow * scale, oh * scale

        # Vẽ trực tiếp mảng pixel gốc 1:1 của GPU lên QRectF hiển thị (Sắc nét tuyệt đối trên màn HiDPI/2K/4K)
        dest_rect = QRectF(tx, ty, disp_w, disp_h)
        src_rect = QRectF(0, 0, ow, oh)
        painter.drawPixmap(dest_rect, self.original_pixmap, src_rect)

        # Viền xám mờ mảnh bao quanh vùng ảnh
        painter.setPen(QPen(QColor(0, 0, 0, 36), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(dest_rect)

        # Layer ghi chú (annotations) — vẽ theo đúng tỉ lệ hiển thị hiện tại
        if self.annotations_visible:
            painter.save()
            painter.translate(tx, ty)
            painter.scale(scale, scale)
            for item in self.annotations:
                self._draw_annotation_item(painter, item)
            if self.current_drawing_item:
                self._draw_annotation_item(painter, self.current_drawing_item)
            painter.restore()

        # Resize grip (3 gạch chéo) góc dưới phải — ẩn khi đang Draw mode
        if not self.draw_mode:
            self._draw_resize_grip(painter, w, h)

    @staticmethod
    def _draw_resize_grip(painter: QPainter, w: int, h: int):
        painter.setPen(QPen(QColor(0, 0, 0, 90), 1.4))
        base_x, base_y = w - 5, h - 5
        for i in range(3):
            off = i * 5
            painter.drawLine(QPointF(base_x - off, base_y), QPointF(base_x, base_y - off))

    # -------------------------------------------------------------------------
    # Mouse events — phân biệt rõ Draw mode (vẽ) và View mode (kéo/resize cửa sổ)
    # -------------------------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            # 1. Kéo thanh Header bar LUÔN LUÔN di chuyển cửa sổ (kể cả khi đang bật Draw mode)
            if pos.y() <= self.header_height:
                self._is_dragging_header = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()
                return

            # 2. Nếu đang bật Draw mode, thực hiện vẽ chú thích trên vùng ảnh
            if self.draw_mode:
                self._show_mini_toolbar()
                img_pos = self.widget_to_image_pos(pos)
                if self.draw_tool == "text":
                    self._open_text_note(img_pos)
                elif self.draw_tool == "eraser":
                    self._erase_at(img_pos)
                else:
                    self._start_drawing(img_pos)
                event.accept()
                return

            # 3. View mode: co giãn kích thước theo mép hoặc kéo di chuyển bằng ảnh
            edge = self.get_resize_edge_at(pos)
            if edge:
                self.resizing_edge = edge
                self.drag_start_global = event.globalPosition().toPoint()
                self.initial_geo = self.geometry()
            else:
                self.resizing_edge = None
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

            event.accept()

    def mouseMoveEvent(self, event):
        global_pos = event.globalPosition().toPoint()
        pos = event.pos()

        # Di chuyển cửa sổ bằng Header bar
        if getattr(self, "_is_dragging_header", False):
            if event.buttons() & Qt.MouseButton.LeftButton:
                self.move(global_pos - self.drag_position)
                event.accept()
                return

        if self.draw_mode:
            self._show_mini_toolbar()
            if event.buttons() & Qt.MouseButton.LeftButton:
                img_pos = self.widget_to_image_pos(pos)
                if self.draw_tool == "eraser":
                    self._erase_at(img_pos)
                elif self.current_drawing_item:
                    self._continue_drawing(img_pos)
                    self.update()
            return

        if self.resizing_edge:
            delta = global_pos - self.drag_start_global
            r = QRect(self.initial_geo)
            min_w, min_h = 220, 150

            is_corner = self.resizing_edge in ("tl", "tr", "bl", "br")
            lock_aspect = is_corner and not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)

            if lock_aspect:
                aspect = self.initial_geo.width() / max(1, self.initial_geo.height())
                if "r" in self.resizing_edge:
                    new_w = max(min_w, self.initial_geo.width() + delta.x())
                else:
                    new_w = max(min_w, self.initial_geo.width() - delta.x())
                new_h = max(min_h, int(new_w / aspect))

                if "r" in self.resizing_edge:
                    r.setRight(r.left() + new_w)
                else:
                    r.setLeft(r.right() - new_w)
                if "b" in self.resizing_edge:
                    r.setBottom(r.top() + new_h)
                else:
                    r.setTop(r.bottom() - new_h)
            else:
                if "r" in self.resizing_edge:
                    r.setRight(max(r.left() + min_w, self.initial_geo.right() + delta.x()))
                if "l" in self.resizing_edge:
                    r.setLeft(min(r.right() - min_w, self.initial_geo.left() + delta.x()))
                if "b" in self.resizing_edge:
                    r.setBottom(max(r.top() + min_h, self.initial_geo.bottom() + delta.y()))
                if "t" in self.resizing_edge:
                    r.setTop(min(r.bottom() - min_h, self.initial_geo.top() + delta.y()))

            self.setGeometry(r)
            self.update()
            event.accept()

        elif event.buttons() & Qt.MouseButton.LeftButton:
            self.move(global_pos - self.drag_position)
            event.accept()

        else:
            edge = self.get_resize_edge_at(pos)
            self.update_cursor_icon(edge)

    def mouseReleaseEvent(self, event):
        self._is_dragging_header = False
        if self.draw_mode:
            if event.button() == Qt.MouseButton.LeftButton and self.current_drawing_item:
                self.annotations.append(self.current_drawing_item)
                self.redo_stack.clear()
                self.current_drawing_item = None
                self.update()
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.resizing_edge = None

    def mouseDoubleClickEvent(self, event):
        """Nhấp kép chuột trái để sửa ghi chú chữ hoặc đóng nhanh cửa sổ ghim."""
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.pos()
            img_pos = self.widget_to_image_pos(pos)
            for item in reversed(self.annotations):
                if isinstance(item, TextItem) and item.get_bounding_rect().adjusted(-6, -6, 6, 6).contains(img_pos.toPoint()):
                    self._open_text_note(img_pos, target_item=item)
                    event.accept()
                    return

            if not self.draw_mode:
                self.close()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, "draw_mode", False):
            self._position_mini_toolbar()

    def showEvent(self, event):
        super().showEvent(event)
        pin_manager.notify_shown(self)

    def closeEvent(self, event):
        pin_manager.unregister_pin_window(self)
        super().closeEvent(event)

    def wheelEvent(self, event):
        """Phóng to / Thu nhỏ bằng con lăn chuột, hoặc chỉnh Opacity nếu giữ Ctrl/Alt."""
        modifiers = event.modifiers()
        delta = event.angleDelta().y()
        if modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier):
            step = 0.05 if delta > 0 else -0.05
            new_op = max(0.15, min(1.0, self.opacity_val + step))
            self.set_opacity(new_op)
        else:
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()

    def zoom_in(self):
        self.current_scale *= 1.1
        self.apply_scale()

    def zoom_out(self):
        self.current_scale *= 0.9
        self.apply_scale()

    def apply_scale(self):
        self.current_scale = max(0.2, min(5.0, self.current_scale))
        new_w = int(self.original_pixmap.width() * self.current_scale) + self.border_width * 2
        new_h = int(self.original_pixmap.height() * self.current_scale) + self.header_height + self.border_width * 2
        self.resize(max(280, new_w), max(200, new_h))
        self.update()

    def _reset_zoom(self):
        self.current_scale = 1.0
        self.apply_scale()

    def rotate_clockwise(self):
        """Xoay ảnh 90 độ cùng chiều kim đồng hồ."""
        transform = QTransform().rotate(90)
        self.original_pixmap = self.original_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        self.apply_scale()
        self.update()

    def rotate_counter_clockwise(self):
        """Xoay ảnh 90 độ ngược chiều kim đồng hồ."""
        transform = QTransform().rotate(-90)
        self.original_pixmap = self.original_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        self.apply_scale()
        self.update()

    def flip_horizontal(self):
        """Lật ảnh theo trục ngang."""
        transform = QTransform().scale(-1, 1)
        self.original_pixmap = self.original_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        self.update()

    def flip_vertical(self):
        """Lật ảnh theo trục dọc."""
        transform = QTransform().scale(1, -1)
        self.original_pixmap = self.original_pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
        self.update()

    def perform_ocr(self):
        """Trích xuất chữ trực tiếp từ ảnh ghim bằng OCR Engine."""
        from ui.overlay.ocr_worker import _OCRWorker
        from ui.ocr_dialog import OCRDialog
        pm = self.get_merged_pixmap()
        if pm.isNull():
            return

        self._ocr_thread = QThread()
        self._ocr_worker = _OCRWorker(pm)
        self._ocr_worker.moveToThread(self._ocr_thread)
        self._ocr_thread.started.connect(self._ocr_worker.run)

        def on_ocr_done(text):
            self._ocr_thread.quit()
            self._ocr_thread.wait()
            dlg = OCRDialog(text, parent=self)
            dlg.exec()

        self._ocr_worker.finished.connect(on_ocr_done)
        self._ocr_thread.start()

    # -------------------------------------------------------------------------
    # Minimize / Opacity
    # -------------------------------------------------------------------------
    def _minimize(self):
        pin_manager.minimize_window(self)

    def _on_opacity_hover(self, entered: bool):
        if entered:
            self._opacity_hide_timer.stop()
            self._show_opacity_popup()
        else:
            self._opacity_hide_timer.start(250)

    def _show_opacity_popup(self):
        if self._opacity_popup is None:
            self._opacity_popup = _OpacityPopup(self)
        pos_global = self.opacity_btn.mapToGlobal(QPoint(-40, self.opacity_btn.height() + 4))
        self._opacity_popup.move(pos_global)
        self._opacity_popup.show()

    def _hide_opacity_popup(self):
        if self._opacity_popup is not None:
            self._opacity_popup.hide()

    def set_opacity(self, opacity: float):
        self.opacity_val = opacity
        self.setWindowOpacity(opacity)
        self.update()

    # -------------------------------------------------------------------------
    # Context Menu
    # -------------------------------------------------------------------------
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(255, 255, 255, 0.96);
                color: #1C1C1E;
                border: 1.5px solid rgba(0,0,0,0.1);
                border-radius: 10px;
                padding: 6px 4px;
                font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
                font-size: 13px;
                font-weight: 600;
            }
            QMenu::item {
                padding: 6px 20px 6px 12px;
                margin: 2px 4px;
                border-radius: 6px;
                color: #1C1C1E;
            }
            QMenu::item:selected {
                background-color: #007AFF;
                color: #FFFFFF;
            }
            QMenu::separator {
                height: 1px;
                background-color: rgba(0, 0, 0, 0.12);
                margin: 4px 8px;
            }
        """)

        draw_act = QAction(("✎  Tắt chế độ vẽ" if self.draw_mode else "✎  Bật chế độ vẽ"), self)
        draw_act.triggered.connect(lambda: self.set_draw_mode(not self.draw_mode))
        menu.addAction(draw_act)

        toggle_vis_act = QAction(("🙈  Ẩn ghi chú" if self.annotations_visible else "👁  Hiện ghi chú"), self)
        toggle_vis_act.setEnabled(bool(self.annotations))
        toggle_vis_act.triggered.connect(self._toggle_annotations_visible)
        menu.addAction(toggle_vis_act)

        clear_act = QAction("🗑  Xoá toàn bộ ghi chú", self)
        clear_act.setEnabled(bool(self.annotations))
        clear_act.triggered.connect(self._clear_annotations)
        menu.addAction(clear_act)

        menu.addSeparator()

        ocr_act = QAction("🔍  Trích xuất văn bản (OCR)", self)
        ocr_act.triggered.connect(self.perform_ocr)
        menu.addAction(ocr_act)

        transform_menu = menu.addMenu("🔄  Xoay & Lật ảnh")
        transform_menu.setStyleSheet(menu.styleSheet())

        rot_cw = QAction("↷  Xoay 90° cùng chiều kim đồng hồ", self)
        rot_cw.triggered.connect(self.rotate_clockwise)
        transform_menu.addAction(rot_cw)

        rot_ccw = QAction("↶  Xoay 90° ngược chiều kim đồng hồ", self)
        rot_ccw.triggered.connect(self.rotate_counter_clockwise)
        transform_menu.addAction(rot_ccw)

        flip_h = QAction("⇄  Lật ngang (Flip Horizontal)", self)
        flip_h.triggered.connect(self.flip_horizontal)
        transform_menu.addAction(flip_h)

        flip_v = QAction("⇅  Lật dọc (Flip Vertical)", self)
        flip_v.triggered.connect(self.flip_vertical)
        transform_menu.addAction(flip_v)

        menu.addSeparator()

        copy_act = QAction("📋 Sao chép vào Clipboard", self)
        copy_act.triggered.connect(self.copy_to_clipboard)
        menu.addAction(copy_act)

        save_act = QAction("💾 Lưu file ảnh", self)
        save_act.triggered.connect(self.save_to_file)
        menu.addAction(save_act)

        menu.addSeparator()

        op_menu = menu.addMenu("Độ trong suốt (Ctrl+Cuộn chuột)")
        op_menu.setStyleSheet(menu.styleSheet())
        for val in [100, 80, 60, 40]:
            act = QAction(f"{val}%", self)
            act.setCheckable(True)
            if int(self.opacity_val * 100) == val:
                act.setChecked(True)
            act.triggered.connect(lambda checked, v=val: self.set_opacity(v / 100.0))
            op_menu.addAction(act)

        reset_zoom_act = QAction("🔍  Tỉ lệ gốc 100%", self)
        reset_zoom_act.triggered.connect(self._reset_zoom)
        menu.addAction(reset_zoom_act)

        menu.addSeparator()

        min_act = QAction("🗕  Thu nhỏ", self)
        min_act.triggered.connect(self._minimize)
        menu.addAction(min_act)

        close_act = QAction("✕ Đóng ghim (Esc / Click đúp)", self)
        close_act.triggered.connect(self.close)
        menu.addAction(close_act)

        menu.exec(event.globalPos())

    def copy_to_clipboard(self):
        pm = self.get_merged_pixmap()
        cb = QGuiApplication.clipboard()
        cb.setPixmap(pm)

    def save_to_file(self):
        pat = self.config_data.get("filename_pattern", "ZCapture_{date}_{time}") if hasattr(self, "config_data") and isinstance(self.config_data, dict) else "ZCapture_{date}_{time}"
        auto_name = pat.replace("{date}", time.strftime("%Y%m%d")).replace("{time}", time.strftime("%H%M%S"))
        if not auto_name.endswith(".png") and not auto_name.endswith(".jpg"):
            auto_name += ".png"
        default_dir = self.config_data.get("save_dir", "") if hasattr(self, "config_data") and isinstance(self.config_data, dict) else ""
        default_path = os.path.join(default_dir, auto_name) if default_dir else auto_name
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Lưu file ảnh", default_path, "PNG Files (*.png);;JPEG Files (*.jpg)"
        )
        if file_path:
            pm = self.get_merged_pixmap()
            quality = self.config_data.get("image_quality", 95) if hasattr(self, "config_data") and isinstance(self.config_data, dict) else 95
            if file_path.lower().endswith((".jpg", ".jpeg")):
                pm.save(file_path, "JPEG", quality)
            else:
                pm.save(file_path)
