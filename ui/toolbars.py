from PyQt6.QtCore import Qt, QPoint, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPixmap, QPolygonF, QIcon, QPainterPath
from PyQt6.QtWidgets import QWidget, QLabel

# --- Custom High-Definition Vector Icon Generators (Crisp Charcoal #1C1C1E) ---

def create_rect_icon(size: int = 24) -> QIcon:
    """Tạo Icon Khung Chữ Nhật Vector sắc nét, chuẩn thiết kế hiện đại."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.scale(size / 24.0, size / 24.0)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    pen = QPen(QColor(28, 28, 30), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawRoundedRect(QRectF(3.5, 4.5, 13, 11), 2.5, 2.5)

    painter.end()
    return QIcon(pm)

def create_pencil_icon(size: int = 24) -> QIcon:
    """Tạo Icon Bút Vẽ Vector sắc nét, độ chi tiết cao."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.scale(size / 24.0, size / 24.0)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    pen = QPen(QColor(28, 28, 30), 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(QBrush(QColor(28, 28, 30)))

    path = QPainterPath()
    path.moveTo(QPointF(5, 16))
    path.lineTo(QPointF(7.5, 7.5))
    path.lineTo(QPointF(14.5, 14.5))
    path.closeSubpath()
    painter.drawPath(path)

    nib = QPolygonF([QPointF(5, 16), QPointF(3, 18), QPointF(7, 17)])
    painter.drawPolygon(nib)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(60, 60, 67)))
    poly = QPolygonF([QPointF(17.5, 15), QPointF(22, 15), QPointF(19.75, 18.5)])
    painter.drawPolygon(poly)

    painter.end()
    return QIcon(pm)

def create_pointer_icon(size: int = 24) -> QIcon:
    """Tạo Icon Con Trỏ Chuột Vector sắc nét theo chuẩn macOS Cursor."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.scale(size / 24.0, size / 24.0)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    painter.setPen(QPen(QColor(28, 28, 30), 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(QBrush(QColor(28, 28, 30)))

    poly = QPolygonF([
        QPointF(5.5, 3.5),
        QPointF(5.5, 17.5),
        QPointF(9.5, 13.5),
        QPointF(12.5, 19),
        QPointF(14.8, 17.8),
        QPointF(11.8, 12.5),
        QPointF(17, 12.5)
    ])
    painter.drawPolygon(poly)

    painter.end()
    return QIcon(pm)

def create_mosaic_icon(size: int = 24) -> QIcon:
    """Tạo Icon Làm Mờ Mosaic Grid sắc nét."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.scale(size / 24.0, size / 24.0)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

    s = 3
    start_x, start_y = 4, 4.5
    painter.setPen(Qt.PenStyle.NoPen)
    for row in range(4):
        for col in range(4):
            if (row + col) % 2 == 0:
                painter.setBrush(QBrush(QColor(28, 28, 30)))
            else:
                painter.setBrush(QBrush(QColor(160, 160, 170)))
            painter.drawRect(int(start_x + col * s), int(start_y + row * s), s, s)

    # Indicator tam giác nhỏ góc dưới phải
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setBrush(QBrush(QColor(60, 60, 67)))
    poly = QPolygonF([QPointF(17.5, 15), QPointF(22, 15), QPointF(19.75, 18.5)])
    painter.drawPolygon(poly)

    painter.end()
    return QIcon(pm)

def create_blackout_icon(size: int = 24) -> QIcon:
    """Tạo Icon Tô Đen Redact (Blackout) sắc nét."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.scale(size / 24.0, size / 24.0)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(28, 28, 30)))
    painter.drawRoundedRect(QRectF(3.5, 7.5, 17, 9), 2.5, 2.5)

    painter.end()
    return QIcon(pm)

def create_watermark_icon(size: int = 24) -> QIcon:
    """Tạo Icon Watermark Stamp gọn gàng."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pm)
    painter.scale(size / 24.0, size / 24.0)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    pen = QPen(QColor(28, 28, 30), 1.6)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(QRectF(3.5, 3.5, 17, 17))

    painter.setPen(QPen(QColor(28, 28, 30)))
    font = QFont("Segoe UI", 9, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(QRectF(3.5, 3.5, 17, 17), Qt.AlignmentFlag.AlignCenter, "W")

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


class DragGripWidget(QWidget):
    """Drag Handle Grip thanh lịch với các chấm vector tròn bo góc mịn màng chuẩn Figma/Apple."""
    def __init__(self, vertical: bool = False, parent=None):
        super().__init__(parent)
        self.vertical = vertical
        self.setCursor(Qt.CursorShape.SizeAllCursor)
        self.setToolTip("Kéo để di chuyển thanh công cụ")
        if vertical:
            self.setFixedHeight(12)
            self.setMinimumWidth(24)
        else:
            self.setFixedWidth(12)
            self.setMinimumHeight(24)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#A1A1AA")))

        w, h = self.width(), self.height()
        r = 1.6
        if self.vertical:
            cx = w / 2.0
            cy = h / 2.0
            for dx in (-5.5, 0.0, 5.5):
                for dy in (-2.2, 2.2):
                    painter.drawEllipse(QPointF(cx + dx, cy + dy), r, r)
        else:
            cx = w / 2.0
            cy = h / 2.0
            for dx in (-2.2, 2.2):
                for dy in (-5.5, 0.0, 5.5):
                    painter.drawEllipse(QPointF(cx + dx, cy + dy), r, r)

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


# QSS Stylesheets - Clean, Modern Fluent Light Mode (10px radius, refined border, compact buttons)
common_toolbar_style = """
    QToolTip {
        background-color: #18181B;
        color: #FFFFFF;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 6px;
        padding: 5px 9px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 11px;
        font-weight: 500;
    }
    DraggableToolbarPanel, QWidget#toolbarPanel {
        background-color: #FFFFFF;
        border: 1px solid rgba(0, 0, 0, 0.10);
        border-radius: 10px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: #18181B;
    }
    QMenu {
        background-color: #FFFFFF;
        color: #18181B;
        border: 1px solid rgba(0, 0, 0, 0.10);
        border-radius: 10px;
        padding: 5px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 12px;
        font-weight: 500;
    }
    QMenu::item {
        padding: 6px 14px;
        margin: 1px 3px;
        border-radius: 6px;
        color: #27272A;
        min-height: 22px;
    }
    QMenu::item:hover {
        background-color: #F4F4F5;
        color: #18181B;
    }
    QMenu::item:selected {
        background-color: #EFF6FF;
        color: #2563EB;
        font-weight: 600;
    }
    QMenu::separator {
        height: 1px;
        background-color: rgba(0, 0, 0, 0.08);
        margin: 4px 6px;
    }
    QToolButton, QPushButton {
        background-color: transparent;
        color: #3F3F46;
        border: none;
        border-radius: 6px;
        padding: 2px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-weight: 600;
        font-size: 13px;
    }
    QToolButton:hover, QPushButton:hover {
        background-color: #F4F4F5;
        color: #18181B;
    }
    QToolButton:checked {
        background-color: #EFF6FF;
        border: 1px solid #BFDBFE;
        color: #2563EB;
        border-radius: 6px;
    }
    QToolButton::menu-indicator {
        image: none;
    }
    QToolButton#cancelBtn:hover, QPushButton#cancelBtn:hover {
        background-color: #FEE2E2;
        color: #DC2626;
        border-radius: 6px;
    }
    QToolButton#zaloCopyBtn, QPushButton#zaloCopyBtn {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #2563EB, stop:1 #1D4ED8);
        border: 1px solid rgba(0, 0, 0, 0.05);
        color: #FFFFFF;
        border-radius: 6px;
        font-weight: bold;
        font-size: 13px;
    }
    QToolButton#zaloCopyBtn:hover, QPushButton#zaloCopyBtn:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #3B82F6, stop:1 #2563EB);
    }
"""

word_toolbar_style = """
    DraggableToolbarPanel, QWidget#wordSubToolbarPanel, QWidget#wordSubToolbar {
        background-color: #FFFFFF;
        border: 1px solid rgba(0, 0, 0, 0.10);
        border-radius: 10px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #18181B;
    }
    QComboBox#fontFamilyCombo {
        background-color: #FAFAFA;
        color: #18181B;
        border: 1px solid rgba(0, 0, 0, 0.12);
        border-radius: 6px;
        padding: 0px 18px 0px 8px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 12px;
        font-weight: 500;
        min-width: 100px;
        max-width: 110px;
        min-height: 29px;
        max-height: 29px;
    }
    QComboBox#fontFamilyCombo:hover {
        border: 1px solid #2563EB;
        background-color: #FFFFFF;
    }
    QComboBox#fontFamilyCombo:focus {
        border: 1.5px solid #2563EB;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: center right;
        width: 18px;
        border-left: none;
    }
    QComboBox::down-arrow {
        image: none;
        border: none;
    }
    QComboBox QAbstractItemView {
        background-color: #FFFFFF;
        color: #18181B;
        border: 1px solid rgba(0, 0, 0, 0.10);
        border-radius: 8px;
        padding: 4px;
        selection-background-color: #EFF6FF;
        selection-color: #2563EB;
        font-size: 12px;
        font-weight: 500;
        outline: none;
    }
    QSpinBox#fontSizeSpin {
        background-color: #FAFAFA;
        color: #18181B;
        border: 1px solid rgba(0, 0, 0, 0.12);
        border-radius: 6px;
        padding-left: 6px;
        padding-right: 20px;
        font-size: 12px;
        font-weight: 600;
        min-width: 54px;
        max-width: 60px;
        min-height: 32px;
        max-height: 32px;
    }
    QSpinBox#fontSizeSpin:hover {
        border: 1px solid #2563EB;
        background-color: #FFFFFF;
    }
    QSpinBox#fontSizeSpin:focus {
        border: 1.5px solid #2563EB;
    }
    QSpinBox#fontSizeSpin::up-button, QSpinBox#fontSizeSpin::down-button {
        subcontrol-origin: border;
        width: 16px;
        background-color: #F4F4F5;
        border-left: 1px solid rgba(0, 0, 0, 0.12);
    }
    QSpinBox#fontSizeSpin::up-button:hover, QSpinBox#fontSizeSpin::down-button:hover {
        background-color: #E4E4E7;
    }
    QSpinBox#fontSizeSpin::up-button {
        subcontrol-position: top right;
        border-top-right-radius: 5px;
    }
    QSpinBox#fontSizeSpin::down-button {
        subcontrol-position: bottom right;
        border-bottom-right-radius: 5px;
        background-color: transparent;
        color: #52525B;
        border: 1px solid rgba(0, 0, 0, 0.10);
        border-right: none;
        border-radius: 0px;
        border-top-left-radius: 6px;
        border-bottom-left-radius: 6px;
        padding: 0px;
        font-size: 11px;
        font-weight: 700;
        min-width: 26px;
        max-width: 26px;
        min-height: 32px;
        max-height: 32px;
    }
    QToolButton#segBtnMid {
        background-color: transparent;
        color: #52525B;
        border: 1px solid rgba(0, 0, 0, 0.10);
        border-left: none;
        border-right: none;
        border-radius: 0px;
        padding: 0px;
        font-size: 11px;
        font-weight: 700;
        min-width: 26px;
        max-width: 26px;
        min-height: 32px;
        max-height: 32px;
    }
    QToolButton#segBtnRight {
        background-color: transparent;
        color: #52525B;
        border: 1px solid rgba(0, 0, 0, 0.10);
        border-left: none;
        border-radius: 0px;
        border-top-right-radius: 6px;
        border-bottom-right-radius: 6px;
        padding: 0px;
        font-size: 11px;
        font-weight: 700;
        min-width: 26px;
        max-width: 26px;
        min-height: 32px;
        max-height: 32px;
    }
    QToolButton#segBtnLeft:hover, QToolButton#segBtnMid:hover, QToolButton#segBtnRight:hover {
        background-color: #F4F4F5;
        color: #18181B;
    }
    QToolButton#segBtnLeft:checked, QToolButton#segBtnMid:checked, QToolButton#segBtnRight:checked {
        background-color: #E6F1FB;
        color: #185FA5;
        border-color: #BFDBFE;
    }
    QComboBox#textBgCombo {
        background-color: #FAFAFA;
        color: #27272A;
        border: 1px solid rgba(0, 0, 0, 0.10);
        border-radius: 6px;
        padding: 0px 18px 0px 8px;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
        font-size: 12px;
        font-weight: 500;
        min-width: 90px;
        max-width: 115px;
        min-height: 29px;
        max-height: 29px;
    }
    QComboBox#textBgCombo:hover {
        border: 1px solid rgba(0, 0, 0, 0.20);
        background-color: #FFFFFF;
    }
    QComboBox#textBgCombo QAbstractItemView {
        background-color: #FFFFFF;
        color: #27272A;
        border: 1px solid rgba(0, 0, 0, 0.10);
        border-radius: 6px;
        padding: 3px;
        selection-background-color: #DBEAFE;
        selection-color: #1D4ED8;
        font-size: 12px;
        outline: none;
    }
    QToolButton#wordFormatBtn {
        background-color: #FAFAFA;
        color: #3F3F46;
        border: 1px solid rgba(0, 0, 0, 0.10);
        border-radius: 6px;
        padding: 2px 6px;
        font-size: 11px;
        font-weight: 700;
        min-width: 24px;
        min-height: 32px;
        max-height: 32px;
    }
    QToolButton#wordFormatBtn:hover {
        border: 1px solid rgba(0, 0, 0, 0.20);
        background-color: #FFFFFF;
        color: #2563EB;
    }
    QToolButton#wordFormatBtn:checked {
        background-color: #E6F1FB;
        border: 1px solid #BFDBFE;
        color: #185FA5;
    }
"""
