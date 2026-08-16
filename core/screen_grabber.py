from PyQt6.QtCore import QRect, QPointF, Qt
from PyQt6.QtGui import QGuiApplication, QPixmap, QCursor, QPainter, QPolygonF, QPen, QBrush, QColor

def capture_full_desktop(include_cursor: bool = False) -> tuple[QPixmap, QRect]:
    """
    Engine Chụp Màn Hình Win32 Raw Physical Pixel 1:1 (Tuyệt đối không bị mờ nhòe HiDPI).
    Chụp trực tiếp mảng pixel vật lý gốc của GPU.
    Hỗ trợ đầy đủ thiết lập Đa Màn Hình (Multi-Monitor Virtual Desktop).
    Hỗ trợ tùy chọn vẽ con trỏ chuột (include_cursor).
    """
    screens = QGuiApplication.screens()
    if not screens:
        return QPixmap(), QRect()

    if len(screens) == 1:
        primary_screen = screens[0]
        virtual_rect = primary_screen.geometry()
        pixmap = primary_screen.grabWindow(0)
        pixmap.setDevicePixelRatio(1.0)
    else:
        # Multi-monitor setup: calculate virtual bounding rectangle across all monitors
        virtual_rect = screens[0].geometry()
        for s in screens[1:]:
            virtual_rect = virtual_rect.united(s.geometry())

        pixmap = QPixmap(virtual_rect.size())
        pixmap.fill(Qt.GlobalColor.black)
        pixmap.setDevicePixelRatio(1.0)

        painter = QPainter(pixmap)
        for s in screens:
            screen_pm = s.grabWindow(0)
            screen_pm.setDevicePixelRatio(1.0)
            target_x = s.geometry().x() - virtual_rect.x()
            target_y = s.geometry().y() - virtual_rect.y()
            painter.drawPixmap(target_x, target_y, screen_pm)
        painter.end()

    # Optionally draw mouse cursor pointer onto screen pixmap
    if include_cursor:
        cursor_pos = QCursor.pos()
        if virtual_rect.contains(cursor_pos):
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            
            rel_x = float(cursor_pos.x() - virtual_rect.x())
            rel_y = float(cursor_pos.y() - virtual_rect.y())
            
            # Clean Windows arrow cursor polygon
            cursor_poly = QPolygonF([
                QPointF(rel_x, rel_y),
                QPointF(rel_x + 5.0, rel_y + 16.0),
                QPointF(rel_x + 9.0, rel_y + 12.0),
                QPointF(rel_x + 15.0, rel_y + 15.0),
                QPointF(rel_x + 17.0, rel_y + 11.0),
                QPointF(rel_x + 11.0, rel_y + 8.0),
                QPointF(rel_x + 16.0, rel_y + 5.0),
            ])
            painter.setPen(QPen(QColor(0, 0, 0), 1.5))
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawPolygon(cursor_poly)
            painter.end()

    return pixmap, virtual_rect

