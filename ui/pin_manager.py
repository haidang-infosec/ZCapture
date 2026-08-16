"""
Quản lý tập trung các cửa sổ Pin đang mở: đếm số lượng, hiển thị Indicator nổi góc
màn hình, danh sách chọn nhanh, và cơ chế Thu nhỏ (Minimize) về icon chip nổi.
Tách riêng khỏi PinnedWindow để một nơi duy nhất nắm giữ vòng đời của tất cả cửa sổ Pin.
"""
# pyrefly: ignore [missing-import]
from PyQt6.QtCore import Qt, QPoint
# pyrefly: ignore [missing-import]
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QGuiApplication
# pyrefly: ignore [missing-import]
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QGraphicsDropShadowEffect
)

_pin_windows = []
_minimized_chips = {}
_indicator = None
_pin_seq = 0


def next_pin_label() -> str:
    global _pin_seq
    _pin_seq += 1
    return f"Ảnh ghim {_pin_seq}"


def register_pin_window(win) -> None:
    if win not in _pin_windows:
        _pin_windows.append(win)
    _sync_indicator()


def unregister_pin_window(win) -> None:
    if win in _pin_windows:
        _pin_windows.remove(win)
    notify_shown(win)  # dọn chip thu nhỏ (nếu có) để tránh chip mồ côi
    _sync_indicator()


def minimize_window(win) -> None:
    """Ẩn cửa sổ Pin và thay bằng 1 icon chip nổi nhỏ ở góc màn hình."""
    if win in _minimized_chips:
        return
    chip = _MinimizedChip(win)
    _minimized_chips[win] = chip
    chip.show()
    _reflow_chips()
    win.hide()


def notify_shown(win) -> None:
    """Gọi khi cửa sổ Pin được show() trở lại — dọn chip thu nhỏ tương ứng nếu có."""
    chip = _minimized_chips.pop(win, None)
    if chip is not None:
        chip.close()
        _reflow_chips()


def _reflow_chips() -> None:
    ps = QGuiApplication.primaryScreen()
    if not ps:
        return
    screen = ps.availableGeometry()
    margin, gap = 24, 8
    dead_wins = []
    chips = list(_minimized_chips.items())
    for i, (win, chip) in enumerate(chips):
        try:
            x = screen.right() - margin - chip.width()
            y = screen.bottom() - margin - (chip.height() + gap) * (i + 1)
            chip.move(x, y)
        except (RuntimeError, AttributeError):
            dead_wins.append(win)
    for dw in dead_wins:
        _minimized_chips.pop(dw, None)


def _sync_indicator() -> None:
    global _indicator
    if _pin_windows:
        if _indicator is None:
            _indicator = PinIndicatorWidget()
        _indicator.refresh()
        _indicator.show()
    elif _indicator is not None:
        if _indicator.list_popup is not None:
            _indicator.list_popup.close()
            _indicator.list_popup = None
        _indicator.hide()


class _MinimizedChip(QWidget):
    """Icon chip tròn nổi thay thế cửa sổ Pin đã bị Thu nhỏ, click để khôi phục."""
    def __init__(self, win):
        super().__init__(None)
        self.win = win
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.setFixedSize(44, 44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"Khôi phục {getattr(win, 'label_text', 'Ảnh ghim')}")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(QColor(0, 104, 255), 2))
        painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
        painter.drawEllipse(2, 2, 40, 40)
        font = QFont("Segoe UI Emoji", 15)
        painter.setFont(font)
        painter.setPen(QPen(QColor(0, 104, 255)))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "📌")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            try:
                self.win.show()
                self.win.raise_()
                self.win.activateWindow()
            except RuntimeError:
                pass


class PinIndicatorWidget(QWidget):
    """Icon nổi góc màn hình hiển thị số ảnh đang Pin, click để mở danh sách chọn nhanh."""
    def __init__(self):
        super().__init__(None)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(46, 46)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Danh sách ảnh đang ghim")
        self.list_popup = None
        self._position_at_corner()

    def _position_at_corner(self):
        ps = QGuiApplication.primaryScreen()
        if not ps:
            return
        screen = ps.availableGeometry()
        margin = 24
        self.move(screen.right() - self.width() - margin, screen.bottom() - self.height() - margin)

    def refresh(self):
        self.update()
        if self.list_popup is not None:
            self.list_popup.rebuild()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(37, 99, 235, 235)))
        painter.drawEllipse(3, 3, 40, 40)
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = QFont("Segoe UI", 13, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, str(len(_pin_windows)))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._toggle_list()

    def _toggle_list(self):
        if self.list_popup is not None:
            self.list_popup.close()
            self.list_popup = None
            return
        self.list_popup = _PinListPopup(self)
        self.list_popup.show()
        self.list_popup.setFocus()


class _PinListPopup(QWidget):
    """Popup danh sách các cửa sổ Pin đang mở, click 1 mục để đưa cửa sổ đó lên trên cùng."""
    def __init__(self, indicator: PinIndicatorWidget):
        super().__init__(None, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.indicator = indicator

        self.container = QWidget(self)
        self.container.setObjectName("pinListContainer")
        self.container.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.container.setStyleSheet("""
            #pinListContainer {
                background-color: #FFFFFF;
                border: 1px solid rgba(0,0,0,0.15);
                border-radius: 12px;
            }
            QPushButton {
                text-align: left;
                background-color: transparent;
                border: none;
                border-radius: 8px;
                padding: 8px 10px;
                color: #3F3F46;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #F4F4F5;
                color: #18181B;
            }
        """)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(0, 0, 0, 60))
        self.container.setGraphicsEffect(shadow)

        self.list_layout = QVBoxLayout(self.container)
        self.list_layout.setContentsMargins(8, 8, 8, 8)
        self.list_layout.setSpacing(2)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)
        outer.addWidget(self.container)

        self.rebuild()

    def rebuild(self):
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        if not _pin_windows:
            lbl = QLabel("Không có ảnh nào đang ghim")
            lbl.setStyleSheet("color: #A1A1AA; font-size: 12px; padding: 6px 10px;")
            self.list_layout.addWidget(lbl)
        else:
            for win in list(_pin_windows):
                label = getattr(win, "label_text", "Ảnh ghim")
                minimized = win in _minimized_chips
                text = f"📌  {label}" + ("  (đã thu nhỏ)" if minimized else "")
                btn = QPushButton(text)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.clicked.connect(lambda _, w=win: self._activate(w))
                self.list_layout.addWidget(btn)

        self.adjustSize()
        self._position()

    def _position(self):
        ind_geo = self.indicator.geometry()
        self.adjustSize()
        x = ind_geo.right() - self.width() + 16
        y = ind_geo.top() - self.height() + 8
        self.move(x, y)

    def _activate(self, win):
        try:
            win.show()
            win.raise_()
            win.activateWindow()
        except RuntimeError:
            pass
        self.close()
        self.indicator.list_popup = None

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.close()
        self.indicator.list_popup = None
