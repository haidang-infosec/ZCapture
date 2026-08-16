"""
Thư viện widget & icon dùng chung cho SettingsWindow (và các dialog khác nếu cần):
- make_icon_pixmap / make_icon: icon vector 16-18px vẽ tay bằng QPainter (không cần asset ngoài).
- make_card: card thay thế QGroupBox (bo góc 12, shadow nhẹ, header icon + label, không kẻ ngang dài).
- StyledCheckBox: checkbox tuỳ biến 18px vẽ tay — tự vẽ text nên KHÔNG bị Qt nuốt ký tự "&" như
  QCheckBox gốc (Qt coi "&" trong text QCheckBox/QPushButton/QGroupBox là ký tự mnemonic).
- ColorPickerRow: swatch tròn + label + ô nhập hex, thay cho các nút chọn màu to-nguyên-hàng cũ.
- RecordingKeySequenceEdit: QKeySequenceEdit phát tín hiệu khi bắt đầu/kết thúc ghi phím.
"""
from PyQt6.QtCore import Qt, QRectF, QPointF, QSize, pyqtSignal
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPixmap, QIcon, QPainterPath, QPolygonF
)
from PyQt6.QtWidgets import (
    QWidget, QCheckBox, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QColorDialog, QKeySequenceEdit, QGraphicsDropShadowEffect
)


def make_icon_pixmap(kind: str, size: int = 16, color: str = "#2563EB") -> QPixmap:
    """Vẽ icon vector đơn giản 1 màu theo `kind`. Trả về QPixmap trong suốt size x size."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    c = QColor(color)
    s = size

    if kind == "home":
        p.setPen(QPen(c, 1.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(s * 0.12, s * 0.5)
        path.lineTo(s * 0.5, s * 0.14)
        path.lineTo(s * 0.88, s * 0.5)
        p.drawPath(path)
        p.drawRect(QRectF(s * 0.24, s * 0.5, s * 0.52, s * 0.36))

    elif kind == "keyboard":
        p.setPen(QPen(c, 1.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(0.5, s * 0.16, s - 1, s * 0.68), 2, 2)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(c))
        key_h = s * 0.12
        key_y = s * 0.16 + (s * 0.68 - key_h) / 2
        for i, x in enumerate([s * 0.18, s * 0.34, s * 0.5, s * 0.66, s * 0.82]):
            w = key_h * (2.2 if i == 2 else 1)
            p.drawRoundedRect(QRectF(x - w / 2, key_y, w, key_h), 1, 1)

    elif kind == "brush":
        p.setPen(QPen(c, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawLine(QPointF(s * 0.8, s * 0.16), QPointF(s * 0.48, s * 0.48))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(c))
        tip = QPolygonF([
            QPointF(s * 0.52, s * 0.42), QPointF(s * 0.64, s * 0.54),
            QPointF(s * 0.34, s * 0.84), QPointF(s * 0.2, s * 0.7)
        ])
        p.drawPolygon(tip)

    elif kind == "droplet":
        p.setPen(QPen(c, 1.3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(s * 0.5, s * 0.1)
        path.cubicTo(s * 0.85, s * 0.5, s * 0.78, s * 0.9, s * 0.5, s * 0.9)
        path.cubicTo(s * 0.22, s * 0.9, s * 0.15, s * 0.5, s * 0.5, s * 0.1)
        p.drawPath(path)

    elif kind == "folder":
        p.setPen(QPen(c, 1.3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(s * 0.12, s * 0.3)
        path.lineTo(s * 0.4, s * 0.3)
        path.lineTo(s * 0.48, s * 0.4)
        path.lineTo(s * 0.88, s * 0.4)
        path.lineTo(s * 0.88, s * 0.8)
        path.lineTo(s * 0.12, s * 0.8)
        path.closeSubpath()
        p.drawPath(path)

    elif kind == "monitor":
        p.setPen(QPen(c, 1.3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(s * 0.08, s * 0.14, s * 0.84, s * 0.58), 2, 2)
        p.drawLine(QPointF(s * 0.5, s * 0.72), QPointF(s * 0.5, s * 0.86))
        p.drawLine(QPointF(s * 0.32, s * 0.86), QPointF(s * 0.68, s * 0.86))

    elif kind == "settings2":
        p.setPen(QPen(c, 1.3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        for cx, cy, r in [(s * 0.32, s * 0.32, s * 0.14), (s * 0.68, s * 0.68, s * 0.14)]:
            p.drawEllipse(QPointF(cx, cy), r, r)
        p.drawLine(QPointF(s * 0.46, s * 0.32), QPointF(s * 0.9, s * 0.32))
        p.drawLine(QPointF(s * 0.1, s * 0.32), QPointF(s * 0.18, s * 0.32))
        p.drawLine(QPointF(s * 0.82, s * 0.68), QPointF(s * 0.9, s * 0.68))
        p.drawLine(QPointF(s * 0.1, s * 0.68), QPointF(s * 0.54, s * 0.68))

    elif kind == "bell":
        p.setPen(QPen(c, 1.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(s * 0.28, s * 0.62)
        path.cubicTo(s * 0.28, s * 0.32, s * 0.34, s * 0.16, s * 0.5, s * 0.16)
        path.cubicTo(s * 0.66, s * 0.16, s * 0.72, s * 0.32, s * 0.72, s * 0.62)
        path.lineTo(s * 0.82, s * 0.72)
        path.lineTo(s * 0.18, s * 0.72)
        path.closeSubpath()
        p.drawPath(path)
        p.drawArc(QRectF(s * 0.4, s * 0.72, s * 0.2, s * 0.16), 180 * 16, -180 * 16)

    elif kind == "info":
        p.setPen(QPen(c, 1.3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(1, 1, s - 2, s - 2))
        font = QFont("Georgia", max(6, int(s * 0.5)), QFont.Weight.Bold)
        font.setItalic(True)
        p.setFont(font)
        p.setPen(QPen(c))
        p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "i")

    elif kind == "sliders":
        p.setPen(QPen(c, 1.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        rows = [(s * 0.28, s * 0.62), (s * 0.5, s * 0.38), (s * 0.72, s * 0.55)]
        for y, _ in rows:
            p.drawLine(QPointF(s * 0.12, y), QPointF(s * 0.88, y))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(c))
        for y, knob_x in rows:
            p.drawEllipse(QPointF(knob_x, y), 1.8, 1.8)

    elif kind == "palette":
        p.setPen(QPen(c, 1.3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(s * 0.08, s * 0.14, s * 0.84, s * 0.72))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(c))
        for cx, cy in [(s * 0.32, s * 0.36), (s * 0.55, s * 0.28), (s * 0.72, s * 0.46), (s * 0.42, s * 0.58)]:
            p.drawEllipse(QPointF(cx, cy), s * 0.06, s * 0.06)

    elif kind == "badge-number":
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(c))
        p.drawEllipse(QRectF(1, 1, s - 2, s - 2))
        p.setPen(QPen(QColor("#FFFFFF")))
        font = QFont("Segoe UI", max(6, int(s * 0.5)), QFont.Weight.Bold)
        p.setFont(font)
        p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "1")

    elif kind == "image":
        p.setPen(QPen(c, 1.3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(1, s * 0.2, s - 2, s * 0.6), 2, 2)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(c))
        p.drawEllipse(QPointF(s * 0.32, s * 0.4), s * 0.07, s * 0.07)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(c, 1.2))
        path = QPainterPath()
        path.moveTo(s * 0.12, s * 0.72)
        path.lineTo(s * 0.4, s * 0.46)
        path.lineTo(s * 0.62, s * 0.64)
        path.lineTo(s * 0.78, s * 0.5)
        path.lineTo(s * 0.9, s * 0.62)
        p.drawPath(path)

    elif kind == "clock":
        p.setPen(QPen(c, 1.3))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(1, 1, s - 2, s - 2))
        p.drawLine(QPointF(s * 0.5, s * 0.5), QPointF(s * 0.5, s * 0.26))
        p.drawLine(QPointF(s * 0.5, s * 0.5), QPointF(s * 0.68, s * 0.6))

    elif kind == "tag":
        p.setPen(QPen(c, 1.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(s * 0.12, s * 0.12)
        path.lineTo(s * 0.55, s * 0.12)
        path.lineTo(s * 0.9, s * 0.47)
        path.lineTo(s * 0.47, s * 0.9)
        path.lineTo(s * 0.12, s * 0.55)
        path.closeSubpath()
        p.drawPath(path)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(c))
        p.drawEllipse(QPointF(s * 0.3, s * 0.3), s * 0.07, s * 0.07)

    elif kind == "cursor":
        p.setPen(QPen(c, 1.2))
        p.setBrush(QBrush(c))
        poly = QPolygonF([
            QPointF(s * 0.2, s * 0.12), QPointF(s * 0.2, s * 0.78),
            QPointF(s * 0.38, s * 0.62), QPointF(s * 0.5, s * 0.86),
            QPointF(s * 0.62, s * 0.8), QPointF(s * 0.48, s * 0.56),
            QPointF(s * 0.72, s * 0.56)
        ])
        p.drawPolygon(poly)

    elif kind == "refresh":
        p.setPen(QPen(c, 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        rect = QRectF(s * 0.16, s * 0.16, s * 0.68, s * 0.68)
        p.drawArc(rect, 40 * 16, 260 * 16)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(c))
        arrow = QPolygonF([QPointF(s * 0.78, s * 0.14), QPointF(s * 0.92, s * 0.28), QPointF(s * 0.68, s * 0.32)])
        p.drawPolygon(arrow)

    elif kind == "power":
        p.setPen(QPen(c, 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.setBrush(Qt.BrushStyle.NoBrush)
        rect = QRectF(s * 0.22, s * 0.22, s * 0.56, s * 0.56)
        p.drawArc(rect, 50 * 16, 260 * 16)
        p.drawLine(QPointF(s / 2, s * 0.12), QPointF(s / 2, s * 0.5))

    elif kind == "upload":
        p.setPen(QPen(c, 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.drawLine(QPointF(s * 0.5, s * 0.78), QPointF(s * 0.5, s * 0.22))
        p.drawLine(QPointF(s * 0.28, s * 0.44), QPointF(s * 0.5, s * 0.2))
        p.drawLine(QPointF(s * 0.72, s * 0.44), QPointF(s * 0.5, s * 0.2))
        p.drawLine(QPointF(s * 0.18, s * 0.86), QPointF(s * 0.82, s * 0.86))

    elif kind == "shield":
        p.setPen(QPen(c, 1.3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(s * 0.5, s * 0.08)
        path.lineTo(s * 0.86, s * 0.22)
        path.lineTo(s * 0.86, s * 0.5)
        path.cubicTo(s * 0.86, s * 0.74, s * 0.7, s * 0.9, s * 0.5, s * 0.96)
        path.cubicTo(s * 0.3, s * 0.9, s * 0.14, s * 0.74, s * 0.14, s * 0.5)
        path.lineTo(s * 0.14, s * 0.22)
        path.closeSubpath()
        p.drawPath(path)
        check = QPainterPath()
        check.moveTo(s * 0.34, s * 0.5)
        check.lineTo(s * 0.46, s * 0.62)
        check.lineTo(s * 0.68, s * 0.36)
        p.drawPath(check)

    elif kind == "download":
        p.setPen(QPen(c, 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.drawLine(QPointF(s * 0.5, s * 0.18), QPointF(s * 0.5, s * 0.74))
        p.drawLine(QPointF(s * 0.28, s * 0.52), QPointF(s * 0.5, s * 0.76))
        p.drawLine(QPointF(s * 0.72, s * 0.52), QPointF(s * 0.5, s * 0.76))
        p.drawLine(QPointF(s * 0.18, s * 0.86), QPointF(s * 0.82, s * 0.86))

    p.end()
    return pm


def make_icon(kind: str, size: int = 16, color: str = "#2563EB") -> QIcon:
    return QIcon(make_icon_pixmap(kind, size, color))


def make_card(title: str, icon_kind: str = None, icon_color: str = "#2563EB") -> tuple:
    """Card thay thế QGroupBox: nền trắng, bo góc 12, shadow rất nhẹ, header icon 16px + label
    (không dùng gạch ngang dài, chỉ cách 16px). Trả về (card_widget, body_layout)."""
    card = QWidget()
    card.setObjectName("settingsCard")
    card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    card.setStyleSheet("""
        #settingsCard {
            background-color: #FFFFFF;
            border: 1px solid rgba(0,0,0,0.06);
            border-radius: 12px;
        }
    """)
    shadow = QGraphicsDropShadowEffect(card)
    shadow.setBlurRadius(6)
    shadow.setOffset(0, 1)
    shadow.setColor(QColor(0, 0, 0, 10))
    card.setGraphicsEffect(shadow)

    outer = QVBoxLayout(card)
    outer.setContentsMargins(20, 20, 20, 20)
    outer.setSpacing(0)

    header = QHBoxLayout()
    header.setSpacing(8)
    if icon_kind:
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(16, 16)
        icon_lbl.setPixmap(make_icon_pixmap(icon_kind, 16, icon_color))
        header.addWidget(icon_lbl)

    title_lbl = QLabel(title)
    font = QFont()
    font.setPointSize(13)
    font.setWeight(QFont.Weight.Medium)
    font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 0.2)
    title_lbl.setFont(font)
    title_lbl.setStyleSheet("color: #2563EB; background: transparent;")
    header.addWidget(title_lbl)
    header.addStretch()
    outer.addLayout(header)

    outer.addSpacing(16)

    body_layout = QVBoxLayout()
    body_layout.setSpacing(12)
    outer.addLayout(body_layout)

    return card, body_layout


class StyledCheckBox(QCheckBox):
    """Checkbox tuỳ biến 18px, bo góc 5, tick trắng khi chọn (thay checkbox vuông mặc định OS).
    Tự vẽ text bằng QPainter nên không bị Qt nuốt ký tự "&" như QCheckBox gốc."""
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def hitButton(self, pos):
        return self.rect().contains(pos)

    def sizeHint(self):
        fm = self.fontMetrics()
        text_w = fm.horizontalAdvance(self.text())
        return QSize(18 + 8 + text_w + 4, max(24, fm.height() + 8))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        box = 18
        y = (self.height() - box) / 2.0
        rect = QRectF(0, y, box, box)

        if self.isChecked():
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor("#2563EB")))
            painter.drawRoundedRect(rect, 5, 5)

            painter.setPen(QPen(QColor("#FFFFFF"), 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            path = QPainterPath()
            path.moveTo(rect.left() + box * 0.28, rect.top() + box * 0.52)
            path.lineTo(rect.left() + box * 0.42, rect.top() + box * 0.68)
            path.lineTo(rect.left() + box * 0.74, rect.top() + box * 0.32)
            painter.drawPath(path)
        else:
            painter.setPen(QPen(QColor(0, 0, 0, 50), 1.5))
            painter.setBrush(QBrush(QColor("#F4F4F5")))
            painter.drawRoundedRect(rect, 5, 5)

        painter.setPen(QPen(QColor("#3F3F46")))
        painter.setFont(self.font())
        text_rect = QRectF(box + 8, 0, self.width() - box - 8, self.height())
        painter.drawText(text_rect, int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft), self.text())


class ColorPickerRow(QWidget):
    """Hàng chọn màu chuẩn hoá: swatch tròn 32px + label + ô nhập mã hex.
    Click swatch mở QColorDialog; gõ hex trực tiếp cũng cập nhật màu."""
    colorChanged = pyqtSignal(QColor)

    def __init__(self, label_text: str, initial_color: QColor, parent=None):
        super().__init__(parent)
        self._color = QColor(initial_color)
        self._dialog_title = f"Select {label_text}"

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.swatch_btn = QPushButton()
        self.swatch_btn.setFixedSize(32, 32)
        self.swatch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.swatch_btn.setToolTip("Click để chọn màu")
        self.swatch_btn.clicked.connect(self._open_picker)
        layout.addWidget(self.swatch_btn)

        label = QLabel(label_text)
        label.setStyleSheet("color: #3F3F46; font-size: 13px; font-weight: 500; background: transparent;")
        layout.addWidget(label)

        layout.addStretch()

        self.hex_input = QLineEdit()
        self.hex_input.setFixedWidth(90)
        self.hex_input.setMaxLength(7)
        self.hex_input.setStyleSheet("""
            QLineEdit {
                background-color: #F4F4F5;
                color: #18181B;
                border: 1px solid rgba(0,0,0,0.08);
                border-radius: 6px;
                padding: 4px 8px;
                font-family: Consolas, monospace;
                font-size: 12px;
            }
            QLineEdit:focus { border-color: #3B82F6; background-color: #FFFFFF; }
        """)
        self.hex_input.editingFinished.connect(self._on_hex_edited)
        layout.addWidget(self.hex_input)

        self._refresh()

    def color(self) -> QColor:
        return QColor(self._color)

    def set_color(self, color: QColor, emit_signal: bool = False):
        if not color.isValid():
            return
        self._color = QColor(color)
        self._refresh()
        if emit_signal:
            self.colorChanged.emit(self._color)

    def _refresh(self):
        # Viền xám nhạt cố định (không dùng viền trắng) để swatch luôn nổi rõ trên nền card
        # trắng của dialog, kể cả khi màu đang chọn là trắng hoặc gần trắng.
        self.swatch_btn.setStyleSheet(
            f"background-color: {self._color.name()}; border-radius: 16px; border: 2px solid rgba(0,0,0,0.15);"
        )
        self.hex_input.setText(self._color.name().upper())

    def _open_picker(self):
        col = QColorDialog.getColor(self._color, self, self._dialog_title)
        if col.isValid():
            self.set_color(col, emit_signal=True)

    def _on_hex_edited(self):
        text = self.hex_input.text().strip()
        if text and not text.startswith("#"):
            text = "#" + text
        col = QColor(text)
        if col.isValid():
            self.set_color(col, emit_signal=True)
        else:
            self.hex_input.setText(self._color.name().upper())


class RecordingKeySequenceEdit(QKeySequenceEdit):
    """QKeySequenceEdit phát tín hiệu recordingChanged(bool) khi focus vào/ra để hiện phản hồi
    trực quan lúc đang 'ghi phím tắt' (border đổi màu, chấm đỏ nhấp nháy — xử lý ở nơi dùng)."""
    recordingChanged = pyqtSignal(bool)

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.recordingChanged.emit(True)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.recordingChanged.emit(False)
