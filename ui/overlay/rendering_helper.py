import math
from PyQt6.QtCore import Qt, QRect, QRectF, QPoint, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPixmap, QImage, QPolygonF,
    QFontMetrics, QPainterPath
)

from models.annotations import (
    ShapeItem, ArrowItem, HighlightItem, PathItem, StepItem, TextItem,
    TimestampItem, WatermarkItem, WatermarkLogoItem, MosaicItem, BlackoutItem,
    LineItem, BlurItem
)


def draw_dimension_badge(painter: QPainter, r: QRect, widget_w: int, widget_h: int):
    """Vẽ nhãn kích thước (W × H px) chuẩn Figma/Apple với nền kính mờ trắng, viền sắc nét và đổ bóng mềm."""
    r = r.normalized()
    txt = f"{r.width()} × {r.height()} px"
    font = QFont("Consolas", 10, QFont.Weight.Bold)
    font.setStyleHint(QFont.StyleHint.Monospace)
    painter.setFont(font)

    metrics = QFontMetrics(font)
    bw = metrics.horizontalAdvance(txt) + 24
    bh = 28

    bx = max(10, min(widget_w - bw - 10, r.left()))
    by = r.top() - bh - 8
    if by < 10:
        by = r.top() + 10

    badge_rect = QRect(bx, by, bw, bh)

    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    # Soft ambient drop shadow
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(0, 0, 0, 22)))
    painter.drawRoundedRect(badge_rect.translated(0, 3), 8, 8)
    painter.setBrush(QBrush(QColor(0, 0, 0, 15)))
    painter.drawRoundedRect(badge_rect.translated(0, 1), 8, 8)

    # Glassmorphic pill body
    painter.setPen(QPen(QColor(0, 0, 0, 20), 1))
    painter.setBrush(QBrush(QColor(255, 255, 255, 248)))
    painter.drawRoundedRect(badge_rect, 8, 8)

    # Crisp typography
    painter.setPen(QPen(QColor("#18181B")))
    painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, txt)
    painter.restore()


def draw_magnifier_loupe(painter: QPainter, pos: QPoint, full_pixmap: QPixmap, cached_image: QImage, widget_w: int, widget_h: int, color_format: str = "HEX"):
    """Vẽ kính lúp cận cảnh pixel + Tọa độ + Mã màu RGB/HEX sắc nét chuẩn Pro."""
    if pos.x() < 0 or pos.y() < 0 or pos.x() >= widget_w or pos.y() >= widget_h:
        return

    size = 130
    grid_count = 15
    extra_h = 42
    box_rect = QRect(pos.x() + 18, pos.y() + 18, size, size + extra_h)

    if box_rect.right() > widget_w:
        box_rect.moveLeft(max(0, pos.x() - size - 18))
    if box_rect.bottom() > widget_h:
        box_rect.moveTop(max(0, pos.y() - size - extra_h - 10))

    if box_rect.left() < 4:
        box_rect.moveLeft(4)
    if box_rect.top() < 4:
        box_rect.moveTop(4)
    if box_rect.right() > widget_w - 4:
        box_rect.moveLeft(max(4, widget_w - box_rect.width() - 4))
    if box_rect.bottom() > widget_h - 4:
        box_rect.moveTop(max(4, widget_h - box_rect.height() - 4))

    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    scale_x = full_pixmap.width() / float(max(1, widget_w))
    scale_y = full_pixmap.height() / float(max(1, widget_h))

    phys_x = int(pos.x() * scale_x)
    phys_y = int(pos.y() * scale_y)

    img = cached_image
    if 0 <= phys_x < img.width() and 0 <= phys_y < img.height():
        col = img.pixelColor(phys_x, phys_y)
        hex_code = col.name().upper()

        # Drop shadow behind magnifier card
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 55)))
        painter.drawRoundedRect(box_rect.translated(0, 4), 10, 10)
        painter.setBrush(QBrush(QColor(0, 0, 0, 30)))
        painter.drawRoundedRect(box_rect.translated(0, 2), 10, 10)

        # Draw card container
        painter.setPen(QPen(QColor(59, 130, 246, 220), 1.5))
        painter.setBrush(QBrush(QColor(15, 23, 42, 248)))
        painter.drawRoundedRect(box_rect, 10, 10)

        # Zoomed viewport with top-rounded clipping
        zoom_rect = QRect(box_rect.left() + 1, box_rect.top() + 1, size - 2, size - 2)
        clip_path = QPainterPath()
        clip_path.addRoundedRect(QRectF(box_rect.left() + 1, box_rect.top() + 1, size - 2, size - 2), 9, 9)

        painter.save()
        painter.setClipPath(clip_path)

        src_rect = QRect(phys_x - grid_count // 2, phys_y - grid_count // 2, grid_count, grid_count)
        zoomed_pm = full_pixmap.copy(src_rect).scaled(size - 2, size - 2, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
        painter.drawPixmap(zoom_rect.topLeft(), zoomed_pm)

        # Precision target reticle at center
        cx = zoom_rect.center().x()
        cy = zoom_rect.center().y()
        target_size = 9
        half_ts = target_size // 2

        # Outer target box
        painter.setPen(QPen(QColor(0, 0, 0, 180), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(cx - half_ts, cy - half_ts, target_size, target_size)
        painter.setPen(QPen(QColor(255, 255, 255, 240), 1))
        painter.drawRect(cx - half_ts, cy - half_ts, target_size, target_size)

        # Subtle cross ticks
        painter.setPen(QPen(QColor(59, 130, 246, 200), 1))
        painter.drawLine(cx, zoom_rect.top(), cx, cy - half_ts - 2)
        painter.drawLine(cx, cy + half_ts + 3, cx, zoom_rect.bottom())
        painter.drawLine(zoom_rect.left(), cy, cx - half_ts - 2, cy)
        painter.drawLine(cx + half_ts + 3, cy, zoom_rect.right(), cy)

        painter.restore()

        # Divider line between zoom and metadata
        painter.setPen(QPen(QColor(30, 41, 59), 1))
        painter.drawLine(box_rect.left() + 1, box_rect.top() + size, box_rect.right() - 1, box_rect.top() + size)

        # Metadata footer
        info_rect = QRect(box_rect.left() + 8, box_rect.top() + size + 4, size - 16, extra_h - 8)

        # Color Swatch with double border for light & dark contrast
        swatch_rect = QRect(info_rect.left(), info_rect.top() + 3, 13, 13)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(col))
        painter.drawRoundedRect(swatch_rect, 3, 3)
        painter.setPen(QPen(QColor(255, 255, 255, 140), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(swatch_rect, 3, 3)

        # Color Code Label (Monospace)
        font_col = QFont("Consolas", 8, QFont.Weight.Bold)
        painter.setFont(font_col)
        painter.setPen(QPen(QColor("#F8FAFC")))
        if color_format.upper() == "RGB":
            col_str = f"{col.red()},{col.green()},{col.blue()}"
        else:
            col_str = f"{hex_code}"
        painter.drawText(QRect(info_rect.left() + 18, info_rect.top() + 1, info_rect.width() - 18, 16),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, col_str)

        # Coordinate & Copy Shortcut Pill Hint
        font_sub = QFont("Segoe UI", 7)
        painter.setFont(font_sub)
        painter.setPen(QPen(QColor("#94A3B8")))
        pos_str = f"{phys_x}, {phys_y}"
        painter.drawText(QRect(info_rect.left(), info_rect.top() + 18, info_rect.width() - 32, 14),
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, pos_str)

        # Mini keyboard badge [C]
        badge_w = 26
        badge_rect = QRect(info_rect.right() - badge_w + 1, info_rect.top() + 18, badge_w, 13)
        painter.setPen(QPen(QColor(51, 65, 85), 1))
        painter.setBrush(QBrush(QColor(30, 41, 59)))
        painter.drawRoundedRect(badge_rect, 3, 3)
        painter.setPen(QPen(QColor("#38BDF8")))
        badge_font = QFont("Segoe UI", 6, QFont.Weight.Bold)
        painter.setFont(badge_font)
        painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, "C:copy")

    painter.restore()


def draw_annotation_item(painter: QPainter, item, selected_annotation=None, current_drawing_item=None):
    """Render một đối tượng chú thích (AnnotationItem) bất kỳ lên Canvas."""
    if isinstance(item, ShapeItem):
        if item.color.alpha() > 0:
            painter.setPen(QPen(item.color, item.stroke_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        else:
            painter.setPen(Qt.PenStyle.NoPen)
        fill_col = getattr(item, "fill_color", None)
        if fill_col is not None and fill_col.alpha() > 0:
            painter.setBrush(QBrush(fill_col))
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
        stype = getattr(item, "tool_type", getattr(item, "shape_type", "rect"))
        if stype == "circle":
            painter.drawEllipse(item.rect)
        else:
            painter.drawRoundedRect(item.rect, 4, 4)

    elif isinstance(item, LineItem):
        pen = QPen(item.color, item.stroke_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(item.start_p, item.end_p)

    elif isinstance(item, ArrowItem):
        pen = QPen(item.color, item.stroke_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawLine(item.start_p, item.end_p)
        angle = math.atan2(item.end_p.y() - item.start_p.y(), item.end_p.x() - item.start_p.x())
        arrow_len = 16
        p1 = item.end_p - QPoint(int(arrow_len * math.cos(angle - math.pi / 6)), int(arrow_len * math.sin(angle - math.pi / 6)))
        p2 = item.end_p - QPoint(int(arrow_len * math.cos(angle + math.pi / 6)), int(arrow_len * math.sin(angle + math.pi / 6)))
        painter.setBrush(QBrush(item.color))
        painter.drawPolygon(QPolygonF([QPointF(item.end_p), QPointF(p1), QPointF(p2)]))

    elif isinstance(item, PathItem):
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

    elif isinstance(item, StepItem):
        r = 14
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(item.color))
        painter.drawEllipse(item.pos, r, r)

        painter.setPen(QPen(Qt.GlobalColor.white))
        font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(QRect(item.pos.x() - r, item.pos.y() - r, r * 2, r * 2), Qt.AlignmentFlag.AlignCenter, str(item.number))

    elif isinstance(item, TextItem):
        painter.setFont(item.font)
        rect = item.get_bounding_rect()
        text_rect = rect.adjusted(10, 6, -10, -6)
        flags = int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        if item.bg_mode == "badge":
            bg_col = QColor(16, 16, 24, int(item.bg_opacity * 255))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(bg_col))
            painter.drawRoundedRect(rect, 6, 6)

            painter.setPen(QPen(item.color))
            painter.drawText(text_rect, flags, item.text)

        elif item.bg_mode == "color":
            bg_col = QColor(item.bg_color) if hasattr(item, "bg_color") else QColor(26, 26, 38)
            bg_col.setAlpha(int(item.bg_opacity * 255))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(bg_col))
            painter.drawRoundedRect(rect, 6, 6)

            painter.setPen(QPen(item.color))
            painter.drawText(text_rect, flags, item.text)

        elif item.bg_mode == "none":
            painter.setPen(QPen(item.color))
            painter.drawText(text_rect, flags, item.text)

    elif isinstance(item, TimestampItem):
        painter.setFont(item.font)
        rect = item.get_bounding_rect()

        bg_col = QColor(16, 16, 22, 230)
        painter.setPen(QPen(QColor(0, 104, 255, 210), 1.5))
        painter.setBrush(QBrush(bg_col))
        painter.drawRoundedRect(rect, 6, 6)

        painter.setPen(QPen(item.color))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, item.text)

    elif isinstance(item, WatermarkItem):
        painter.setFont(item.font)
        rect = item.get_bounding_rect()

        bg_col = QColor(15, 15, 20, 220)
        painter.setPen(QPen(QColor(255, 255, 255, 100), 1))
        painter.setBrush(QBrush(bg_col))
        painter.drawRoundedRect(rect, 6, 6)

        wm_col = QColor(item.color)
        wm_col.setAlpha(int(item.opacity * 255))
        painter.setPen(QPen(wm_col))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, item.text)

    elif isinstance(item, WatermarkLogoItem):
        rect = item.get_bounding_rect()
        painter.setOpacity(item.opacity)
        scaled_logo = item.original_pixmap.scaled(rect.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        painter.drawPixmap(rect.topLeft(), scaled_logo)
        painter.setOpacity(1.0)

    elif isinstance(item, (MosaicItem, BlackoutItem)):
        if item == selected_annotation or item == current_drawing_item:
            painter.setPen(QPen(QColor(0, 104, 255), 1.5, Qt.PenStyle.DashLine))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(item.rect)
