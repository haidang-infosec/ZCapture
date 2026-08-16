from PyQt6.QtCore import Qt, QRect, QPoint
from PyQt6.QtGui import QColor, QFont, QPixmap, QFontMetrics

def calc_position_from_setting(pos_name: str, item_w: int, item_h: int, sel_rect: QRect) -> QPoint:
    """Tính toán tọa độ hiển thị theo cấu hình vị trí Settings (Bottom-Right, Bottom-Left, Top-Right, Top-Left, Center)."""
    pos_name = (pos_name or "").lower()
    margin = 15
    if "top" in pos_name and "left" in pos_name:
        x = sel_rect.left() + margin
        y = sel_rect.top() + margin
    elif "top" in pos_name and "right" in pos_name:
        x = sel_rect.right() - item_w - margin
        y = sel_rect.top() + margin
    elif "bottom" in pos_name and "left" in pos_name:
        x = sel_rect.left() + margin
        y = sel_rect.bottom() - item_h - margin
    elif "center" in pos_name:
        x = sel_rect.left() + (sel_rect.width() - item_w) // 2
        y = sel_rect.top() + (sel_rect.height() - item_h) // 2
    else:  # Default Bottom-Right
        x = sel_rect.right() - item_w - margin
        y = sel_rect.bottom() - item_h - margin

    if x < sel_rect.left(): x = sel_rect.left() + 5
    if y < sel_rect.top(): y = sel_rect.top() + 5
    return QPoint(x, y)


class AnnotationItem:
    """Lớp cha lưu thông tin các đối tượng vẽ trên hình (Vector Annotation)."""
    def __init__(self, tool_type, color, stroke_width=3):
        self.tool_type = tool_type
        self.color = QColor(color)
        self.stroke_width = stroke_width
        self.selected = False

    def get_bounding_rect(self) -> QRect:
        return QRect()


class ShapeItem(AnnotationItem):
    def __init__(self, tool_type, rect: QRect, color, stroke_width=3, fill=False, corner_radius=8):
        super().__init__(tool_type, color, stroke_width)
        self.rect = rect
        self.fill = fill
        self.corner_radius = corner_radius

    def get_bounding_rect(self) -> QRect:
        return self.rect.normalized()


class ArrowItem(AnnotationItem):
    def __init__(self, start_p: QPoint, end_p: QPoint, color, stroke_width=3):
        super().__init__("arrow", color, stroke_width)
        self.start_p = start_p
        self.end_p = end_p

    def get_bounding_rect(self) -> QRect:
        return QRect(self.start_p, self.end_p).normalized().adjusted(-8, -8, 8, 8)


class HighlightItem(AnnotationItem):
    """Đối tượng Tô Highlight Vùng Chữ Nhật Dạ Quang (Phóng to thu nhỏ & Di chuyển tự do)."""
    def __init__(self, rect: QRect, color: QColor):
        super().__init__("highlighter", color)
        self.rect = rect

    def get_bounding_rect(self) -> QRect:
        return self.rect.normalized()


class PathItem(AnnotationItem):
    def __init__(self, points, color, stroke_width=3, tool_type="pencil"):
        super().__init__("pencil", color, stroke_width)
        self.points = points
        self.tool_type = tool_type
        self._cached_rect = None
        self._last_len = 0

    def get_bounding_rect(self) -> QRect:
        if not self.points:
            return QRect()
        if self._cached_rect is not None and len(self.points) == self._last_len:
            return self._cached_rect
        min_x = min(p.x() for p in self.points)
        max_x = max(p.x() for p in self.points)
        min_y = min(p.y() for p in self.points)
        max_y = max(p.y() for p in self.points)
        self._cached_rect = QRect(QPoint(min_x, min_y), QPoint(max_x, max_y)).adjusted(-6, -6, 6, 6)
        self._last_len = len(self.points)
        return self._cached_rect


class StepItem(AnnotationItem):
    def __init__(self, pos: QPoint, number: int, color):
        super().__init__("step", color)
        self.pos = pos
        self.number = number

    def get_bounding_rect(self) -> QRect:
        r = 16
        return QRect(self.pos.x() - r, self.pos.y() - r, r * 2, r * 2)


class TextItem(AnnotationItem):
    def __init__(self, pos: QPoint, text: str, font: QFont, color, bg_color=None, bg_mode="badge", bg_opacity=0.85):
        super().__init__("text", color)
        self.pos = pos
        self.text = text
        self.font = QFont(font)
        if self.font.pointSize() <= 0:
            if self.font.pixelSize() > 0:
                self.font.setPointSize(self.font.pixelSize())
            else:
                self.font.setPointSize(14)
        self.bg_color = QColor(bg_color) if bg_color else QColor(16, 16, 24)
        self.bg_mode = bg_mode
        self.bg_opacity = bg_opacity
        self.calc_rect()

    def calc_rect(self):
        metrics = QFontMetrics(self.font)
        lines = self.text.split("\n") if "\n" in self.text else [self.text]
        max_w = 0
        line_spacing = metrics.lineSpacing()
        for line in lines:
            max_w = max(max_w, metrics.horizontalAdvance(line))
        total_h = max(metrics.height(), len(lines) * line_spacing)

        pad_x = 8
        pad_y = 5
        self.rect = QRect(self.pos.x(), self.pos.y(), max_w + pad_x * 2, max(total_h + pad_y * 2, 26))

    def get_bounding_rect(self) -> QRect:
        self.calc_rect()
        return self.rect


class TimestampItem(AnnotationItem):
    """Đối tượng Nhãn Ngày Giờ Chuyên Nghiệp (Đồng Bộ Cấu Hình Settings)."""
    def __init__(self, pos: QPoint, text: str, font: QFont, color: QColor):
        super().__init__("timestamp", color)
        self.pos = pos
        self.text = text
        self.font = QFont(font)
        if self.font.pointSize() <= 0:
            if self.font.pixelSize() > 0:
                self.font.setPointSize(self.font.pixelSize())
            else:
                self.font.setPointSize(14)
        self.calc_rect()

    def calc_rect(self):
        metrics = QFontMetrics(self.font)
        br = metrics.boundingRect(self.text)
        pad = 12
        self.rect = QRect(self.pos.x(), self.pos.y(), br.width() + pad * 2, max(br.height() + pad * 2, 28))

    def get_bounding_rect(self) -> QRect:
        self.calc_rect()
        return self.rect


class WatermarkItem(AnnotationItem):
    """Đối tượng Watermark Chữ Chuyên Nghiệp (Đồng Bộ Đầy Đủ Cấu Hình Settings)."""
    def __init__(self, pos: QPoint, text: str, font: QFont, color: QColor, opacity=0.85):
        super().__init__("watermark", color)
        self.pos = pos
        self.text = text
        self.font = QFont(font)
        if self.font.pointSize() <= 0:
            if self.font.pixelSize() > 0:
                self.font.setPointSize(self.font.pixelSize())
            else:
                self.font.setPointSize(14)
        self.opacity = opacity
        self.calc_rect()

    def calc_rect(self):
        metrics = QFontMetrics(self.font)
        br = metrics.boundingRect(self.text)
        pad = 12
        self.rect = QRect(self.pos.x(), self.pos.y(), br.width() + pad * 2, max(br.height() + pad * 2, 32))

    def get_bounding_rect(self) -> QRect:
        self.calc_rect()
        return self.rect


class WatermarkLogoItem(AnnotationItem):
    """Đối tượng Watermark Logo Ảnh Chuyên Nghiệp (Đồng Bộ Đầy Đủ Cấu Hình Settings)."""
    def __init__(self, pos: QPoint, pixmap: QPixmap, opacity=0.85):
        super().__init__("watermark_logo", QColor(255, 255, 255))
        self.pos = pos
        self.original_pixmap = pixmap
        self.opacity = opacity
        self.rect = QRect(pos, pixmap.size())

    def get_bounding_rect(self) -> QRect:
        return self.rect.normalized()


class MosaicItem(AnnotationItem):
    def __init__(self, rect: QRect, block_size=12):
        super().__init__("mosaic", QColor(0, 0, 0))
        self.rect = rect
        self.block_size = block_size

    def get_bounding_rect(self) -> QRect:
        return self.rect.normalized()


class BlackoutItem(AnnotationItem):
    """Redact vùng chọn bằng khối màu đặc (opaque), phá hủy hoàn toàn dữ liệu pixel gốc.
    An toàn hơn Mosaic vì không thể bị khôi phục lại bằng các kỹ thuật depixelization."""
    def __init__(self, rect: QRect, color: QColor = None):
        super().__init__("blackout", color if color else QColor(0, 0, 0, 255))
        self.rect = rect

    def get_bounding_rect(self) -> QRect:
        return self.rect.normalized()
