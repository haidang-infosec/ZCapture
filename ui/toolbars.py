from PyQt6.QtCore import Qt, QPoint, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPixmap, QPolygonF, QIcon, QPainterPath
from PyQt6.QtWidgets import QWidget

# --- Custom High-Definition Vector Icon Generators (Crisp Dark Charcoal #1C1C1E) ---

def create_rect_icon() -> QIcon:
    """Tạo Icon Khung Chữ Nhật Vector 42x42px Nét Sắc Đẳng Cấp."""
    pm = QPixmap(42, 42)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    pen = QPen(QColor(28, 28, 30), 2.2)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(QRectF(7, 11, 20, 16), 3, 3)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(28, 28, 30)))
    poly = QPolygonF([QPointF(29, 21), QPointF(35, 21), QPointF(32, 25)])
    painter.drawPolygon(poly)

    painter.end()
    return QIcon(pm)

def create_pencil_icon() -> QIcon:
    """Tạo Icon Bút Vẽ Vector 42x42px Nét Sắc Đẳng Cấp."""
    pm = QPixmap(42, 42)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    pen = QPen(QColor(28, 28, 30), 2)
    painter.setPen(pen)
    painter.setBrush(QBrush(QColor(28, 28, 30)))

    path = QPainterPath()
    path.moveTo(QPointF(8, 25))
    path.lineTo(QPointF(11, 14))
    path.lineTo(QPointF(21, 24))
    path.closeSubpath()
    painter.drawPath(path)

    nib = QPolygonF([QPointF(8, 25), QPointF(5, 28), QPointF(11, 27)])
    painter.drawPolygon(nib)

    painter.setPen(Qt.PenStyle.NoPen)
    poly = QPolygonF([QPointF(29, 21), QPointF(35, 21), QPointF(32, 25)])
    painter.drawPolygon(poly)

    painter.end()
    return QIcon(pm)

def create_pointer_icon() -> QIcon:
    """Tạo Icon Con Trỏ Chuột Vector 42x42px."""
    pm = QPixmap(42, 42)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    painter.setPen(QPen(QColor(28, 28, 30), 1.5))
    painter.setBrush(QBrush(QColor(28, 28, 30)))

    poly = QPolygonF([
        QPointF(11, 9),
        QPointF(11, 29),
        QPointF(16, 24),
        QPointF(20, 31),
        QPointF(24, 29),
        QPointF(20, 22),
        QPointF(27, 22)
    ])
    painter.drawPolygon(poly)

    painter.end()
    return QIcon(pm)

def create_mosaic_icon() -> QIcon:
    """Tạo Icon Làm Mờ Mosaic Grid 42x42px."""
    pm = QPixmap(42, 42)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    s = 4
    start_x, start_y = 11, 11
    painter.setPen(Qt.PenStyle.NoPen)
    for row in range(5):
        for col in range(5):
            if (row + col) % 2 == 0:
                painter.setBrush(QBrush(QColor(28, 28, 30)))
            else:
                painter.setBrush(QBrush(QColor(160, 160, 170)))
            painter.drawRect(start_x + col * s, start_y + row * s, s, s)

    painter.end()
    return QIcon(pm)

def create_blackout_icon() -> QIcon:
    """Tạo Icon Tô Đen Redact (Blackout) 42x42px."""
    pm = QPixmap(42, 42)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(28, 28, 30)))
    painter.drawRoundedRect(9, 15, 24, 12, 2, 2)

    painter.end()
    return QIcon(pm)

def create_watermark_icon() -> QIcon:
    """Tạo Icon Watermark Stamp HD 42x42px Sang Trọng."""
    pm = QPixmap(42, 42)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    pen = QPen(QColor(28, 28, 30), 2.2)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(QRectF(8, 7, 26, 26))

    painter.setPen(QPen(QColor(28, 28, 30)))
    font = QFont("Segoe UI", 11, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(QRectF(8, 7, 26, 26), Qt.AlignmentFlag.AlignCenter, "W")

    painter.end()
    return QIcon(pm)


# --- Tray Menu Row Icons (16x16, dùng cho QLabel trong menu tray light theme) ---

def create_camera_icon(size=16, color="#52525B") -> QIcon:
    """Tạo Icon Camera Vector cho mục 'Capture Screen' trong Tray Menu."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor(color), 1.3))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawRoundedRect(QRectF(1, size * 0.32, size - 2, size * 0.56), 2, 2)
    p.drawRect(QRectF(size * 0.36, size * 0.16, size * 0.28, size * 0.18))
    p.drawEllipse(QRectF(size * 0.30, size * 0.42, size * 0.4, size * 0.4))
    p.end()
    return QIcon(pm)


def create_settings_icon(size=16, color="#52525B") -> QIcon:
    """Tạo Icon Sliders (thanh trượt cấu hình) cho mục 'Settings' trong Tray Menu."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor(color), 1.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    rows = [(size * 0.28, size * 0.62), (size * 0.5, size * 0.38), (size * 0.72, size * 0.55)]
    for y, knob_x in rows:
        p.drawLine(QPointF(size * 0.12, y), QPointF(size * 0.88, y))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(QColor(color)))
    for y, knob_x in rows:
        p.drawEllipse(QPointF(knob_x, y), 1.8, 1.8)
    p.end()
    return QIcon(pm)


def create_info_icon(size=16, color="#52525B") -> QIcon:
    """Tạo Icon Info tròn (i) cho mục 'About ZCapture' trong Tray Menu."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor(color), 1.3))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(1, 1, size - 2, size - 2))
    font = QFont("Georgia", int(size * 0.5), QFont.Weight.Bold)
    font.setItalic(True)
    p.setFont(font)
    p.setPen(QPen(QColor(color)))
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "i")
    p.end()
    return QIcon(pm)


def create_power_icon(size=16, color="#DC2626") -> QIcon:
    """Tạo Icon Power/Logout cho mục 'Exit ZCapture' trong Tray Menu (màu cảnh báo đỏ)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setPen(QPen(QColor(color), 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    p.setBrush(Qt.BrushStyle.NoBrush)
    rect = QRectF(size * 0.22, size * 0.22, size * 0.56, size * 0.56)
    p.drawArc(rect, 50 * 16, 260 * 16)
    p.drawLine(QPointF(size / 2, size * 0.12), QPointF(size / 2, size * 0.5))
    p.end()
    return QIcon(pm)


from PyQt6.QtWidgets import QLabel


class DragGripWidget(QLabel):
    """Drag Handle Grip icon giúp người dùng nhận diện và kéo di chuyển thanh menu tùy ý."""
    def __init__(self, vertical: bool = False, parent=None):
        super().__init__(parent)
        self.vertical = vertical
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if vertical:
            self.setFixedHeight(12)
            self.setText("···")
            self.setStyleSheet("color: #A1A1AA; font-size: 13px; font-weight: bold; background: transparent; padding: 0px;")
            self.setToolTip("Kéo để di chuyển thanh công cụ")
        else:
            self.setFixedWidth(12)
            self.setText("⋮")
            self.setStyleSheet("color: #A1A1AA; font-size: 13px; font-weight: bold; background: transparent; padding: 0px;")
            self.setToolTip("Kéo để di chuyển thanh công cụ")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.parent():
            p = self.mapTo(self.parent(), event.position().toPoint())
            self.parent().drag_start_pos = p
            self.parent()._is_dragging = True
            self.parent().is_user_moved = True
            self.parent().raise_()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.parent() and getattr(self.parent(), "_is_dragging", False):
            parent_container = self.parent().parent()
            if parent_container:
                parent_mouse = parent_container.mapFromGlobal(event.globalPosition().toPoint())
                new_x = parent_mouse.x() - self.parent().drag_start_pos.x()
                new_y = parent_mouse.y() - self.parent().drag_start_pos.y()
                pw, ph = parent_container.width(), parent_container.height()
                w, h = self.parent().width(), self.parent().height()
                cx = max(0, min(pw - w, new_x))
                cy = max(0, min(ph - h, new_y))
                self.parent().move(cx, cy)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.parent():
            self.parent()._is_dragging = False
        event.accept()


class DraggableToolbarPanel(QWidget):
    """Thanh Menu Panel Cho Phép Kéo Thả Di Chuyển Vị Trí Tự Do Trên Màn Hình."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.drag_start_pos = QPoint()
        self._is_dragging = False
        self.is_user_moved = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_pos = event.position().toPoint()
            self._is_dragging = True
            self.is_user_moved = True
            self.raise_()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton and self._is_dragging:
            if self.parent():
                parent_mouse = self.parent().mapFromGlobal(event.globalPosition().toPoint())
                new_x = parent_mouse.x() - self.drag_start_pos.x()
                new_y = parent_mouse.y() - self.drag_start_pos.y()
                pw, ph = self.parent().width(), self.parent().height()
                w, h = self.width(), self.height()
                cx = max(0, min(pw - w, new_x))
                cy = max(0, min(ph - h, new_y))
                self.move(cx, cy)
            else:
                self.move(event.globalPosition().toPoint() - self.drag_start_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)


# QSS Stylesheets - CleanShot X Light Mode (Strict User Prompt Spec: rgba(255,255,255,0.88), 16px radius, #3F3F46 text, #E6F1FB active fill, #185FA5 icon)
common_toolbar_style = """
    QToolTip {
        background-color: #FFFFFF;
        color: #3F3F46;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 8px;
        padding: 5px 10px;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", sans-serif;
        font-size: 12px;
        font-weight: 600;
    }
    DraggableToolbarPanel, QWidget#toolbarPanel {
        background-color: rgba(255, 255, 255, 0.88);
        border: 1px solid rgba(0, 0, 0, 0.06);
        border-radius: 16px;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
        color: #3F3F46;
    }
    QMenu {
        background-color: #FFFFFF;
        color: #27272A;
        border: 1px solid rgba(0, 0, 0, 0.06);
        border-radius: 12px;
        padding: 6px;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
        font-size: 14px;
        font-weight: 400;
    }
    QMenu::item {
        padding: 8px 16px 8px 12px;
        margin: 2px 4px;
        border-radius: 8px;
        color: #27272A;
        min-height: 24px;
    }
    QMenu::item:hover {
        background-color: #F4F4F5;
        color: #27272A;
    }
    QMenu::item:selected {
        background-color: #DBEAFE;
        color: #1D4ED8;
        font-weight: 500;
    }
    QMenu::separator {
        height: 1px;
        background-color: rgba(0, 0, 0, 0.06);
        margin: 4px 8px;
    }
    QToolButton, QPushButton {
        background-color: transparent;
        color: #3F3F46;
        border: none;
        border-radius: 10px;
        padding: 4px;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI Symbol", sans-serif;
        font-weight: 600;
        font-size: 17px;
    }
    QToolButton:hover, QPushButton:hover {
        background-color: #F4F4F5;
        color: #18181B;
    }
    QToolButton:checked {
        background-color: #E6F1FB;
        border: none;
        color: #185FA5;
        border-radius: 10px;
    }
    QToolButton::menu-indicator {
        image: none;
    }
    QToolButton#cancelBtn:hover, QPushButton#cancelBtn:hover {
        background-color: #FEE2E2;
        color: #DC2626;
        border-radius: 18px;
    }
    QToolButton#zaloCopyBtn, QPushButton#zaloCopyBtn {
        background: #2563EB;
        border: none;
        color: #FFFFFF;
        border-radius: 18px;
        font-weight: bold;
        font-size: 18px;
    }
    QToolButton#zaloCopyBtn:hover, QPushButton#zaloCopyBtn:hover {
        background: #1D4ED8;
    }
"""

word_toolbar_style = """
    DraggableToolbarPanel, QWidget#wordSubToolbarPanel {
        background-color: #FFFFFF;
        border: 1px solid rgba(0, 0, 0, 0.06);
        border-radius: 12px;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
        color: #3F3F46;
    }
    QComboBox#fontFamilyCombo {
        background-color: #FAFAFA;
        color: #27272A;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 8px;
        padding: 0px 22px 0px 10px;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
        font-size: 13px;
        font-weight: 500;
        min-width: 120px;
        max-width: 130px;
        min-height: 30px;
        max-height: 32px;
    }
    QComboBox#fontFamilyCombo:hover {
        border: 1px solid rgba(0, 0, 0, 0.16);
        background-color: #FFFFFF;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: center right;
        width: 20px;
        border-left: none;
    }
    QComboBox::down-arrow {
        image: none;
        border: none;
    }
    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        color: #27272A;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 8px;
        padding: 4px;
        selection-background-color: #DBEAFE;
        selection-color: #1D4ED8;
        font-size: 13px;
        font-weight: 500;
        outline: none;
    }
    QSpinBox#fontSizeSpin {
        background-color: #FAFAFA;
        color: #27272A;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 8px;
        padding: 0px 4px;
        font-size: 13px;
        font-weight: 500;
        min-width: 44px;
        max-width: 56px;
        min-height: 30px;
        max-height: 32px;
    }
    QSpinBox#fontSizeSpin:hover {
        border: 1px solid rgba(0, 0, 0, 0.16);
        background-color: #FFFFFF;
    }
    QSpinBox#fontSizeSpin::up-button, QSpinBox#fontSizeSpin::down-button {
        width: 14px;
        border: none;
        background: transparent;
    }
    QToolButton#segBtnLeft {
        background-color: transparent;
        color: #52525B;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-right: none;
        border-radius: 0px;
        border-top-left-radius: 8px;
        border-bottom-left-radius: 8px;
        padding: 0px;
        font-size: 13px;
        font-weight: 700;
        min-width: 30px;
        max-width: 32px;
        min-height: 30px;
        max-height: 32px;
    }
    QToolButton#segBtnMid {
        background-color: transparent;
        color: #52525B;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-left: none;
        border-right: none;
        border-radius: 0px;
        padding: 0px;
        font-size: 13px;
        font-weight: 700;
        min-width: 30px;
        max-width: 32px;
        min-height: 30px;
        max-height: 32px;
    }
    QToolButton#segBtnRight {
        background-color: transparent;
        color: #52525B;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-left: none;
        border-radius: 0px;
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
        padding: 0px;
        font-size: 13px;
        font-weight: 700;
        min-width: 30px;
        max-width: 32px;
        min-height: 30px;
        max-height: 32px;
    }
    QToolButton#segBtnLeft:hover, QToolButton#segBtnMid:hover, QToolButton#segBtnRight:hover {
        background-color: #F4F4F5;
    }
    QToolButton#segBtnLeft:checked, QToolButton#segBtnMid:checked, QToolButton#segBtnRight:checked {
        background-color: #DBEAFE;
        color: #2563EB;
        font-weight: 600;
    }
    QComboBox#textBgCombo {
        background-color: #FAFAFA;
        color: #27272A;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 8px;
        padding: 0px 22px 0px 8px;
        font-size: 13px;
        font-weight: 500;
        min-height: 30px;
        max-height: 32px;
    }
    QComboBox#textBgCombo:hover {
        border: 1px solid rgba(0, 0, 0, 0.16);
        background-color: #FFFFFF;
    }
    QToolButton#wordFormatBtn {
        background-color: #FAFAFA;
        color: #3F3F46;
        border: 1px solid rgba(0, 0, 0, 0.08);
        border-radius: 8px;
        padding: 4px 8px;
        font-size: 13px;
        font-weight: 700;
        min-width: 28px;
        min-height: 30px;
        max-height: 32px;
    }
    QToolButton#wordFormatBtn:hover {
        border: 1px solid rgba(0, 0, 0, 0.16);
        background-color: #FFFFFF;
        color: #2563EB;
    }
    QToolButton#wordFormatBtn:checked {
        background-color: #DBEAFE;
        border: 1px solid rgba(37, 99, 235, 0.3);
        color: #2563EB;
    }
"""
