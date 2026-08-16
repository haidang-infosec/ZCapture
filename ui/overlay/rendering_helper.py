import math
from PyQt6.QtCore import Qt, QRect, QRectF, QPoint, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QBrush, QColor, QFont, QPixmap, QImage, QPolygonF,
    QFontMetrics, QPainterPath
)

from models.annotations import (
    ShapeItem, ArrowItem, HighlightItem, PathItem, StepItem, TextItem,
    TimestampItem, WatermarkItem, WatermarkLogoItem, MosaicItem, BlackoutItem
)


def draw_dimension_badge(painter: QPainter, r: QRect, widget_w: int, widget_h: int):
    """Vẽ nhãn kích thước (922 x 561 px) nền trắng pill bo góc 8px góc trên trái chuẩn screenshot."""
    r = r.normalized()
    txt = f"{r.width()} x {r.height()} px"
    font = QFont("Consolas", 10, QFont.Weight.Bold)
    font.setStyleHint(QFont.StyleHint.Monospace)
    painter.setFont(font)

    metrics = QFontMetrics(font)
    bw = metrics.horizontalAdvance(txt) + 20
    bh = 28

    bx = max(10, min(widget_w - bw - 10, r.left()))
    by = r.top() - bh - 8
    if by < 10:
        by = r.top() + 10

    badge_rect = QRect(bx, by, bw, bh)

    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QBrush(QColor(0, 0, 0, 20)))
    painter.drawRoundedRect(badge_rect.translated(0, 2), 8, 8)

    painter.setPen(QPen(QColor("rgba(0, 0, 0, 0.08)"), 1))
    painter.setBrush(QBrush(QColor(255, 255, 255, 245)))
    painter.drawRoundedRect(badge_rect, 8, 8)

    painter.setPen(QPen(QColor("#3F3F46")))
    painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, txt)


def draw_magnifier_loupe(painter: QPainter, pos: QPoint, full_pixmap: QPixmap, cached_image: QImage, widget_w: int, widget_h: int):
    """Vẽ kính lúp cận cảnh pixel + Mã màu RGB/HEX chuẩn Zalo Style."""
    if pos.x() < 0 or pos.y() < 0 or pos.x() >= widget_w or pos.y() >= widget_h:
        return

    size = 120
    grid_count = 15
    box_rect = QRect(pos.x() + 18, pos.y() + 18, size, size + 25)

    if box_rect.right() > widget_w:
        box_rect.moveLeft(max(0, pos.x() - size - 18))
    if box_rect.bottom() > widget_h:
        box_rect.moveTop(max(0, pos.y() - size - 40))

    if box_rect.left() < 2:
        box_rect.moveLeft(2)
    if box_rect.top() < 2:
        box_rect.moveTop(2)
    if box_rect.right() > widget_w - 2:
        box_rect.moveLeft(max(2, widget_w - box_rect.width() - 2))
    if box_rect.bottom() > widget_h - 2:
        box_rect.moveTop(max(2, widget_h - box_rect.height() - 2))

    painter.setPen(QPen(QColor(0, 104, 255), 2))
    painter.setBrush(QBrush(QColor(30, 30, 36, 235)))
    painter.drawRoundedRect(box_rect, 6, 6)

    scale_x = full_pixmap.width() / float(max(1, widget_w))
    scale_y = full_pixmap.height() / float(max(1, widget_h))

    phys_x = int(pos.x() * scale_x)
    phys_y = int(pos.y() * scale_y)

    img = cached_image
    if 0 <= phys_x < img.width() and 0 <= phys_y < img.height():
        col = img.pixelColor(phys_x, phys_y)
        hex_code = col.name().upper()

        src_rect = QRect(phys_x - grid_count // 2, phys_y - grid_count // 2, grid_count, grid_count)
        zoomed_pm = full_pixmap.copy(src_rect).scaled(size, size, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
        painter.drawPixmap(box_rect.topLeft(), zoomed_pm)

        center_x = box_rect.left() + size // 2
        center_y = box_rect.top() + size // 2
        painter.setPen(QPen(QColor(0, 104, 255, 230), 1))
        painter.drawRect(center_x - 4, center_y - 4, 8, 8)

        painter.setPen(QPen(Qt.GlobalColor.white))
        font = QFont("Consolas", 9, QFont.Weight.Bold)
        painter.setFont(font)
        dim_str = f"{hex_code} | {col.red()},{col.green()},{col.blue()}"
        painter.drawText(QRect(box_rect.left(), box_rect.bottom() - 20, size, 20), Qt.AlignmentFlag.AlignCenter, dim_str)


def draw_annotation_item(painter: QPainter, item, selected_annotation=None, current_drawing_item=None):
    """Render một đối tượng chú thích (AnnotationItem) bất kỳ lên Canvas."""
    if isinstance(item, ShapeItem):
        pen = QPen(item.color, item.stroke_width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        stype = getattr(item, "tool_type", getattr(item, "shape_type", "rect"))
        if stype == "circle":
            painter.drawEllipse(item.rect)
        else:
            painter.drawRoundedRect(item.rect, 4, 4)

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

        if item.bg_mode == "badge":
            bg_col = QColor(16, 16, 24, int(item.bg_opacity * 255))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(bg_col))
            painter.drawRoundedRect(rect, 6, 6)

            painter.setPen(QPen(item.color))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, item.text)

        elif item.bg_mode == "color":
            bg_col = QColor(item.bg_color) if hasattr(item, "bg_color") else QColor(26, 26, 38)
            bg_col.setAlpha(int(item.bg_opacity * 255))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(bg_col))
            painter.drawRoundedRect(rect, 6, 6)

            painter.setPen(QPen(item.color))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, item.text)

        elif item.bg_mode == "none":
            painter.setPen(QPen(item.color))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, item.text)

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
