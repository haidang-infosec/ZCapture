import os
import time
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QFontMetrics, QBrush, QPen

class WatermarkSettings:
    def __init__(self):
        self.enabled = False
        self.text = "ZCS-Labs"
        self.font_family = "Segoe UI"
        self.font_size = 18
        self.color = QColor(255, 255, 255, 180)
        self.position = "Bottom-Right"  # Bottom-Right, Bottom-Left, Top-Right, Top-Left, Center
        self.opacity = 0.7
        self.logo_path = ""

def apply_watermark(pixmap: QPixmap, settings: WatermarkSettings) -> QPixmap:
    """Chèn Watermark Text / Logo vào ảnh."""
    if not settings.enabled:
        return pixmap

    result = QPixmap(pixmap)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

    w, h = result.width(), result.height()
    margin = 16

    # 1. Render Logo Watermark if logo_path is configured and exists
    if settings.logo_path and os.path.exists(settings.logo_path):
        logo_pm = QPixmap(settings.logo_path)
        if not logo_pm.isNull():
            max_w = min(200, max(40, int(w * 0.25)))
            max_h = min(120, max(30, int(h * 0.25)))
            scaled_logo = logo_pm.scaled(max_w, max_h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            lw, lh = scaled_logo.width(), scaled_logo.height()

            if settings.position == "Bottom-Right":
                pos_x, pos_y = w - lw - margin, h - lh - margin
            elif settings.position == "Bottom-Left":
                pos_x, pos_y = margin, h - lh - margin
            elif settings.position == "Top-Right":
                pos_x, pos_y = w - lw - margin, margin
            elif settings.position == "Top-Left":
                pos_x, pos_y = margin, margin
            else:  # Center
                pos_x, pos_y = (w - lw) // 2, (h - lh) // 2

            painter.setOpacity(settings.opacity)
            painter.drawPixmap(pos_x, pos_y, scaled_logo)
            painter.setOpacity(1.0)
            painter.end()
            return result

    # 2. Render Text Watermark
    font = QFont(settings.font_family, settings.font_size, QFont.Weight.Bold)
    painter.setFont(font)

    color = QColor(settings.color)
    color.setAlpha(int(settings.opacity * 255))
    painter.setPen(QPen(color))

    metrics = QFontMetrics(font)
    text_w = metrics.horizontalAdvance(settings.text)
    text_h = metrics.height()

    if settings.position == "Bottom-Right":
        pos_x = w - text_w - margin
        pos_y = h - margin
    elif settings.position == "Bottom-Left":
        pos_x = margin
        pos_y = h - margin
    elif settings.position == "Top-Right":
        pos_x = w - text_w - margin
        pos_y = text_h + margin
    elif settings.position == "Top-Left":
        pos_x = margin
        pos_y = text_h + margin
    else:  # Center
        pos_x = (w - text_w) // 2
        pos_y = (h + text_h) // 2

    # Draw semi-transparent text badge background
    bg_rect = QRect(pos_x - 6, pos_y - text_h, text_w + 12, text_h + 6)
    painter.fillRect(bg_rect, QColor(0, 0, 0, int(settings.opacity * 120)))

    painter.drawText(pos_x, pos_y, settings.text)
    painter.end()

    return result

def apply_timestamp(pixmap: QPixmap) -> QPixmap:
    """Chèn nhãn Thời gian (Timestamp: YYYY-MM-DD HH:MM:SS) vào góc ảnh."""
    if pixmap.isNull():
        return pixmap

    result = QPixmap(pixmap)
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

    ts_str = time.strftime("%Y-%m-%d %H:%M:%S")
    font = QFont("Segoe UI", 11, QFont.Weight.Bold)
    painter.setFont(font)
    fm = QFontMetrics(font)
    bw = fm.horizontalAdvance(ts_str) + 16
    bh = fm.height() + 8

    # Đặt góc dưới bên trái ảnh
    rect = QRect(12, result.height() - bh - 12, bw, bh)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(15, 15, 20, 220)))
    painter.drawRoundedRect(rect, 5, 5)

    painter.setPen(QPen(QColor(0, 104, 255))) # Zalo Blue accent dot
    painter.drawEllipse(rect.left() + 8, rect.top() + (bh - 6) // 2, 6, 6)

    painter.setPen(QPen(QColor(255, 255, 255)))
    painter.drawText(QRect(rect.left() + 18, rect.top(), bw - 18, bh), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, ts_str)
    painter.end()

    return result
