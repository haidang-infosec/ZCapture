import os
import sys
import ctypes

def enable_hidpi_awareness():
    """
    Kích hoạt Per-Monitor V2 DPI Awareness tối đa trên Windows.
    Đảm bảo DWM (Desktop Window Manager) cung cấp khung hình 1:1 physical pixel grid.
    """
    if sys.platform == "win32":
        # Tắt scaling logic của Qt: toạ độ Qt = physical pixel, khớp với grabWindow và Win32 rect.
        # Nếu bật, màn hình có DPI khác nhau (vd 125% + 100%) bị lệch toạ độ khi ghép đa màn hình.
        os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
        try:
            # DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 (-4)
            DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)
            ctypes.windll.user32.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
        except Exception:
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except Exception:
                try:
                    ctypes.windll.user32.SetProcessDPIAware()
                except Exception:
                    pass


_PX_RE = None
_SCALED_PROP = "_zc_ui_scaled"
_QT_MAX = 16777215
# Phóng thêm cho thanh công cụ overlay và menu popup để dễ bấm hơn (nhân với hệ số DPI)
TOOLBAR_BOOST = 1.2
# Icon trên thanh công cụ phóng thêm so với nút để nhìn rõ hơn
ICON_EXTRA = 1.25


def get_ui_scale() -> float:
    """Hệ số phóng UI = DPI hệ thống / 96 (vd 125% -> 1.25). Dùng vì đã tắt scaling của Qt."""
    if sys.platform != "win32":
        return 1.0
    try:
        dpi = ctypes.windll.user32.GetDpiForSystem()
        return max(1.0, round(dpi / 96.0, 2))
    except Exception:
        return 1.0


def _scale_stylesheet(css: str, s: float, font_mul: float = 1.0) -> str:
    global _PX_RE
    import re
    if _PX_RE is None:
        _PX_RE = re.compile(r"(?<![\w.#-])(\d+(?:\.\d+)?)px")
    if font_mul != 1.0:
        # font-size được nhân thêm font_mul; đánh dấu "@px" để lượt phóng chung bên dưới bỏ qua
        css = re.sub(r"(font-size:\s*)(\d+(?:\.\d+)?)px",
                     lambda m: f"{m.group(1)}{round(float(m.group(2)) * s * font_mul)}@px", css)
    out = _PX_RE.sub(lambda m: f"{round(float(m.group(1)) * s)}px", css)
    return out.replace("@px", "px")


def _scale_widget(w, s: float, icon_mul: float = 1.0) -> None:
    from PyQt6.QtWidgets import QAbstractButton, QWidget
    if w.property(_SCALED_PROP):
        return
    w.setProperty(_SCALED_PROP, True)

    css = w.styleSheet()
    if css and "px" in css:
        w.setStyleSheet(_scale_stylesheet(css, s, icon_mul))

    from PyQt6.QtWidgets import QComboBox
    # QComboBox: min/max size đến từ stylesheet (đã được phóng ở trên), nhân thêm lần nữa sẽ bị quá to
    if not isinstance(w, QComboBox):
        mn, mx = w.minimumSize(), w.maximumSize()
        if mn.width() > 0 or mn.height() > 0:
            w.setMinimumSize(round(mn.width() * s), round(mn.height() * s))
        nw = mx.width() if mx.width() >= _QT_MAX else round(mx.width() * s)
        nh = mx.height() if mx.height() >= _QT_MAX else round(mx.height() * s)
        if (nw, nh) != (mx.width(), mx.height()):
            w.setMaximumSize(nw, nh)

    if isinstance(w, QAbstractButton) and icon_mul > 1.0 and w.icon().isNull() and 0 < len(w.text()) <= 2:
        # Nút glyph (T, undo/redo, settings, pin, save...): setFont tường minh nên phải phóng cỡ chữ trực tiếp
        f = w.font()
        px = f.pixelSize() if f.pixelSize() > 0 else round(f.pointSizeF() * 96 / 72)
        px = max(8, round(px * s * icon_mul))
        if w.maximumWidth() < _QT_MAX:
            px = min(px, int(w.maximumWidth() * 0.5))  # chừa chỗ để glyph/emoji không bị cắt thành "..."
        f.setPixelSize(px)
        w.setFont(f)
        w.setStyleSheet(w.styleSheet() + f" QAbstractButton {{ font-size: {px}px; }}")

    if isinstance(w, QAbstractButton):
        ic = w.iconSize()
        if ic.isValid() and ic.width() > 0:
            w.setIconSize(ic * (s * icon_mul))

    # Widget đặt tay bằng setGeometry trong cửa sổ không có layout (vd container của Settings)
    parent = w.parentWidget()
    if parent is not None and parent.isWindow() and parent.layout() is None             and not hasattr(parent, "update_toolbar_positions"):
        g = w.geometry()
        w.setGeometry(round(g.x() * s), round(g.y() * s), round(g.width() * s), round(g.height() * s))

    lay = w.layout()
    if lay is not None:
        m = lay.contentsMargins()
        lay.setContentsMargins(round(m.left() * s), round(m.top() * s), round(m.right() * s), round(m.bottom() * s))
        if lay.spacing() > 0:
            lay.setSpacing(round(lay.spacing() * s))


def apply_ui_scale(root, s: float | None = None, boost: float = 1.0) -> None:
    """Phóng to một cây widget (kích thước cố định, margin, spacing, px trong stylesheet) theo hệ số s * boost."""
    from PyQt6.QtWidgets import QWidget
    s = (s or get_ui_scale()) * boost
    if s <= 1.0:
        return
    icon_mul = ICON_EXTRA if boost > 1.0 else 1.0
    _scale_widget(root, s, icon_mul)
    for child in root.findChildren(QWidget):
        _scale_widget(child, s, icon_mul)


def install_auto_ui_scale(app, exclude_types=()) -> None:
    """Tự phóng mọi widget của app khi hiện lần đầu (trừ các lớp trong exclude_types, vd canvas overlay)."""
    from PyQt6.QtCore import QObject, QEvent, QTimer
    from PyQt6.QtWidgets import QWidget
    s = get_ui_scale()
    if s <= 1.0:
        return

    class _Filter(QObject):
        def eventFilter(self, obj, ev):
            if ev.type() == QEvent.Type.Show and isinstance(obj, QWidget) \
                    and not isinstance(obj, exclude_types) and not obj.property(_SCALED_PROP):
                from PyQt6.QtWidgets import QMenu
                top = obj.window()
                boosted = isinstance(top, QMenu) or hasattr(top, "update_toolbar_positions")
                apply_ui_scale(obj, s, TOOLBAR_BOOST if boosted else 1.0)
                parent = obj.parentWidget()
                if parent is not None and hasattr(parent, "update_toolbar_positions"):
                    QTimer.singleShot(0, parent.update_toolbar_positions)
            return False

    app._zc_scale_filter = _Filter(app)
    app.installEventFilter(app._zc_scale_filter)
